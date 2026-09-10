import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from django.conf import settings
from .models import BusinessClient, KnowledgeDocument

logger = logging.getLogger(__name__)

# Vector DB directory in project
VECTOR_DB_DIR = os.path.join(settings.BASE_DIR, 'chroma_db_store')
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# Initialize Persistent Chroma Client
chroma_client = chromadb.PersistentClient(
    path=VECTOR_DB_DIR,
    settings=Settings(anonymized_telemetry=False, is_persistent=True)
)

class VectorRAGEngine:
    @staticmethod
    def get_collection_name(client: BusinessClient) -> str:
        """
        Creates clean isolated collection name per business client.
        """
        clean_name = f"client_{client.id.hex}"
        return clean_name

    @classmethod
    def get_or_create_collection(cls, client: BusinessClient):
        coll_name = cls.get_collection_name(client)
        return chroma_client.get_or_create_collection(
            name=coll_name,
            metadata={"client_id": str(client.id), "client_name": client.name}
        )

    @classmethod
    def add_or_update_document(cls, client: BusinessClient, doc: KnowledgeDocument):
        """
        Chunk and embed document into client's Vector DB collection.
        """
        try:
            collection = cls.get_or_create_collection(client)
            doc_id = str(doc.id)
            
            # Delete old vector if updating
            try:
                collection.delete(ids=[doc_id])
            except Exception:
                pass

            collection.add(
                ids=[doc_id],
                documents=[f"Title: {doc.page_title}\n{doc.content_text}"],
                metadatas=[{
                    "doc_id": doc_id,
                    "title": doc.page_title[:100],
                    "content_type": doc.content_type
                }]
            )
        except Exception as e:
            logger.error(f"[Vector DB Add Error]: {e}")

    @classmethod
    def delete_document(cls, client: BusinessClient, doc_id: str):
        try:
            collection = cls.get_or_create_collection(client)
            collection.delete(ids=[str(doc_id)])
        except Exception as e:
            logger.error(f"[Vector DB Delete Error]: {e}")

    @classmethod
    def clear_client_collection(cls, client: BusinessClient):
        try:
            coll_name = cls.get_collection_name(client)
            chroma_client.delete_collection(name=coll_name)
        except Exception as e:
            logger.error(f"[Vector DB Clear Error]: {e}")

    @classmethod
    def similarity_search(cls, client: BusinessClient, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Perform Semantic Vector Search using Cosine Similarity.
        """
        try:
            collection = cls.get_or_create_collection(client)
            count = collection.count()
            if count == 0:
                return []

            actual_k = min(top_k, count)
            results = collection.query(
                query_texts=[query],
                n_results=actual_k
            )

            matched = []
            if results and 'documents' in results and results['documents']:
                for i in range(len(results['documents'][0])):
                    matched.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                    })
            return matched
        except Exception as e:
            logger.error(f"[Vector DB Search Error]: {e}")
            return []
