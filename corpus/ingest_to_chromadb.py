import os
import json
import time
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient


CORPUS_PATH = os.path.join(os.path.dirname(__file__), "rag_corpus.jsonl")
COLLECTION_NAME = "visa_code_corpus"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rag-assistant", "chroma_store"))

# Function to load and clean the corpus from a JSONL file
def load_corpus(corpus_path):
    with open(corpus_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                # Parse each line as a JSON object
                item = json.loads(line)

                # Skip if 'document' field is missing or empty
                if not item.get("document", "").strip():
                    print(f"⚠️ Skipping empty content on line {idx}")
                    continue

                # Extract and clean metadata
                meta = item.get("metadata", {})
                metadata = {
                    "source": meta.get("source"),
                    "file_path": meta.get("file_path"),
                    "chunk_index": meta.get("chunk_index"),
                    "token_count": meta.get("token_count"),
                    "type": meta.get("type"),
                    "tags": ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags", []), list) else str(meta.get("tags", "")),
                    "language": meta.get("language")
                }

                # Yield the document record with metadata as-is
                yield {
                    "id": item["id"],
                    "document": item["document"],
                    "metadata": metadata
                }

            except json.JSONDecodeError:
                # Catch and report JSON formatting errors
                print(f"Invalid JSON on line {idx}: {line[:80]}")

# Add this function to ingest_to_chromadb.py
def clean_metadata(meta):
    return {k: (v if v is not None else "") for k, v in meta.items()}

# Function to embed documents and store them into a local ChromaDB
def ingest_to_chromadb(corpus_path, collection_name, model_name, persist_dir):
    # Load the sentence-transformer model to generate embeddings
    embedder = SentenceTransformer(model_name)

    # Initialize ChromaDB client with disk persistence
    client = PersistentClient(path=persist_dir)

    # Create or get the named collection to store documents
    collection = client.get_or_create_collection(name=collection_name)

    # Set up batching for efficient processing
    batch_size = 64
    buffer = []
    total_docs = 0
    start_time = time.time()

    # Load and buffer documents in batches
    for doc in load_corpus(corpus_path):
        buffer.append(doc)

        # Once batch size is hit, process and ingest it
        if len(buffer) >= batch_size:
            batch_start = time.time()

            # Extract fields for ChromaDB
            ids = [doc["id"] for doc in buffer]
            texts = [doc["document"] for doc in buffer]
            metadatas = [clean_metadata(doc["metadata"]) for doc in buffer]
            embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

            # Add the batch to the collection
            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            total_docs += len(buffer)
            print(f"Ingested {total_docs} docs (last batch in {time.time() - batch_start:.2f}s)")
            # Clear buffer before starting the next batch
            buffer = []

    # Process any remaining documents after loop
    if buffer:
        batch_start = time.time()
        ids = [doc["id"] for doc in buffer]
        texts = [doc["document"] for doc in buffer]
        metadatas = [clean_metadata(doc["metadata"]) for doc in buffer]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        total_docs += len(buffer)
        print(f"Ingested final {len(buffer)} docs (in {time.time() - batch_start:.2f}s)")
    print(f"ChromaDB store should be at: {persist_dir}")
    print(f"Total docs ingested: {total_docs}")
if __name__ == "__main__":
    ingest_to_chromadb(CORPUS_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME, CHROMA_PERSIST_DIR)
