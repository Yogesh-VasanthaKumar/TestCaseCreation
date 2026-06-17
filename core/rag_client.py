from qdrant_client import QdrantClient
from core.config import Config
from core.logger import logger
import uuid

class RAGClient:
    def __init__(self):
        try:
            url = Config.QDRANT_URL
            api_key = Config.QDRANT_API_KEY if Config.QDRANT_API_KEY else None
            
            # For local memory/testing if no URL
            if not url or url == "memory":
                self.client = QdrantClient(":memory:")
            elif api_key:
                self.client = QdrantClient(url=url, api_key=api_key)
            else:
                self.client = QdrantClient(url=url)
            
            # Setup fastembed model
            self.client.set_model("BAAI/bge-small-en-v1.5")
            self.connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant or initialize model: {e}")
            self.connected = False
            
    def get_collections(self):
        if not self.connected:
            return []
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []

    def add_document(self, collection_name: str, text: str, metadata: dict = None):
        if not self.connected:
            return False
        try:
            if not metadata:
                metadata = {}
            
            # `add` handles fastembed automatically and creates collection if missing
            self.client.add(
                collection_name=collection_name,
                documents=[text],
                metadata=[metadata],
                ids=[uuid.uuid4().hex]
            )
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
            
    def query(self, collection_name: str, query_text: str, limit: int = 2) -> list[str]:
        if not self.connected:
            return []
        try:
            results = self.client.query(
                collection_name=collection_name,
                query_text=query_text,
                limit=limit
            )
            return [res.document for res in results if res.document]
        except Exception as e:
            logger.error(f"Error querying Qdrant: {e}")
            return []
