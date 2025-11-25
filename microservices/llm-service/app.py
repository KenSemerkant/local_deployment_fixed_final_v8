from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
import os
import asyncio
import logging
import time
import json
import pickle
import numpy as np
import re
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument

# Initialize FastAPI app
app = FastAPI(
    title="LLM Service",
    version="1.0.0",
    root_path="/llm"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums for LLM
class LLMMode(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    OLLAMA = "ollama"

class LLMStatusResponse(BaseModel):
    status: str
    mode: str
    model: Optional[str]
    error: Optional[str]
    base_url: Optional[str] = None
    provider: Optional[str] = None
    api_key_status: Optional[str] = None

class LLMModeRequest(BaseModel):
    mode: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None

# Configuration
LLM_MODE = os.environ.get("LLM_MODE", "mock")
MOCK_DELAY = int(os.environ.get("MOCK_DELAY", "2"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "lm-studio")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "mistralai/magistral-small-2509")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://host.docker.internal:1234/v1")

# Financial analyst system prompt
FINANCIAL_ANALYST_SYSTEM_PROMPT = """
You are a seasoned Financial Analyst with over 15 years of experience specializing in 10-K and 10-Q filings. Your expertise lies in extracting critical financial intelligence and identifying subtle cues that inform investment decisions for both individual and institutional portfolios.

Your core capabilities include:

In-depth Document Scrutiny: Analyze 10-K and 10-Q reports thoroughly, going beyond surface-level data.
Tone and Language Analysis: Evaluate management's tone and language to identify hidden risks, undisclosed liabilities, potential opportunities or shifts in strategy not explicitly stated.
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
    ]
}

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

def remove_thinking_tags(text: str) -> str:
    """
    Remove thinking sections from LLM responses (for models like DeepSeek R1).

    Args:
        text: The raw LLM response text

    Returns:
        The text with thinking sections removed
    """
    if not text:
        return text

    # Remove <think>...</think> sections using regex (for DeepSeek R1 and similar models)
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Clean up any extra whitespace that might be left
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)  # Replace multiple newlines with double newlines
    cleaned_text = cleaned_text.strip()  # Remove leading/trailing whitespace

    return cleaned_text

def ask_question_openai(vector_db_path: str, question: str) -> Dict[str, Any]:
    """Ask a question using OpenAI API with proper vector database similarity search."""
    try:
        # Load the FAISS vector database
        documents_path = os.path.join(vector_db_path, "documents.pkl")
        embeddings_path = os.path.join(vector_db_path, "index.faiss")

        if not os.path.exists(embeddings_path):
            logger.error(f"Vector database not found at {embeddings_path}")
            return {
                "answer": "Vector database not found",
                "sources": []
            }

        # Load the embeddings from the local FAISS store
        embeddings = OpenAIEmbeddings()
        db = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)

        # Perform similarity search to find relevant documents (using the question to find similar chunks)
        relevant_docs = db.similarity_search(question, k=3)  # Get top 3 most relevant chunks

        # Prepare context from relevant documents
        context_parts = []
        sources = []

        for i, doc in enumerate(relevant_docs):
            content = doc.page_content
            context_parts.append(f"Relevant section {i+1}:\n{content}")

            # Create source information
            source_info = {
                "page": doc.metadata.get("page", 1),  # Assuming page is stored in metadata
                "snippet": content[:200] + "..." if len(content) > 200 else content  # First 200 chars as snippet
            }
            sources.append(source_info)

        context = "\n\n".join(context_parts)

        # Prepare the complete prompt with the financial analyst system prompt and relevant context
        prompt = f"""
        {FINANCIAL_ANALYST_SYSTEM_PROMPT}

        Context information from the financial document:
        {context}

        Question: {question}

        Please provide a detailed answer based on the context information. If the answer is not in the context, say so.
        """

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

        logger.info(f"Calling OpenAI-compatible API with model: {OPENAI_MODEL}")

        # Create messages
        messages = [
            SystemMessage(content=FINANCIAL_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        # Make the API call
        response = chat(messages)

        # Remove thinking sections from response (for models like DeepSeek R1)
        content = response.content
        content = remove_thinking_tags(content)

        return {
            "answer": content,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error asking question with OpenAI: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }

def process_document_openai(file_path: str) -> Dict[str, Any]:
    """Process document using OpenAI API with proper vector database creation."""
    try:
        # Extract text from document
        text = extract_text_from_document(file_path)
        if not text:
            return {"error": "Failed to extract text from document"}

        # Create chunks using text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_text(text)

        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = LangchainDocument(
                page_content=chunk,
                metadata={
                    "source": file_path,
                    "chunk_id": i,
                    "page": i + 1  # Simple page assignment
                }
            )
            documents.append(doc)

        # Create embeddings and vector database
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_documents(documents, embeddings)

        # Save the vector database
        document_id = os.path.basename(os.path.dirname(file_path))
        vector_db_path = os.path.join("/data/vector_db", document_id)
        os.makedirs(vector_db_path, exist_ok=True)

        # Save the FAISS index
        db.save_local(vector_db_path)

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

        # Create messages for summary
        summary_messages = [
            SystemMessage(content=FINANCIAL_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=summary_prompt)
        ]

        # Get summary
        summary_response = chat(summary_messages)
        summary = remove_thinking_tags(summary_response.content)

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

        # Create messages for key figures
        key_figures_messages = [
            SystemMessage(content=FINANCIAL_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=key_figures_prompt)
        ]

        # Get key figures
        key_figures_response = chat(key_figures_messages)
        key_figures_content = remove_thinking_tags(key_figures_response.content)

        # Try to extract JSON from response
        import json
        import re

        # Look for JSON array in response
        json_match = re.search(r'\[.*\]', key_figures_content, re.DOTALL)
        if json_match:
            try:
                key_figures = json.loads(json_match.group(0))
            except:
                key_figures = [
                    {"name": "Revenue", "value": "Not found in processed document", "source_page": None},
                    {"name": "Net Income", "value": "Not found in processed document", "source_page": None},
                    {"name": "Total Assets", "value": "Not found in processed document", "source_page": None}
                ]
        else:
            key_figures = [
                {"name": "Revenue", "value": "Not found in processed document", "source_page": None},
                {"name": "Net Income", "value": "Not found in processed document", "source_page": None},
                {"name": "Total Assets", "value": "Not found in processed document", "source_page": None}
            ]

        return {
            "summary": summary,
            "key_figures": key_figures,
            "vector_db_path": vector_db_path
        }
    except Exception as e:
        logger.error(f"Error processing document with OpenAI: {e}")
        return {"error": str(e)}

def process_document_mock(file_path: str) -> Dict[str, Any]:
    """Process document using mock data."""
    time.sleep(MOCK_DELAY)  # Simulate processing time

    doc_type = "annual_report"  # Default type

    summary = MOCK_SUMMARIES.get(doc_type, MOCK_SUMMARIES["annual_report"])
    key_figures = MOCK_KEY_FIGURES.get(doc_type, MOCK_KEY_FIGURES["annual_report"])

    # Create a mock vector database for the document
    document_id = os.path.basename(os.path.dirname(file_path))
    vector_db_path = os.path.join("/data/vector_db", document_id)
    os.makedirs(vector_db_path, exist_ok=True)

    # Create a mock FAISS index file
    with open(os.path.join(vector_db_path, "index.faiss"), "w") as f:
        f.write("MOCK_FAISS_INDEX")

    # Create mock documents file
    with open(os.path.join(vector_db_path, "documents.pkl"), "wb") as f:
        pickle.dump([LangchainDocument(page_content="Mock document content for testing", metadata={"page": 1})], f)

    return {
        "summary": summary,
        "key_figures": key_figures,
        "vector_db_path": vector_db_path
    }

def ask_question_mock(document_id: str, question: str) -> Dict[str, Any]:
    """Ask a question using mock data."""
    doc_type = "annual_report"

    # Determine response based on question content
    question_lower = question.lower()
    if "revenue" in question_lower:
        answer = "Based on the financial report, the total revenue for this quarter was $2.5 million."
        sources = [{"page": 1, "snippet": "Total revenue: $2.5 million"}]
    elif "profit" in question_lower or "income" in question_lower:
        answer = "The net income for the period was $187 million, representing a 15% increase from the previous period."
        sources = [{"page": 2, "snippet": "Net income: $187 million"}]
    else:
        answer = "The information you're looking for isn't explicitly covered in the document. The document primarily focuses on financial performance, strategic initiatives, and market outlook."
        sources = []

    return {
        "answer": answer,
        "sources": sources
    }

@app.get("/")
def read_root():
    return {"service": "llm-service", "status": "running"}

@app.get("/status", response_model=LLMStatusResponse)
def get_llm_status():
    status = {
        "status": "available",
        "mode": LLM_MODE,
        "model": None,
        "error": None
    }

    if LLM_MODE == "mock":
        status["model"] = "mock"
    elif LLM_MODE == "openai":
        status["model"] = OPENAI_MODEL
        status["base_url"] = OPENAI_BASE_URL
        status["provider"] = "OpenAI-compatible (LM Studio)"
    elif LLM_MODE == "ollama":
        # Ollama status checking would go here
        status["model"] = os.environ.get("OLLAMA_MODEL", "llama2")
        status["provider"] = "Ollama"
    else:
        status["status"] = "error"
        status["error"] = f"Unknown LLM mode: {LLM_MODE}"

    return status

@app.post("/mode", response_model=LLMStatusResponse)
def set_llm_mode(request: LLMModeRequest):
    global LLM_MODE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

    if request.mode not in ["mock", "openai", "ollama"]:
        return {
            "status": "error",
            "message": f"Invalid LLM mode: {request.mode}. Must be one of: mock, openai, ollama"
        }

    # Update mode
    LLM_MODE = request.mode

    # Update API key, model, and base URL if provided
    if request.mode == "openai":
        if request.api_key:
            OPENAI_API_KEY = request.api_key
        if request.model:
            OPENAI_MODEL = request.model
        if request.base_url:
            OPENAI_BASE_URL = request.base_url
    elif request.mode == "ollama" and request.model:
        os.environ["OLLAMA_MODEL"] = request.model

    return {
        "status": "success",
        "message": f"LLM mode set to {LLM_MODE}",
        "llm_status": get_llm_status()
    }

@app.post("/process")
def process_document(request: Request):
    # This endpoint would receive a file path and perform document analysis
    file_path = request.query_params.get("file_path", "")

    if LLM_MODE == "mock":
        result = process_document_mock(file_path)
    elif LLM_MODE == "openai":
        result = process_document_openai(file_path)
    else:
        # In a real implementation, this would call the actual LLM
        result = {
            "summary": "Document processed successfully",
            "key_figures": [],
            "vector_db_path": ""
        }

    return result

@app.post("/ask")
def ask_question(request: Request):
    # This endpoint would receive a document ID and question
    document_id = request.query_params.get("document_id", "")
    question = request.query_params.get("question", "")

    if LLM_MODE == "mock":
        result = ask_question_mock(document_id, question)
    elif LLM_MODE == "openai":
        # We need to get the vector_db_path for the document
        vector_db_path = f"/data/vector_db/{document_id}"
        result = ask_question_openai(vector_db_path, question)
    else:
        # In a real implementation, this would call the actual LLM
        result = {
            "answer": "This is a sample answer from the LLM service.",
            "sources": []
        }

    return result

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "llm-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)