import voyageai
from pinecone import Pinecone, ServerlessSpec, Index
from typing import List, Dict
import itertools
from src.utils.logging_config import setup_logger
from src.config import api_keys

logger = setup_logger("db_module")

class VectorStoreService:
    def __init__(self, index: Index = None):
        """Initialize VectorStore with optional existing index"""
        self.index = index or self._initialize_pinecone()
        self.voyage_client = voyageai.Client(api_key=api_keys.VOYAGE_API_KEY)
        
    def _initialize_pinecone(self) -> Index:
        """Initialize Pinecone index"""
        try:
            pc = Pinecone(api_key=api_keys.PINECONE_API_KEY)
            index_name = "voyageai-pinecone-text"
            
            # First try to get the existing index
            try:
                logger.info(f"Attempting to connect to existing index: {index_name}")
                return pc.Index(index_name)
            except Exception as e:
                logger.info(f"Index {index_name} does not exist, creating new one")
                # If index doesn't exist, create it
                pc.create_index(
                    name=index_name,
                    dimension=1024,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Successfully created new index: {index_name}")
                return pc.Index(index_name)
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    async def query(self, query_text: str, limit: int = 5) -> List[Dict]:
        """Query the vector store and return relevant results"""
        try:
            # Generate embedding for query
            query_embedding = self.voyage_client.embed(
                texts=[query_text],
                model='voyage-3',
                input_type='document'
            ).embeddings[0]
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True
            )
            
            # Rerank results if available
            if hasattr(self, 'rerank_results'):
                return await self.rerank_results(query_text, results.matches)
                
            return results.matches
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []

    async def index_documents(self, documents: List[Dict]) -> bool:
        """Index new documents in batches"""
        try:
            # Generate embeddings
            embeddings = self._generate_embeddings(documents)
            
            # Prepare vectors for indexing
            vectors = [
                (doc["id"], embedding, {"text": doc["text"]}) 
                for doc, embedding in zip(documents, embeddings)
            ]
            
            # Index in batches
            for batch in self._create_batches(vectors, 200):
                self.index.upsert(vectors=batch)
                
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return False

    def _generate_embeddings(self, documents: List[Dict]) -> List:
        """Generate embeddings for documents using Voyage AI"""
        try:
            batch_size = 128
            all_embeddings = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                texts = [doc["text"] for doc in batch]
                
                embeddings = self.voyage_client.embed(
                    texts=texts,
                    model='voyage-3',
                    input_type='document',
                    truncation=True
                ).embeddings
                
                all_embeddings.extend(embeddings)
                
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    @staticmethod
    def _create_batches(items: List, batch_size: int):
        """Create batches of specified size from list"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size] 