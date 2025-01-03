import voyageai

# Initialize VoyageAI client
vc = voyageai.Client(api_key=VOYAGE_API_KEY)

# Function to rerank the retrieved documents based on the user query
def rerank_results(query: str, retrieved_documents: List[dict], top_k: int = 5) -> List[dict]:
    """
    Function to rerank the retrieved documents based on relevance to the query.
    
    Args:
        query (str): The user's search query.
        retrieved_documents (List[dict]): A list of documents (chunks) retrieved from Pinecone.
        top_k (int): The number of top results to return after reranking. Defaults to 5.
        
    Returns:
        List[dict]: The top-k documents sorted by relevance.
    """
    # Extract the text from each retrieved document (chunk)
    documents = [doc['text'] for doc in retrieved_documents]

    # Use VoyageAI's rerank model
    reranking = vc.rerank(query, documents, model="rerank-2", top_k=top_k)
    
    # Format the reranked results to return the relevant chunks
    reranked_results = []
    for result in reranking.results:
        reranked_results.append({
            "document": result.document,
            "relevance_score": result.relevance_score
        })
    
    return reranked_results

# Example: Search and rerank the top 3 most relevant documents
def search_and_rerank(query: str):
    # Step 1: Search your Pinecone index to retrieve the relevant chunks
    retrieved_documents = pinecone_search(query)  # Function to search Pinecone, not shown here
    
    # Step 2: Rerank the retrieved documents based on relevance to the query
    top_results = rerank_results(query, retrieved_documents, top_k=3)
    
    # Display the top 3 reranked results
    for result in top_results:
        print(f"Document: {result['document']}")
        print(f"Relevance Score: {result['relevance_score']}")
