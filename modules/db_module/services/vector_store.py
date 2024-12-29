from pinecone import Index

class VectorStoreService:
    def __init__(self, index: Index):
        self.index = index
    
    async def query_context(self, query_vector: list, limit: int = 5):
        results = self.index.query(
            vector=query_vector,
            top_k=limit,
            include_metadata=True
        )
        return results.matches 