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

def process_document_mock(file_path: str) -> Dict[str, Any]:
    """Process document using mock data."""
    time.sleep(MOCK_DELAY)  # Simulate processing time
    
    doc_type = "annual_report"  # Default type
    
    summary = MOCK_SUMMARIES.get(doc_type, MOCK_SUMMARIES["annual_report"])
    key_figures = MOCK_KEY_FIGURES.get(doc_type, MOCK_KEY_FIGURES["annual_report"])
    
    return {
        "summary": summary,
        "key_figures": key_figures,
        "vector_db_path": os.path.join("/data/vector_db", os.path.basename(file_path))
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
    # In a real implementation, it would call the appropriate LLM backend
    file_path = request.query_params.get("file_path", "")
    
    if LLM_MODE == "mock":
        result = process_document_mock(file_path)
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
    # In a real implementation, it would call the appropriate LLM backend
    document_id = request.query_params.get("document_id", "")
    question = request.query_params.get("question", "")
    
    if LLM_MODE == "mock":
        result = ask_question_mock(document_id, question)
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