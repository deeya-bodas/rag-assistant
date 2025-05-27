import os
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

# Directory where ChromaDB will persist data
CHROMA_PERSIST_DIR = "./chroma_store"
# Name of the collection in ChromaDB
COLLECTION_NAME = "visa_code_corpus"
# Name of the embedding model to use
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
# Number of top results to retrieve
TOP_K = 5

# Example query
QUERY = "How do I authenticate using Visa API?"

def query_chroma_store(query, top_k=5):
    # Load the embedding model
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    # Connect to the persistent ChromaDB client
    client = PersistentClient(path=CHROMA_PERSIST_DIR)
    # Get or create the collection
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    # Encode the query to get its embedding
    query_embedding = embedder.encode([query]).tolist()
    # Query the collection for similar documents
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    print(f"\nTop {top_k} results for query: '{query}'")
    for i in range(top_k):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        dist = results["distances"][0][i]
        print(f"\nResult {i+1}:")
        print(f"Document: {doc[:300]}...")
        print(f"Metadata: {meta}")
        print(f"Distance: {dist:.4f}")

if __name__ == "__main__":
    query_chroma_store(QUERY, top_k=TOP_K)
