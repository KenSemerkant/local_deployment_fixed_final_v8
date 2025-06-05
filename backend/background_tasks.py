import json
import logging
import threading
from typing import Dict, Set
from sqlalchemy.orm import Session
from models import Document, AnalysisResult
from llm_integration import process_document

logger = logging.getLogger(__name__)

# Global task manager to track running document processing tasks
class TaskManager:
    def __init__(self):
        self._running_tasks: Dict[int, threading.Event] = {}
        self._lock = threading.Lock()

    def start_task(self, document_id: int) -> threading.Event:
        """Start tracking a task and return a cancellation event."""
        with self._lock:
            cancel_event = threading.Event()
            self._running_tasks[document_id] = cancel_event
            logger.info(f"Started tracking task for document {document_id}")
            return cancel_event

    def cancel_task(self, document_id: int) -> bool:
        """Cancel a running task."""
        with self._lock:
            if document_id in self._running_tasks:
                self._running_tasks[document_id].set()
                logger.info(f"Cancelled task for document {document_id}")
                return True
            return False

    def finish_task(self, document_id: int):
        """Mark a task as finished."""
        with self._lock:
            if document_id in self._running_tasks:
                del self._running_tasks[document_id]
                logger.info(f"Finished tracking task for document {document_id}")

    def is_task_running(self, document_id: int) -> bool:
        """Check if a task is currently running."""
        with self._lock:
            return document_id in self._running_tasks

    def get_running_tasks(self) -> Set[int]:
        """Get set of currently running document IDs."""
        with self._lock:
            return set(self._running_tasks.keys())

# Global task manager instance
task_manager = TaskManager()

def process_document_task(db: Session, document_id: int):
    """Background task to process a document with cancellation support."""
    # Start tracking this task
    cancel_event = task_manager.start_task(document_id)

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return

        # Check if cancelled before starting
        if cancel_event.is_set():
            logger.info(f"Task cancelled before processing: {document_id}")
            document.status = "CANCELLED"
            db.commit()
            return

        # Update status to PROCESSING
        document.status = "PROCESSING"
        db.commit()

        # Process document with cancellation support
        result = process_document(document.file_path, cancel_event)

        # Check if cancelled during processing
        if cancel_event.is_set():
            logger.info(f"Task cancelled during processing: {document_id}")
            document.status = "CANCELLED"
            db.commit()
            return

        if "error" in result:
            logger.error(f"Error processing document: {result['error']}")
            document.status = "ERROR"
            db.commit()
            return

        # Check if cancelled before saving results
        if cancel_event.is_set():
            logger.info(f"Task cancelled before saving results: {document_id}")
            document.status = "CANCELLED"
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
        # Check if this was due to cancellation
        if cancel_event.is_set():
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "CANCELLED"
                db.commit()
        else:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "ERROR"
                db.commit()
    finally:
        # Always clean up task tracking
        task_manager.finish_task(document_id)