"""
LLM integration module for the AI Financial Analyst application.
Supports Ollama (with Gemma 3 27B), OpenAI, and mock LLM backends.
"""

import os
import time
import json
import hashlib
import logging
import requests
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import pickle
import tempfile

# Vector store and document processing
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document as LangchainDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM Configuration
LLM_MODE = os.environ.get("LLM_MODE", "mock")  # "mock", "ollama", or "openai"
MOCK_DELAY = int(os.environ.get("MOCK_DELAY", "2"))  # Seconds to simulate processing

# Ollama Configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:27b")
OLLAMA_USE_CPU = os.environ.get("OLLAMA_USE_CPU", "false").lower() == "true"
OLLAMA_MAX_TOKENS = int(os.environ.get("OLLAMA_MAX_TOKENS", "8192"))  # Default to 8192 if not specified

# OpenAI Configuration (also supports LM Studio)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "none")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")  # Default to OpenAI, can be set to LM Studio

# Vector store and caching configuration
STORAGE_PATH = os.environ.get("STORAGE_PATH", "/data")
VECTOR_DB_PATH = f"{STORAGE_PATH}/vector_db"
CACHE_PATH = f"{STORAGE_PATH}/cache"
ENABLE_CACHING = os.environ.get("ENABLE_CACHING", "true").lower() == "true"

# Create necessary directories
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)

# Financial Analyst System Prompt
FINANCIAL_ANALYST_SYSTEM_PROMPT = """
You are a seasoned Financial Analyst with over 15 years of experience specializing in 10-K and 10-Q filings. Your expertise lies in extracting critical financial intelligence and identifying subtle cues that inform investment decisions for both individual and institutional portfolios.

Your core capabilities include:

In-depth Document Scrutiny: Analyze 10-K and 10-Q reports thoroughly, going beyond surface-level data.
Tone and Language Analysis: Evaluate management's tone and language to identify hidden risks, undisclosed liabilities, potential opportunities, or shifts in strategy not explicitly stated.
Inconsistency Detection: Pinpoint inconsistencies across different sections of financial reports that may signal unstated risks or exploitable opportunities.
Qualitative and Quantitative Risk/Opportunity Assessment: Identify qualitative factors and interpret quantitative data to foresee potential short-term or long-term financial gains or losses for portfolios.
Proactive Risk Communication: Immediately identify and articulate any impending details or trends that pose investment risks to stakeholders.
Your objective is to provide precise, actionable insights that enable informed decision-making and risk mitigation for financial stakeholders.
"""

# Mock data for demonstration
MOCK_SUMMARIES = {
    "annual_report": """
This annual report presents the financial performance and strategic developments of the company for the fiscal year 2024. 

Key highlights include:
- Revenue growth of 12.5% year-over-year, reaching $1.25 billion
- Operating margin improvement to 18.3%, up from 16.7% in the previous year
- Successful expansion into three new international markets
- Launch of two major product lines contributing 8% to total revenue
- Reduction in carbon footprint by 15% through sustainability initiatives
- Strategic acquisition of TechInnovate Inc. for $230 million

The company faced challenges including supply chain disruptions in Q2 and increased regulatory scrutiny in European markets. However, management implemented mitigation strategies including diversification of suppliers and enhanced compliance protocols.

The outlook for 2025 remains positive, with projected revenue growth of 8-10% and continued margin expansion through operational efficiencies and strategic pricing initiatives.
""",
    "quarterly_report": """
The Q1 2025 quarterly report shows mixed results with some positive developments and ongoing challenges.

Key highlights include:
- Revenue of $328 million, up 5.2% compared to Q1 2024
- Earnings per share of $0.87, slightly below analyst expectations of $0.92
- Operating expenses increased by 7.8% due to ongoing expansion efforts
- Cash reserves of $412 million, providing strong liquidity position
- New customer acquisition up 12% year-over-year

The company continues to invest in its digital transformation initiative, with $28 million allocated this quarter. The new customer portal launched in February has shown promising early results with user engagement up 34%.

Management has maintained its full-year guidance but acknowledged potential headwinds from increasing raw material costs and competitive pressures in the Asian market.
""",
    "financial_statement": """
The consolidated financial statements for the fiscal year ending December 31, 2024, present a comprehensive view of the company's financial position.

The balance sheet shows total assets of $3.42 billion, up from $3.18 billion in the previous year. Current assets represent 38% of total assets, with cash and cash equivalents at $412 million. The company maintains a healthy liquidity position with a current ratio of 2.3.

Long-term debt decreased by $85 million to $920 million, improving the debt-to-equity ratio to 0.68. Shareholders' equity increased to $1.35 billion, reflecting retained earnings and minimal share repurchases during the year.

The income statement shows revenue of $1.25 billion and net income of $187 million, representing a net profit margin of 15%. Operating expenses were well-controlled at 66% of revenue, down from 68% in the previous year.

The cash flow statement indicates strong operational cash generation of $245 million, with $120 million used for capital expenditures, $75 million for debt repayment, and $50 million returned to shareholders through dividends.
"""
}

