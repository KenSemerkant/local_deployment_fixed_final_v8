import os
import uuid
import logging
import redis
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None

class ParentChildSplitter:
    def __init__(self, parent_chunk_size=4000, child_chunk_size=512, child_overlap=64):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap
        
        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.kv_store = redis.from_url(redis_url)
            self.kv_store.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.kv_store = None

    def process_document(self, structured_doc: Dict[str, Any]) -> List[Chunk]:
        """
        Input: Structured JSON from Layout Parser
        Output: List of Child Chunks for Vectorization
        """
        all_child_chunks = []
        
        if not self.kv_store:
            logger.warning("Redis not available, skipping parent block storage")

        for section in structured_doc.get('sections', []):
            # 1. Create Parent Block
            parent_id = str(uuid.uuid4())
            parent_content = section['content']
            
            # Store Parent Block in KV Store (Retrievable Context)
            if self.kv_store:
                try:
                    key = f"parent:{parent_id}"
                    value = {
                        "content": parent_content,
                        "section_name": section['title'],
                        "ticker": structured_doc.get('ticker', 'UNKNOWN'),
                        "fiscal_year": structured_doc.get('fiscal_year', 'UNKNOWN')
                    }
                    # Store as hash or JSON string. Using hash for simplicity in this example if fields are flat
                    # But content can be large, so maybe just store the content string if that's the main thing
                    # Let's store metadata as separate keys or use JSON serialization
                    import json
                    self.kv_store.set(key, json.dumps(value))
                    # Set expiry to avoid infinite growth in this demo (e.g., 24 hours)
                    self.kv_store.expire(key, 86400) 
                except Exception as e:
                    logger.error(f"Error storing parent block in Redis: {e}")

            # 2. Generate Child Chunks (Search Units)
            child_chunks = self._split_text(parent_content)
            
            for i, chunk_text in enumerate(child_chunks):
                child_id = str(uuid.uuid4())
                
                # 3. Inject Metadata
                metadata = {
                    "parent_id": parent_id,
                    "chunk_index": i,
                    "section_name": section['title'],
                    "ticker": structured_doc.get('ticker', 'UNKNOWN'),
                    "fiscal_year": structured_doc.get('fiscal_year', 'UNKNOWN'),
                    "source_filename": structured_doc.get('filename', 'unknown'),
                    "type": "narrative"
                }
                
                all_child_chunks.append(Chunk(
                    id=child_id,
                    content=chunk_text,
                    metadata=metadata
                ))

        logger.info(f"Generated {len(all_child_chunks)} child chunks from {len(structured_doc.get('sections', []))} sections")
        return all_child_chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text into overlapping windows of self.child_chunk_size
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.child_chunk_size,
            chunk_overlap=self.child_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        return splitter.split_text(text)
