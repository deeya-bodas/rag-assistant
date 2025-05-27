from fastapi import FastAPI, Query, HTTPException  # <-- add HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = FastAPI()

# Paths
CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rag-assistant", "chroma_store"))
COLLECTION_NAME = "visa_code_corpus"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Load model and DB
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
client = PersistentClient(path=CHROMA_PERSIST_DIR)
collection = client.get_collection(COLLECTION_NAME)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search_rag(req: QueryRequest):
    embedding = embedder.encode(req.query).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=req.top_k)

    docs = [
        {
            "id": doc_id,
            "text": doc,
            "metadata": meta
        }
        for doc_id, doc, meta in zip(results["ids"][0], results["documents"][0], results["metadatas"][0])
    ]
    return {"query": req.query, "results": docs}

@app.post("/ask")
async def ask_rag(request: QueryRequest):
    try:
        query_embedding = embedder.encode([request.query])[0].tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=request.top_k)  # <-- use top_k

        docs = results["documents"][0]
        context = "\n---\n".join(docs)

        prompt = f"""You are an assistant using Visa's publicly facing repositories to aid users who are asking questions about the repository. Use primarily the retrieved documents to answer the user's question, if needed supplement with external resoruces and cite where this information comes from. End all of your answers with a joke."
{context}
---
User question: {request.query}
Answer:"""

        response = model.generate_content(prompt)
        return {"answer": response.text, "context": docs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))