MOCK_KEY_FIGURES = {
    "annual_report": [
        {"name": "Annual Revenue", "value": "$1.25 billion", "source_page": 12},
        {"name": "Revenue Growth", "value": "12.5%", "source_page": 12},
        {"name": "Operating Margin", "value": "18.3%", "source_page": 15},
        {"name": "Net Income", "value": "$187 million", "source_page": 18},
        {"name": "Earnings Per Share", "value": "$3.42", "source_page": 18},
        {"name": "Dividend Per Share", "value": "$0.92", "source_page": 22},
        {"name": "R&D Expenditure", "value": "$78 million", "source_page": 34},
        {"name": "Total Assets", "value": "$3.42 billion", "source_page": 45},
        {"name": "Long-term Debt", "value": "$920 million", "source_page": 47},
        {"name": "Debt-to-Equity Ratio", "value": "0.68", "source_page": 48}
    ],
    "quarterly_report": [
        {"name": "Quarterly Revenue", "value": "$328 million", "source_page": 5},
        {"name": "Revenue Growth (YoY)", "value": "5.2%", "source_page": 5},
        {"name": "Earnings Per Share", "value": "$0.87", "source_page": 6},
        {"name": "Operating Expenses", "value": "$215 million", "source_page": 8},
        {"name": "Operating Expense Growth", "value": "7.8%", "source_page": 8},
        {"name": "Cash Reserves", "value": "$412 million", "source_page": 10},
        {"name": "New Customer Growth", "value": "12%", "source_page": 12},
        {"name": "Digital Transformation Investment", "value": "$28 million", "source_page": 15}
    ],
    "financial_statement": [
        {"name": "Total Assets", "value": "$3.42 billion", "source_page": 3},
        {"name": "Current Assets", "value": "$1.30 billion", "source_page": 3},
        {"name": "Cash and Equivalents", "value": "$412 million", "source_page": 3},
        {"name": "Current Ratio", "value": "2.3", "source_page": 4},
        {"name": "Long-term Debt", "value": "$920 million", "source_page": 5},
        {"name": "Debt-to-Equity Ratio", "value": "0.68", "source_page": 5},
        {"name": "Shareholders' Equity", "value": "$1.35 billion", "source_page": 6},
        {"name": "Revenue", "value": "$1.25 billion", "source_page": 8},
        {"name": "Net Income", "value": "$187 million", "source_page": 8},
        {"name": "Net Profit Margin", "value": "15%", "source_page": 9},
        {"name": "Operating Expenses", "value": "66% of revenue", "source_page": 10},
        {"name": "Operational Cash Flow", "value": "$245 million", "source_page": 12},
        {"name": "Capital Expenditures", "value": "$120 million", "source_page": 12},
        {"name": "Dividend Payout", "value": "$50 million", "source_page": 13}
    ]
}

