from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import logging

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
CHROMA_PERSIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "rag-assistant", "chroma_store")
)
COLLECTION_NAME = "visa_code_corpus"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Load sentence transformer and ChromaDB
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
client = PersistentClient(path=CHROMA_PERSIST_DIR)
collection = client.get_collection(COLLECTION_NAME)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

# Input schema
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
        # Embed the query
        query_embedding = embedder.encode([request.query])[0].tolist()

        # Retrieve top-k results from Chroma
        results = collection.query(query_embeddings=[query_embedding], n_results=request.top_k)

        docs = results["documents"][0]
        metadatas = results["metadatas"][0]

        # Build context sections with text and source URL
        context_sections = []
        for doc, meta in zip(docs, metadatas):
            source = meta.get("source", "") if meta else ""
            context_sections.append({
                "text": doc,
                "source": source
            })

        # Build context string for Gemini prompt
        context_str = "\n---\n".join(
            f"{section['text']}\nSource: {section['source']}" if section['source'] else section['text']
            for section in context_sections
        )

        # Construct prompt for Gemini
        prompt = f"""You are an assistant using Visa's publicly facing repositories and developer center to aid users who are asking questions about Visa's product. Use primarily the retrieved documents to answer the user's question. If needed, supplement with external resources and knowledge, and generate code snippets. If you do not have a sufficient answer, suggest that the user visits the Visa developer portal. Also please refer to all context you are provided as "my knowledge base". If the user asks you something unsafe, or something extremely unrelated to your knowledge base, please apologize and tell them that "I am not equipped to answer this question".

Context:
{context_str}
---
User question: {request.query}
Answer:"""

        # Generate answer using Gemini
        response = model.generate_content(prompt)

        # Return answer and context with URLs
        return {
            "answer": response.text,
            "context": context_sections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
