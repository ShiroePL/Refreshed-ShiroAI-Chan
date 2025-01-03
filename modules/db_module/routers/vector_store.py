from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()

class VectorQuery(BaseModel):
    query: str
    limit: int = 5

@router.post("/vector/query")
async def query_vector_store(
    query: VectorQuery,
    vector_store=Depends(lambda: app.state.vector_store)
):
    """Query the vector store for relevant documents"""
    results = await vector_store.query(query.query, query.limit)
    return results

@router.post("/vector/index")
async def index_documents(
    documents: List[Dict],
    vector_store=Depends(lambda: app.state.vector_store)
):
    """Index new documents in the vector store"""
    success = await vector_store.index_documents(documents)
    return {"success": success} 