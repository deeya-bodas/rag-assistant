# Visa Developer AI Agent Chat

This project is a Retrieval-Augmented Generation (RAG) assistant for Visa's public code and documentation. It uses a React frontend, a FastAPI backend, ChromaDB for vector storage, and Gemini for LLM-powered answers.

---

## Features

- **Chat UI**: Ask questions about Visa's codebase and developer docs.
- **RAG Backend**: Retrieves relevant code/doc chunks using embeddings and ChromaDB.
- **LLM Integration**: Uses Gemini to generate answers based on retrieved context.
- **Source Attribution**: Shows links to the sources used in each answer.

---

## Prerequisites

- Python 3.9+
- Node.js 18+
- [GitHub Personal Access Token](https://github.com/settings/tokens) (for corpus building)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (for LLM answers)

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/rag-assistant.git
cd rag-assistant
```

---

## 2. Set Up Python Backend

### a. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### b. Install Python dependencies

```bash
pip install -r requirements.txt
```

### c. Set up environment variables

Create a `.env` file in the project root:

```
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 3. Build the Corpus

This will clone Visa's public GitHub repos and scrape Visa developer docs.

```bash
cd corpus
python corpus_builder.py
```

---

## 4. Ingest the Corpus into ChromaDB

```bash
python ingest_to_chromadb.py
```

---

## 5. Start the Backend API

```bash
cd ../backend
uvicorn app:app --reload
```

The backend will run at [http://localhost:8000](http://localhost:8000).

---

## 6. Start the Frontend (React)

```bash
cd ../frontend
npm install
npm run dev
```

The frontend will run at [http://localhost:5173](http://localhost:5173).

---

## 7. Open the App

Visit [http://localhost:5173](http://localhost:5173) in your browser.

---

## Troubleshooting

- **CORS errors**: Make sure the backend is running and CORS is enabled for `localhost:5173`.
- **Missing tokens/keys**: Ensure your `.env` file is set up correctly.
- **ChromaDB issues**: Delete the `chroma_store` directory and re-run ingestion if you encounter vector DB errors.

---

## Project Structure

```
rag-assistant/
├── backend/           # FastAPI backend
│   └── app.py
├── corpus/            # Corpus builder and ingestion scripts
│   ├── corpus_builder.py
│   └── ingest_to_chromadb.py
├── frontend/          # React frontend
│   └── src/App.jsx
├── chroma_store/      # ChromaDB persistent storage (created after ingestion)
├── rag_corpus.jsonl   # Built corpus (created after running corpus_builder.py)
├── requirements.txt
└── .env
```

---

## License

This project is for educational and demonstration purposes only.
