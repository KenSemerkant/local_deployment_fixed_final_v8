import json
import logging
from sqlalchemy.orm import Session
from models import Document, AnalysisResult
from llm_integration import process_document

logger = logging.getLogger(__name__)

def process_document_task(db: Session, document_id: int):
    """Background task to process a document."""
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document not found: {document_id}")
        return
    
    try:
        # Update status to PROCESSING
        document.status = "PROCESSING"
        db.commit()
        
        # Process document
        result = process_document(document.file_path)
        
        if "error" in result:
            logger.error(f"Error processing document: {result['error']}")
            document.status = "ERROR"
            db.commit()
            return
        
        # Create analysis result
        analysis_result = AnalysisResult(
            summary=result["summary"],
            key_figures=json.dumps(result["key_figures"]),
            vector_db_path=result["vector_db_path"],
            document_id=document.id
        )
        db.add(analysis_result)
        
        # Update document status
        document.status = "COMPLETED"
        db.commit()
        
        logger.info(f"Document processed successfully: {document_id}")
    except Exception as e:
        logger.error(f"Error in process_document_task: {str(e)}")
        document.status = "ERROR"
        db.commit()