MOCK_QA_RESPONSES = {
    "annual_report": {
        "revenue": {
            "answer": "The company reported annual revenue of $1.25 billion for the fiscal year 2024, representing a growth of 12.5% compared to the previous year.",
            "sources": [
                {"page": 12, "snippet": "Total revenue reached $1.25 billion, a 12.5% increase from the previous fiscal year."}
            ]
        },
        "profit": {
            "answer": "The company reported a net income of $187 million for fiscal year 2024, with a net profit margin of 15%.",
            "sources": [
                {"page": 18, "snippet": "Net income for the year was $187 million, representing a net profit margin of 15%."}
            ]
        },
        "challenges": {
            "answer": "The main challenges faced by the company in 2024 were supply chain disruptions during Q2 and increased regulatory scrutiny in European markets. Management addressed these through supplier diversification and enhanced compliance protocols.",
            "sources": [
                {"page": 24, "snippet": "Supply chain disruptions in Q2 2024 temporarily impacted product availability in key markets."},
                {"page": 25, "snippet": "European operations faced increased regulatory scrutiny, requiring additional compliance investments."}
            ]
        },
        "default": {
            "answer": "The information you're looking for isn't explicitly covered in the annual report. The report primarily focuses on financial performance, strategic initiatives, market expansion, and outlook for the coming year.",
            "sources": []
        }
    },
    "quarterly_report": {
        "revenue": {
            "answer": "The company reported quarterly revenue of $328 million for Q1 2025, representing a growth of 5.2% compared to Q1 2024.",
            "sources": [
                {"page": 5, "snippet": "Q1 2025 revenue was $328 million, up 5.2% year-over-year."}
            ]
        },
        "earnings": {
            "answer": "The company reported earnings per share of $0.87 for Q1 2025, which was slightly below analyst expectations of $0.92.",
            "sources": [
                {"page": 6, "snippet": "Earnings per share were $0.87, falling short of consensus analyst expectations of $0.92."}
            ]
        },
        "guidance": {
            "answer": "Management has maintained its full-year guidance despite acknowledging potential headwinds from increasing raw material costs and competitive pressures in the Asian market.",
            "sources": [
                {"page": 18, "snippet": "We are maintaining our full-year guidance while monitoring potential headwinds from raw material cost inflation and intensifying competition in Asian markets."}
            ]
        },
        "default": {
            "answer": "The information you're looking for isn't explicitly covered in the quarterly report. The Q1 2025 report primarily focuses on financial performance, digital transformation initiatives, and market challenges for the current quarter.",
            "sources": []
        }
    },
    "financial_statement": {
        "assets": {
            "answer": "The company reported total assets of $3.42 billion as of December 31, 2024, up from $3.18 billion in the previous year. Current assets represent 38% of total assets at $1.30 billion, with cash and cash equivalents at $412 million.",
            "sources": [
                {"page": 3, "snippet": "Total assets increased to $3.42 billion from $3.18 billion, with current assets of $1.30 billion (38%) including $412 million in cash and cash equivalents."}
            ]
        },
        "debt": {
            "answer": "The company's long-term debt decreased by $85 million to $920 million, improving the debt-to-equity ratio to 0.68.",
            "sources": [
                {"page": 5, "snippet": "Long-term debt decreased to $920 million, down $85 million from the previous year, resulting in an improved debt-to-equity ratio of 0.68."}
            ]
        },
        "cash flow": {
            "answer": "The company generated $245 million in operational cash flow, with $120 million used for capital expenditures, $75 million for debt repayment, and $50 million returned to shareholders through dividends.",
            "sources": [
                {"page": 12, "snippet": "Operating activities generated $245 million in cash flow. Major cash outflows included $120 million for capital expenditures, $75 million for debt repayment, and $50 million for shareholder dividends."}
            ]
        },
        "default": {
            "answer": "The information you're looking for isn't explicitly covered in the financial statements. The statements primarily focus on the balance sheet, income statement, and cash flow statement for the fiscal year ending December 31, 2024.",
            "sources": []
        }
    },
    "default": {
        "default": {
            "answer": "I don't have enough information to answer this question based on the document. The document may not contain this specific information, or it might be in sections that weren't included in the analysis.",
            "sources": []
        }
    }
}

# Helper functions for caching
def get_file_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_cache_path(document_id: str, operation: str) -> str:
    """Get cache file path for a document and operation."""
    return os.path.join(CACHE_PATH, f"{document_id}_{operation}.pkl")

def save_to_cache(document_id: str, operation: str, data: Any) -> None:
    """Save data to cache."""
    if not ENABLE_CACHING:
        return
    
    try:
        cache_path = get_cache_path(document_id, operation)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Saved {operation} to cache for document {document_id}")
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")

def load_from_cache(document_id: str, operation: str) -> Optional[Any]:
    """Load data from cache if available."""
    if not ENABLE_CACHING:
        return None
    
    cache_path = get_cache_path(document_id, operation)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            logger.info(f"Loaded {operation} from cache for document {document_id}")
            return data
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
    
    return None

def check_document_processed(document_id: str, file_path: str) -> bool:
    """Check if document has been processed and cached with the same MD5."""
    if not ENABLE_CACHING:
        return False
    
    try:
        # Get current file MD5
        current_md5 = get_file_md5(file_path)
        
        # Check if MD5 cache exists
        md5_cache_path = get_cache_path(document_id, "md5")
        if os.path.exists(md5_cache_path):
            with open(md5_cache_path, 'rb') as f:
                cached_md5 = pickle.load(f)
            
            # Check if vector DB exists
            vector_db_path = load_from_cache(document_id, "vector_db_path")
            if vector_db_path and os.path.exists(vector_db_path):
                # Check if summary exists
                summary = load_from_cache(document_id, "summary")
                if summary is not None:
                    # Check if MD5 matches
                    if cached_md5 == current_md5:
                        logger.info(f"Document {document_id} already processed with same MD5")
                        return True
    except Exception as e:
        logger.error(f"Error checking document processed: {str(e)}")
    
    return False

def get_document_type(file_path: str) -> str:
    """Determine document type based on content or filename."""
    file_name = os.path.basename(file_path).lower()
    
    if "annual" in file_name or "10-k" in file_name:
        return "annual_report"
    elif "quarter" in file_name or "10-q" in file_name:
        return "quarterly_report"
    elif "financial" in file_name or "statement" in file_name:
        return "financial_statement"
    else:
        return "annual_report"  # Default to annual report

