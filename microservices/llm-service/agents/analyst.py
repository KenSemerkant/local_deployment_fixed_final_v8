import logging
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

class FinancialAnalystAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Define the prompt for table summarization
        self.prompt = PromptTemplate(
            input_variables=["table_content", "section_name", "ticker", "fiscal_year"],
            template="""
            You are a Senior Financial Analyst. Your task is to interpret the following financial table/data extracted from a 10-K filing.

            **Input Data:**
            {table_content}

            **Context:**
            Section: {section_name}
            Company: {ticker}
            Year: {fiscal_year}

            **Instructions:**
            1.  **Identify Key Trends:** Summarize the most significant changes (YoY growth, margin shifts, debt levels) visible in the data.
            2.  **Explain the "Why":** If the data implies reasons for these changes, mention them.
            3.  **Natural Language Output:** Write a concise paragraph (3-5 sentences) that would allow a search engine to find this table when a user asks a question like "How did revenue change in 2023?" or "What is the debt maturity profile?".
            4.  **Do NOT** simply list the numbers again. Interpret them.

            **Output:**
            """
        )

    def summarize_table(self, table_content: str, metadata: Dict[str, Any]) -> str:
        """
        Summarizes a financial table or section.
        """
        try:
            # We need to access the underlying LangChain LLM object from the client
            # Assuming llm_client has a 'client' attribute which is the LangChain LLM
            llm = self.llm_client.client
            
            chain = LLMChain(llm=llm, prompt=self.prompt)
            
            summary = chain.run({
                "table_content": table_content,
                "section_name": metadata.get("section_name", "Unknown"),
                "ticker": metadata.get("ticker", "Unknown"),
                "fiscal_year": metadata.get("fiscal_year", "Unknown")
            })
            
            return summary.strip()
        except Exception as e:
            logger.error(f"Error summarizing table: {e}")
            return "Error generating summary."
