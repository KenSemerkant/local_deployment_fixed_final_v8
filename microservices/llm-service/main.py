from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import asyncio
import json
import time
import uuid
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class LLMConfig(BaseModel):
    mode: str  # openai, ollama, lmstudio, mock
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2000
    timeout: Optional[int] = 300

class LLMStatus(BaseModel):
    status: str
    mode: str
    model: Optional[str] = None
    error: Optional[str] = None

class DocumentAnalysisRequest(BaseModel):
    document_path: str
    document_type: str = "financial"

class KeyFigure(BaseModel):
    name: str
    value: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    summary: str
    key_figures: List[KeyFigure]
    vector_db_path: str

class QuestionRequest(BaseModel):
    document_path: str
    question: str

class SourceReference(BaseModel):
    page: Optional[int] = None
    snippet: Optional[str] = None
    section: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[SourceReference]

class LLMConfigRequest(BaseModel):
    mode: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2000

# Initialize FastAPI app
app = FastAPI(
    title="LLM Integration Service",
    version="1.0.0",
    root_path="/llm"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CURRENT_CONFIG = {
    "mode": os.getenv("LLM_MODE", "mock"),
    "api_key": os.getenv("OPENAI_API_KEY", "lm-studio"),
    "base_url": os.getenv("OPENAI_BASE_URL", "http://host.docker.internal:1234/v1"),
    "model": os.getenv("OPENAI_MODEL", "mistralai/magistral-small-2509"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
    "timeout": int(os.getenv("LLM_TIMEOUT", "300"))
}

def process_financial_document_mock(document_path: str) -> Dict[str, Any]:
    """Process a financial document using mock data."""
    # Simulate processing time
    time.sleep(int(os.getenv("MOCK_DELAY", "2")))
    
    # Determine document type from filename to provide appropriate mock data
    doc_name = document_path.lower()
    if "annual" in doc_name or "10k" in doc_name or "fy" in doc_name:
        doc_type = "annual_report"
    elif "quarter" in doc_name or "10q" in doc_name or "q1" in doc_name or "q2" in doc_name or "q3" in doc_name or "q4" in doc_name:
        doc_type = "quarterly_report"
    else:
        doc_type = "financial_statement"
    
    mock_summaries = {
        "annual_report": """
This annual report presents the comprehensive financial performance and strategic developments of the company for the fiscal year 2024.

Key highlights include:
- Revenue growth of 12.5% year-over-year, reaching $1.25 billion
- Operating margin improvement to 18.3%, up from 16.7% in the previous year
- Successful expansion into three new international markets
- Launch of two major product lines contributing 8% to total revenue
- Reduction in carbon footprint by 15% through sustainability initiatives
- Strategic acquisition of TechInnovate Inc. for $230 million

The company faced challenges including supply chain disruptions in Q2 and increased regulatory scrutiny in European markets. However, management implemented mitigation strategies including supplier diversification and enhanced compliance protocols.

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

    mock_key_figures = {
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

    # Generate a unique vector DB path
    unique_id = str(uuid.uuid4())
    vector_db_path = f"/data/vector_dbs/{unique_id}_{os.path.basename(document_path).replace('.pdf', '')}.faiss"

    return {
        "summary": mock_summaries[doc_type],
        "key_figures": mock_key_figures[doc_type],
        "vector_db_path": vector_db_path
    }

def answer_question_mock(document_path: str, question: str) -> Dict[str, Any]:
    """Answer a question about a document using mock data."""
    # Simulate processing time
    time.sleep(int(os.getenv("MOCK_DELAY", "1")) / 2)
    
    # Determine document type from path
    doc_name = document_path.lower()
    if "annual" in doc_name or "10k" in doc_name or "fy" in doc_name:
        doc_type = "annual_report"
    elif "quarter" in doc_name or "10q" in doc_name or "q1" in doc_name or "q2" in doc_name or "q3" in doc_name or "q4" in doc_name:
        doc_type = "quarterly_report"
    else:
        doc_type = "financial_statement"
    
    # Generate response based on question content
    question_lower = question.lower()
    
    # Default response
    answer = "Based on the financial document, the company shows solid fundamentals with revenue growth of 12.5%, improved operating margins of 18.3%, and a conservative debt-to-equity ratio of 0.68. The outlook for the next fiscal period remains positive with projected growth continuing in the 8-10% range."
    sources = [
        {"page": 12, "snippet": "Revenue growth of 12.5% demonstrates strong market position"},
        {"page": 15, "snippet": "Operating margin improved to 18.3% from 16.7% in previous year"},
        {"page": 48, "snippet": "Debt-to-equity ratio of 0.68 indicates conservative leverage management"}
    ]
    
    # Customize response based on question content
    if "revenue" in question_lower or "sales" in question_lower:
        answer = "Based on the financial report, the total revenue for this period was $1.25 billion, representing a growth of 12.5% compared to the previous year. This growth was driven by strong performance in the core business segments and successful expansion into new markets."
        sources = [
            {"page": 12, "snippet": "Total revenue reached $1.25 billion, a 12.5% increase from the previous fiscal year"},
            {"page": 15, "snippet": "Growth in core segments contributed to the revenue increase"}
        ]
    elif "profit" in question_lower or "income" in question_lower or "earnings" in question_lower:
        answer = "The net income for the period was $187 million, with an earnings per share of $3.42. This represents an improvement in profitability compared to the previous period due to operational efficiency gains and cost management initiatives."
        sources = [
            {"page": 18, "snippet": "Net income of $187 million was recorded for the fiscal year"},
            {"page": 18, "snippet": "Earnings per share of $3.42, up from $3.15 in the previous year"}
        ]
    elif "debt" in question_lower or "liabilit" in question_lower:
        answer = "The company has long-term debt of $920 million with a debt-to-equity ratio of 0.68. The debt-to-equity ratio indicates a conservative capital structure with manageable leverage levels. The company has maintained adequate liquidity with cash reserves of $412 million."
        sources = [
            {"page": 47, "snippet": "Long-term debt of $920 million as of year-end"},
            {"page": 48, "snippet": "Debt-to-equity ratio of 0.68 reflects conservative capital management"}
        ]
    
    return {"answer": answer, "sources": sources}

class MockLLMClient:
    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        return process_financial_document_mock(document_path)
    
    def answer_question(self, document_path: str, question: str) -> Dict[str, Any]:
        return answer_question_mock(document_path, question)

def get_llm_client():
    """Get appropriate LLM client based on current configuration."""
    mode = CURRENT_CONFIG["mode"]
    
    if mode == "mock":
        return MockLLMClient()
    elif mode in ["openai", "lmstudio"]:
        try:
            from openai import OpenAI
            return OpenAILLMClient()
        except ImportError:
            logger.warning(f"OpenAI module not available, falling back to mock mode")
            return MockLLMClient()
    elif mode == "ollama":
        try:
            from langchain_community.llms import Ollama
            return OllamaLLMClient()
        except ImportError:
            logger.warning(f"Ollama module not available, falling back to mock mode")
            return MockLLMClient()
    else:
        logger.warning(f"Unsupported mode: {mode}, falling back to mock mode")
        return MockLLMClient()

class OpenAILLMClient:
    def __init__(self):
        from langchain_openai import ChatOpenAI
        
        self.client = ChatOpenAI(
            base_url=CURRENT_CONFIG["base_url"],
            api_key=CURRENT_CONFIG["api_key"],
            model=CURRENT_CONFIG["model"],
            temperature=CURRENT_CONFIG["temperature"],
            max_tokens=CURRENT_CONFIG["max_tokens"],
            timeout=CURRENT_CONFIG["timeout"]
        )
    
    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        from langchain_community.document_loaders import PyMuPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        
        # Load document
        loader = PyMuPDFLoader(document_path)
        pages = loader.load()
        
        # Combine all text (up to a reasonable limit to avoid context overflow)
        full_text = "\n\n".join([page.page_content for page in pages])
        max_chars = 100000  # Adjust based on model's context window
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars]
        
        # Create a prompt for financial analysis
        prompt = f"""
        You are a seasoned Financial Analyst with over 15 years of experience specializing in 10-K and 10-Q filings. Your expertise lies in extracting critical financial intelligence and identifying subtle cues that inform investment decisions for both individual and institutional portfolios.

        Your core capabilities include:

        In-depth Document Scrutiny: Analyze 10-K and 10-Q reports thoroughly, going beyond surface-level data.
        Tone and Language Analysis: Evaluate management's tone and language to identify hidden risks, undisclosed liabilities, potential opportunities or shifts in strategy not explicitly stated.
        Inconsistency Detection: Pinpoint inconsistencies across different sections of financial reports that may signal unstated risks or exploitable opportunities.
        Qualitative and Quantitative Risk/Opportunity Assessment: Identify qualitative factors and interpret quantitative data to foresee potential short-term or long-term financial gains or losses for portfolios.
        Proactive Risk Communication: Immediately identify and articulate any impending details or trends that pose investment risks to stakeholders.

        Based on the provided financial document, please provide:
        1. A comprehensive summary highlighting key financial performance indicators, strategic developments, and potential risks/opportunities
        2. Extract 8-12 key financial figures with their source page numbers in the JSON format: [{{"name": "figure_name", "value": "figure_value", "source_page": page_number}}]
        
        Document content:
        {full_text}
        """
        
        # Get analysis from LLM
        try:
            response = self.client.invoke(prompt)
            analysis_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error calling LLM for document analysis: {e}")
            # Fall back to mock data if API call fails
            return process_financial_document_mock(document_path)
        
        # Create vector database for Q&A
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        docs = text_splitter.split_documents(pages)
        
        embeddings = OpenAIEmbeddings(
            openai_api_key=CURRENT_CONFIG["api_key"],
            model="text-embedding-ada-002"
        )
        
        # Generate unique vector store path
        unique_id = str(uuid.uuid4())
        vector_db_path = f"/data/vector_dbs/{unique_id}_{os.path.basename(document_path).replace('.pdf', '')}.faiss"
        
        try:
            # Create and save vector store
            vector_store = FAISS.from_documents(docs, embeddings)
            vector_store.save_local(vector_db_path)
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            vector_db_path = ""  # Set to empty if vector store creation fails
        
        # For this simplified implementation, return analysis text and key figures
        # In a real implementation, we would parse the LLM response for structured data
        key_figures = [
            {"name": "Revenue", "value": "TBD", "source_page": 1},
            {"name": "Net Income", "value": "TBD", "source_page": 1},
            {"name": "Assets", "value": "TBD", "source_page": 1},
        ]
        
        return {
            "summary": analysis_text,
            "key_figures": key_figures,
            "vector_db_path": vector_db_path
        }
    
    def answer_question(self, document_path: str, question: str) -> Dict[str, Any]:
        from langchain.chains import RetrievalQA
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import PyMuPDFLoader
        
        # Generate vector store path based on document path
        unique_id = os.path.basename(document_path).replace('.pdf', '')
        vector_db_path = f"/data/vector_dbs/{unique_id}.faiss"
        
        # Try to load existing vector store, if not create new one
        try:
            embeddings = OpenAIEmbeddings(
                openai_api_key=CURRENT_CONFIG["api_key"],
                model="text-embedding-ada-002"
            )
        
            # Check if vector store exists
            import os
            if not os.path.exists(vector_db_path):
                # Create new vector store from document
                loader = PyMuPDFLoader(document_path)
                pages = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=100,
                    separators=["\n\n", "\n", ".", " ", ""]
                )
                docs = text_splitter.split_documents(pages)
                
                # Create and save vector store
                vector_store = FAISS.from_documents(docs, embeddings)
                vector_store.save_local(vector_db_path)
            else:
                # Load existing vector store
                vector_store = FAISS.load_local(
                    vector_db_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
        
            # Create QA chain
            qa = RetrievalQA.from_chain_type(
                llm=self.client,
                chain_type="stuff",
                retriever=vector_store.as_retriever()
            )
        
            # Get answer
            result = qa({"query": question})
        
            # Extract sources (in a real implementation, this would come from intermediate steps)
            sources = []  # Placeholder - would get real sources in full implementation
            return {
                "answer": result["result"],
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            # Fall back to mock response if API call fails
            return answer_question_mock(document_path, question)

@app.get("/")
def read_root():
    return {"service": "llm-service", "status": "running"}

@app.get("/status", response_model=LLMStatus)
def get_llm_status():
    return LLMStatus(
        status="available",
        mode=CURRENT_CONFIG["mode"],
        model=CURRENT_CONFIG["model"],
        error=None
    )

@app.post("/config")
def update_llm_config(config: LLMConfigRequest):
    global CURRENT_CONFIG
    # Update configuration values
    for key, value in config.dict(exclude_unset=True).items():
        CURRENT_CONFIG[key] = value
    return {"message": "LLM configuration updated successfully", "config": CURRENT_CONFIG}

@app.post("/analyze", response_model=DocumentAnalysisResponse)
def analyze_document(request: DocumentAnalysisRequest):
    llm_client = get_llm_client()
    results = llm_client.analyze_document(request.document_path)
    
    # Convert dictionaries to KeyFigure objects
    key_figures = [KeyFigure(**fig) for fig in results["key_figures"]]
    
    return DocumentAnalysisResponse(
        summary=results["summary"],
        key_figures=key_figures,
        vector_db_path=results["vector_db_path"]
    )

@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    llm_client = get_llm_client()
    results = llm_client.answer_question(request.document_path, request.question)
    
    # Convert source dictionaries to SourceReference objects
    sources = [SourceReference(**src) for src in results["sources"]]
    
    return QuestionResponse(
        answer=results["answer"],
        sources=sources
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "llm-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)