def process_document_mock(file_path: str, cancel_event=None) -> Dict[str, Any]:
    """Process document using mock data with cancellation support."""
    # Simulate processing delay with cancellation checks
    delay_chunks = 10  # Split delay into chunks for cancellation checks
    chunk_delay = MOCK_DELAY / delay_chunks

    for i in range(delay_chunks):
        if cancel_event and cancel_event.is_set():
            logger.info("Mock processing cancelled")
            return {"error": "Processing cancelled"}
        time.sleep(chunk_delay)
    
    # Determine document type
    doc_type = get_document_type(file_path)
    
    # Get mock data
    summary = MOCK_SUMMARIES.get(doc_type, MOCK_SUMMARIES["annual_report"])
    key_figures = MOCK_KEY_FIGURES.get(doc_type, MOCK_KEY_FIGURES["annual_report"])
    
    # Create vector DB path
    document_id = os.path.basename(os.path.dirname(file_path))
    vector_db_path = os.path.join(VECTOR_DB_PATH, document_id)
    os.makedirs(vector_db_path, exist_ok=True)
    
    # Create a dummy vector DB file
    with open(os.path.join(vector_db_path, "index.faiss"), "wb") as f:
        f.write(b"MOCK_VECTOR_DB")
    
    return {
        "summary": summary,
        "key_figures": key_figures,
        "vector_db_path": vector_db_path
    }

def process_document_ollama(file_path: str, cancel_event=None) -> Dict[str, Any]:
    """Process document using Ollama with cancellation support."""
    logger.info(f"Processing document with Ollama: {file_path}")
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Using Ollama max tokens: {OLLAMA_MAX_TOKENS}")

    try:
        # Check for cancellation before text extraction
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama processing cancelled before text extraction")
            return {"error": "Processing cancelled"}

        # Extract text from document
        text = extract_text_from_document(file_path)
        if not text:
            return {"error": "Failed to extract text from document"}

        # Check for cancellation after text extraction
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama processing cancelled after text extraction")
            return {"error": "Processing cancelled"}
        
        # Create chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_text(text)
        
        # Create vector DB
        document_id = os.path.basename(os.path.dirname(file_path))
        vector_db_path = os.path.join(VECTOR_DB_PATH, document_id)
        
        # Create embeddings for chunks
        documents = [LangchainDocument(page_content=chunk, metadata={"source": file_path}) for chunk in chunks]
        
        # Use simple numpy embeddings for demo
        embeddings = np.random.rand(len(documents), 768)
        
        # Save to FAISS
        os.makedirs(vector_db_path, exist_ok=True)
        with open(os.path.join(vector_db_path, "documents.pkl"), "wb") as f:
            pickle.dump(documents, f)
        
        # Generate summary using Ollama
        summary_prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}
        
        Please analyze the following financial document and provide a comprehensive summary:
        
        {text[:50000]}  # Limit text to avoid token limits
        
        Your summary should include:
        1. Key financial highlights
        2. Important trends
        3. Potential risks or opportunities
        4. Management's outlook
        """
        
        # Check for cancellation before summary generation
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama processing cancelled before summary generation")
            return {"error": "Processing cancelled"}

        summary = call_ollama_api(summary_prompt, cancel_event)

        # Check for cancellation after summary generation
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama processing cancelled after summary generation")
            return {"error": "Processing cancelled"}

        # Extract key figures using Ollama
        key_figures_prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}

        Please extract key financial figures from the following document:

        {text[:50000]}  # Limit text to avoid token limits

        For each key figure, provide:
        1. Name of the figure (e.g., "Annual Revenue", "Net Income", "Debt-to-Equity Ratio")
        2. Value (e.g., "$1.25 billion", "15%", "0.68")
        3. Source page number if available

        Format your response as a JSON array of objects with "name", "value", and "source_page" fields.
        """

        # Check for cancellation before key figures extraction
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama processing cancelled before key figures extraction")
            return {"error": "Processing cancelled"}

        key_figures_response = call_ollama_api(key_figures_prompt, cancel_event)
        
        # Parse key figures from response
        key_figures = extract_key_figures_from_response(key_figures_response)
        
        return {
            "summary": summary,
            "key_figures": key_figures,
            "vector_db_path": vector_db_path
        }
    except Exception as e:
        logger.error(f"Error processing document with Ollama: {e}")
        return {"error": str(e)}

def process_document_openai(file_path: str, cancel_event=None) -> Dict[str, Any]:
    """Process document using OpenAI with cancellation support."""
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not provided"}

    try:
        # Check for cancellation before text extraction
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI processing cancelled before text extraction")
            return {"error": "Processing cancelled"}

        # Extract text from document
        text = extract_text_from_document(file_path)
        if not text:
            return {"error": "Failed to extract text from document"}

        # Check for cancellation after text extraction
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI processing cancelled after text extraction")
            return {"error": "Processing cancelled"}
        
        # Create chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_text(text)
        
        # Create vector DB
        document_id = os.path.basename(os.path.dirname(file_path))
        vector_db_path = os.path.join(VECTOR_DB_PATH, document_id)
        
        # Create embeddings for chunks
        documents = [LangchainDocument(page_content=chunk, metadata={"source": file_path}) for chunk in chunks]
        
        # Use simple numpy embeddings for demo
        embeddings = np.random.rand(len(documents), 768)
        
        # Save to FAISS
        os.makedirs(vector_db_path, exist_ok=True)
        with open(os.path.join(vector_db_path, "documents.pkl"), "wb") as f:
            pickle.dump(documents, f)
        
        # Generate summary using OpenAI
        summary_prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}
        
        Please analyze the following financial document and provide a comprehensive summary:
        
        {text[:50000]}  # Limit text to avoid token limits
        
        Your summary should include:
        1. Key financial highlights
        2. Important trends
        3. Potential risks or opportunities
        4. Management's outlook
        """
        
        # Check for cancellation before summary generation
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI processing cancelled before summary generation")
            return {"error": "Processing cancelled"}

        summary = call_openai_api(summary_prompt, cancel_event)

        # Check for cancellation after summary generation
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI processing cancelled after summary generation")
            return {"error": "Processing cancelled"}

        # Extract key figures using OpenAI
        key_figures_prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}

        Please extract key financial figures from the following document:

        {text[:50000]}  # Limit text to avoid token limits

        For each key figure, provide:
        1. Name of the figure (e.g., "Annual Revenue", "Net Income", "Debt-to-Equity Ratio")
        2. Value (e.g., "$1.25 billion", "15%", "0.68")
        3. Source page number if available

        Format your response as a JSON array of objects with "name", "value", and "source_page" fields.
        """

        # Check for cancellation before key figures extraction
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI processing cancelled before key figures extraction")
            return {"error": "Processing cancelled"}

        key_figures_response = call_openai_api(key_figures_prompt, cancel_event)
        
        # Parse key figures from response
        key_figures = extract_key_figures_from_response(key_figures_response)
        
        return {
            "summary": summary,
            "key_figures": key_figures,
            "vector_db_path": vector_db_path
        }
    except Exception as e:
        logger.error(f"Error processing document with OpenAI: {e}")
        return {"error": str(e)}

def extract_text_from_document(file_path: str) -> str:
    """Extract text from document file."""
    try:
        # For text files, read directly
        if file_path.endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        # For PDF files, use PyMuPDF (fitz) for text extraction
        elif file_path.endswith(".pdf"):
            import fitz  # PyMuPDF

            logger.info(f"Extracting text from PDF: {file_path}")
            text_content = []

            # Open the PDF document
            doc = fitz.open(file_path)

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()

                if text.strip():  # Only add non-empty pages
                    # Add page marker for better context
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")

            doc.close()

            # Combine all pages
            full_text = "\n\n".join(text_content)

            if not full_text.strip():
                logger.warning(f"No text extracted from PDF: {file_path}")
                return "No readable text found in this PDF document."

            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            return full_text

        # For other file types, return a placeholder
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return "This file type is not supported for text extraction."
    except Exception as e:
        logger.error(f"Error extracting text from document {file_path}: {e}")
        return f"Error extracting text: {str(e)}"

def call_ollama_api(prompt: str, cancel_event=None) -> str:
    """Call Ollama API with prompt and cancellation support."""
    # Declare global variable at the very beginning of the function
    global OLLAMA_BASE_URL

    try:
        # Check for cancellation before starting
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama API call cancelled before starting")
            return "Processing cancelled"

        # Try multiple URLs to find Ollama
        urls_to_try = [
            OLLAMA_BASE_URL,
            "http://host.docker.internal:11434",
            "http://localhost:11434",
            "http://172.17.0.1:11434"  # Docker default bridge network
        ]

        working_url = None
        for url in urls_to_try:
            try:
                logger.info(f"Trying Ollama URL: {url}")
                response = requests.get(f"{url}/api/version", timeout=5)
                if response.status_code == 200:
                    working_url = url
                    logger.info(f"Found working Ollama URL: {url}")
                    # Update global URL if different
                    if OLLAMA_BASE_URL != working_url:
                        OLLAMA_BASE_URL = working_url
                        logger.info(f"Updated OLLAMA_BASE_URL to {working_url}")
                    break
            except Exception as e:
                logger.warning(f"Failed to connect to Ollama at {url}: {e}")

        if not working_url:
            return "Error: Could not connect to Ollama server. Please ensure Ollama is running and accessible."

        # Check for cancellation before making the request
        if cancel_event and cancel_event.is_set():
            logger.info("Ollama API call cancelled before request")
            return "Processing cancelled"

        # Prepare request payload with max tokens
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": OLLAMA_MAX_TOKENS  # Use the configured max tokens
            }
        }

        if OLLAMA_USE_CPU:
            payload["options"]["num_gpu"] = 0

        # Create a session for better control
        session = requests.Session()

        # Call Ollama API with reasonable timeout and cancellation checks
        logger.info("Starting Ollama API request")
        try:
            response = session.post(
                f"{working_url}/api/generate",
                json=payload,
                timeout=900  # 15 minutes timeout - reasonable for large documents
            )

            # Check for cancellation after request
            if cancel_event and cancel_event.is_set():
                logger.info("Ollama API call cancelled after request")
                session.close()
                return "Processing cancelled"

            if response.status_code == 200:
                result = response.json().get("response", "")
                session.close()
                return result
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                session.close()
                return f"Error: Ollama API returned status code {response.status_code}"
        except requests.exceptions.Timeout:
            logger.warning("Ollama API request timed out after 5 minutes")
            session.close()
            if cancel_event and cancel_event.is_set():
                return "Processing cancelled"
            return "Error: Request timed out after 5 minutes. The document may be too large or complex for processing."
        except Exception as e:
            logger.error(f"Error during Ollama API request: {e}")
            session.close()
            raise

    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return f"Error: {str(e)}"

def call_openai_api(prompt: str, cancel_event=None) -> str:
    """Call OpenAI-compatible API using LangChain (supports OpenAI and LM Studio)."""
    try:
        # Check for cancellation before starting
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI API call cancelled before starting")
            return "Processing cancelled"

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        # Configure LangChain ChatOpenAI for custom base URL (LM Studio support)
        if OPENAI_BASE_URL != "https://api.openai.com/v1":
            # LM Studio or other OpenAI-compatible API
            logger.info(f"Using custom OpenAI-compatible API at: {OPENAI_BASE_URL}")
            # For LM Studio, API key can be anything or empty
            api_key = OPENAI_API_KEY if OPENAI_API_KEY != "none" else "lm-studio"

            chat = ChatOpenAI(
                model=OPENAI_MODEL,
                openai_api_base=OPENAI_BASE_URL,
                openai_api_key=api_key,
                max_tokens=2000,
                temperature=0.3,
                request_timeout=300  # 5 minutes timeout
            )
        else:
            # Standard OpenAI API
            chat = ChatOpenAI(
                model=OPENAI_MODEL,
                openai_api_key=OPENAI_API_KEY,
                max_tokens=2000,
                temperature=0.3,
                request_timeout=300  # 5 minutes timeout
            )

        # Check for cancellation before making request
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI API call cancelled before request")
            return "Processing cancelled"

        logger.info(f"Calling OpenAI-compatible API with model: {OPENAI_MODEL}")

        # Create messages
        messages = [
            SystemMessage(content=FINANCIAL_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        # Make the API call
        response = chat(messages)

        # Check for cancellation after request
        if cancel_event and cancel_event.is_set():
            logger.info("OpenAI API call cancelled after request")
            return "Processing cancelled"

        return response.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API with LangChain: {e}")
        if cancel_event and cancel_event.is_set():
            return "Processing cancelled"
        return f"Error: {str(e)}"

def extract_key_figures_from_response(response: str) -> List[Dict[str, Any]]:
    """Extract key figures from LLM response."""
    try:
        # Try to find JSON array in response
        import re
        json_match = re.search(r'\[\s*{.*}\s*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        # If no JSON found, try to parse structured text
        key_figures = []
        lines = response.split('\n')
        current_figure = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for name: value pattern
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip()
                value = parts[1].strip()
                
                # Check if this is a new figure or part of current one
                if name.lower() in ['name', 'figure', 'metric']:
                    if current_figure and 'name' in current_figure and 'value' in current_figure:
                        key_figures.append(current_figure)
                    current_figure = {'name': value}
                elif name.lower() in ['value', 'amount']:
                    current_figure['value'] = value
                elif name.lower() in ['source', 'page', 'source page', 'source_page']:
                    try:
                        page_num = int(re.search(r'\d+', value).group(0))
                        current_figure['source_page'] = page_num
                    except:
                        current_figure['source_page'] = value
        
        # Add last figure if exists
        if current_figure and 'name' in current_figure and 'value' in current_figure:
            key_figures.append(current_figure)
        
        return key_figures if key_figures else [
            {"name": "Revenue", "value": "Not found", "source_page": None},
            {"name": "Net Income", "value": "Not found", "source_page": None},
            {"name": "Total Assets", "value": "Not found", "source_page": None}
        ]
    except Exception as e:
        logger.error(f"Error extracting key figures: {e}")
        return [
            {"name": "Revenue", "value": "Error extracting", "source_page": None},
            {"name": "Net Income", "value": "Error extracting", "source_page": None},
            {"name": "Total Assets", "value": "Error extracting", "source_page": None}
        ]

def process_document(file_path: str, cancel_event=None) -> Dict[str, Any]:
    """Process document using selected LLM backend with cancellation support."""
    # Check for cancellation at the start
    if cancel_event and cancel_event.is_set():
        logger.info("Document processing cancelled at start")
        return {"error": "Processing cancelled"}

    # Get document ID from path
    document_id = os.path.basename(os.path.dirname(file_path))

    # Check if document already processed
    if check_document_processed(document_id, file_path):
        logger.info(f"Loading document {document_id} from cache")
        return {
            "summary": load_from_cache(document_id, "summary"),
            "key_figures": load_from_cache(document_id, "key_figures"),
            "vector_db_path": load_from_cache(document_id, "vector_db_path")
        }
    
    # Check for cancellation before processing
    if cancel_event and cancel_event.is_set():
        logger.info("Document processing cancelled before LLM processing")
        return {"error": "Processing cancelled"}

    # Process document based on LLM mode
    result = {}
    if LLM_MODE == "mock":
        result = process_document_mock(file_path, cancel_event)
    elif LLM_MODE == "ollama":
        result = process_document_ollama(file_path, cancel_event)
    elif LLM_MODE == "openai":
        result = process_document_openai(file_path, cancel_event)
    else:
        result = {"error": f"Unknown LLM mode: {LLM_MODE}"}

    # Check for cancellation after processing
    if cancel_event and cancel_event.is_set():
        logger.info("Document processing cancelled after LLM processing")
        return {"error": "Processing cancelled"}

    # Cache results if successful
    if "error" not in result:
        # Save MD5 hash
        save_to_cache(document_id, "md5", get_file_md5(file_path))

        # Save results
        save_to_cache(document_id, "summary", result.get("summary"))
        save_to_cache(document_id, "key_figures", result.get("key_figures"))
        save_to_cache(document_id, "vector_db_path", result.get("vector_db_path"))

    return result

def ask_question(vector_db_path: str, question: str) -> Dict[str, Any]:
    """Ask a question about a document."""
    # Get document ID from vector DB path
    document_id = os.path.basename(vector_db_path)
    
    # Check if document exists
    if not os.path.exists(vector_db_path):
        return {
            "answer": "Document not found",
            "sources": []
        }
    
    # Process question based on LLM mode
    if LLM_MODE == "mock":
        return ask_question_mock(document_id, question)
    elif LLM_MODE == "ollama":
        return ask_question_ollama(vector_db_path, question)
    elif LLM_MODE == "openai":
        return ask_question_openai(vector_db_path, question)
    else:
        return {
            "answer": f"Unknown LLM mode: {LLM_MODE}",
            "sources": []
        }

def ask_question_mock(document_id: str, question: str) -> Dict[str, Any]:
    """Ask a question using mock data."""
    # Determine document type
    doc_type = "annual_report"  # Default
    
    # Get mock responses for document type
    responses = MOCK_QA_RESPONSES.get(doc_type, MOCK_QA_RESPONSES["default"])
    
    # Find best matching response
    question_lower = question.lower()
    if "revenue" in question_lower:
        response_key = "revenue"
    elif "profit" in question_lower or "income" in question_lower or "earnings" in question_lower:
        response_key = "profit" if "profit" in responses else "earnings"
    elif "challenge" in question_lower or "risk" in question_lower:
        response_key = "challenges"
    elif "asset" in question_lower:
        response_key = "assets"
    elif "debt" in question_lower:
        response_key = "debt"
    elif "cash" in question_lower or "flow" in question_lower:
        response_key = "cash flow"
    elif "guidance" in question_lower or "outlook" in question_lower:
        response_key = "guidance"
    else:
        response_key = "default"
    
    # Get response
    response = responses.get(response_key, responses["default"])
    
    return response

def ask_question_ollama(vector_db_path: str, question: str) -> Dict[str, Any]:
    """Ask a question using Ollama."""
    try:
        # Load documents from vector DB
        documents_path = os.path.join(vector_db_path, "documents.pkl")
        if not os.path.exists(documents_path):
            return {
                "answer": "Document vector database not found",
                "sources": []
            }
        
        with open(documents_path, "rb") as f:
            documents = pickle.load(f)
        
        # Get relevant chunks (simple approach for demo)
        relevant_chunks = documents[:3]  # Just use first 3 chunks
        context = "\n\n".join([doc.page_content for doc in relevant_chunks])
        
        # Prepare prompt
        prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}
        
        Context information from the financial document:
        {context}
        
        Question: {question}
        
        Please provide a detailed answer based on the context information. If the answer is not in the context, say so.
        """
        
        # Call Ollama API
        answer = call_ollama_api(prompt)
        
        # Prepare sources
        sources = []
        for i, doc in enumerate(relevant_chunks):
            sources.append({
                "page": i + 1,  # Mock page number
                "snippet": doc.page_content[:100] + "..."  # First 100 chars
            })
        
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error asking question with Ollama: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }

def ask_question_openai(vector_db_path: str, question: str) -> Dict[str, Any]:
    """Ask a question using OpenAI."""
    if not OPENAI_API_KEY:
        return {
            "answer": "OpenAI API key not provided",
            "sources": []
        }
    
    try:
        # Load documents from vector DB
        documents_path = os.path.join(vector_db_path, "documents.pkl")
        if not os.path.exists(documents_path):
            return {
                "answer": "Document vector database not found",
                "sources": []
            }
        
        with open(documents_path, "rb") as f:
            documents = pickle.load(f)
        
        # Get relevant chunks (simple approach for demo)
        relevant_chunks = documents[:3]  # Just use first 3 chunks
        context = "\n\n".join([doc.page_content for doc in relevant_chunks])
        
        # Prepare prompt
        prompt = f"""
        Context information from the financial document:
        {context}
        
        Question: {question}
        
        Please provide a detailed answer based on the context information. If the answer is not in the context, say so.
        """
        
        # Call OpenAI API
        answer = call_openai_api(prompt)
        
        # Prepare sources
        sources = []
        for i, doc in enumerate(relevant_chunks):
            sources.append({
                "page": i + 1,  # Mock page number
                "snippet": doc.page_content[:100] + "..."  # First 100 chars
            })
        
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error asking question with OpenAI: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }

def get_llm_status() -> Dict[str, Any]:
    """Get LLM status."""
    global OLLAMA_BASE_URL

    status = {
        "status": "available",
        "mode": LLM_MODE,
        "model": None,
        "error": None
    }

    if LLM_MODE == "mock":
        status["model"] = "mock"
    elif LLM_MODE == "ollama":
        status["model"] = OLLAMA_MODEL

        # Check Ollama connection
        try:
            # Try multiple URLs to find Ollama
            urls_to_try = [
                OLLAMA_BASE_URL,
                "http://host.docker.internal:11434",
                "http://localhost:11434",
                "http://172.17.0.1:11434"  # Docker default bridge network
            ]

            working_url = None
            for url in urls_to_try:
                try:
                    response = requests.get(f"{url}/api/version", timeout=5)
                    if response.status_code == 200:
                        working_url = url
                        # Update global URL if different
                        if OLLAMA_BASE_URL != working_url:
                            OLLAMA_BASE_URL = working_url
                        break
                except:
                    pass
            
            if not working_url:
                status["status"] = "error"
                status["error"] = "Could not connect to Ollama server"
            else:
                # Check if model is available
                response = requests.get(f"{working_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name") for model in models]
                    if OLLAMA_MODEL not in model_names:
                        status["status"] = "warning"
                        status["error"] = f"Model {OLLAMA_MODEL} not found in Ollama"
                else:
                    status["status"] = "warning"
                    status["error"] = "Could not get list of models from Ollama"
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)
    elif LLM_MODE == "openai":
        status["model"] = OPENAI_MODEL
        status["base_url"] = OPENAI_BASE_URL

        # Check if using LM Studio or OpenAI
        if OPENAI_BASE_URL != "https://api.openai.com/v1":
            status["provider"] = "LM Studio (or OpenAI-compatible)"
            # For LM Studio, API key is optional
            if not OPENAI_API_KEY or OPENAI_API_KEY == "none":
                status["api_key_status"] = "Using default (LM Studio doesn't require API key)"
            else:
                status["api_key_status"] = "Custom API key provided"
        else:
            status["provider"] = "OpenAI"
            # Check OpenAI API key
            if not OPENAI_API_KEY or OPENAI_API_KEY == "none":
                status["status"] = "error"
                status["error"] = "OpenAI API key not provided"
    else:
        status["status"] = "error"
        status["error"] = f"Unknown LLM mode: {LLM_MODE}"
    
    return status

def set_llm_mode(mode: str, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Set LLM mode."""
    global LLM_MODE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, OLLAMA_MODEL

    if mode not in ["mock", "ollama", "openai"]:
        return {
            "status": "error",
            "message": f"Invalid LLM mode: {mode}. Must be one of: mock, ollama, openai"
        }

    # Update mode
    LLM_MODE = mode

    # Update API key, model, and base URL if provided
    if mode == "openai":
        if api_key:
            OPENAI_API_KEY = api_key
        if model:
            OPENAI_MODEL = model
        if base_url:
            OPENAI_BASE_URL = base_url
    elif mode == "ollama" and model:
        OLLAMA_MODEL = model

    return {
        "status": "success",
        "message": f"LLM mode set to {mode}",
        "llm_status": get_llm_status()
    }

def get_current_llm_mode() -> str:
    """Get current LLM mode."""
    return LLM_MODE

def get_available_llm_modes() -> List[str]:
    """Get available LLM modes."""
    return ["mock", "ollama", "openai"]

def clear_document_cache(document_id: str) -> bool:
    """Clear cache for a specific document."""
    try:
        cache_operations = ["md5", "summary", "key_figures", "vector_db_path"]
        cleared_count = 0

        for operation in cache_operations:
            cache_path = get_cache_path(document_id, operation)
            if os.path.exists(cache_path):
                os.remove(cache_path)
                cleared_count += 1
                logger.info(f"Cleared cache for document {document_id}, operation: {operation}")

        logger.info(f"Cleared {cleared_count} cache files for document {document_id}")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache for document {document_id}: {e}")
        return False

def clear_all_cache() -> bool:
    """Clear all cached data."""
    try:
        if os.path.exists(CACHE_PATH):
            import shutil
            shutil.rmtree(CACHE_PATH)
            os.makedirs(CACHE_PATH, exist_ok=True)
            logger.info("Cleared all cache data")
            return True
        return True
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
        return False
