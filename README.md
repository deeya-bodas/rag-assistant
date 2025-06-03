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

- Python 3.9+ (Python 3.12 is supported, but ensure all dependencies are compatible)
- Node.js 18+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (for LLM answers, reach out to deeyabodas1@gmail.com for key access)
- [Git LFS](https://git-lfs.github.com/) (for downloading large files like the corpus and ChromaDB store)

---

## 1. Clone the Repository and Download Large Files

First, make sure you have [Git LFS](https://git-lfs.github.com/) installed.

```bash
git lfs install
git clone https://github.com/your-username/rag-assistant.git
cd rag-assistant
git lfs pull
```

This will download the large pre-built corpus file (e.g., `rag_corpus.jsonl`) and any other large files tracked by LFS (such as the ChromaDB store).

---

## 2. Set Up Environment Variables

Create a `.env` file in the project root:

```
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:**  
> You do **not** need to run any scripts in the `corpus/` directory (such as `corpus_builder.py` or `ingest_to_chromadb.py`).  
> You do **not** need a github token unless you are re-ingesting your corpus, feel free to leave it blank.
> The corpus and vector store are already built and included via Git LFS.

---

## 3. Install Dependencies and Run the App

A helper script is provided to automate setup and startup.

### a. For macOS/Linux users

Run the setup script:

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### b. For Windows users

Run the PowerShell setup script:

```powershell
# In PowerShell, from the project root:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_and_run.ps1
```

This script will:
- Create and activate a Python virtual environment
- Install all Python dependencies
- Check for your `.env` file
- Start the FastAPI backend (`uvicorn`)
- Install frontend dependencies and start the React app

### c. Manual steps (if you prefer)

**Backend:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd backend
uvicorn app:app --reload
```

**Frontend (in a new terminal):**
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Open the App

Visit [http://localhost:5173](http://localhost:5173) in your browser.

- The backend will run at [http://localhost:8000](http://localhost:8000).
- The frontend will run at [http://localhost:5173](http://localhost:5173).

---

## Troubleshooting

- **CORS errors:** Make sure the backend is running and CORS is enabled for `localhost:5173` (already configured in `app.py`).
- **Missing API key:** Ensure your `.env` file is set up correctly.
- **ChromaDB/corpus issues:** The corpus and vector DB should already be included via LFS. If not, please contact deeyabodas1@gmail.com.
- **Dependency errors:** If you see errors related to `protobuf`, `pyarrow`, or other packages, ensure you are using the provided `requirements.txt` and have `protobuf<=3.20.3` and `pyarrow>=14.0.0` installed.

---

## Project Structure

```
rag-assistant/
├── backend/           # FastAPI backend (app.py)
├── corpus/            # Corpus builder and ingestion scripts (ignore for normal use)
├── frontend/          # React frontend (src/App.jsx)
├── chroma_store/      # ChromaDB persistent storage (included via LFS)
├── rag_corpus.jsonl   # Built corpus (included via LFS)
├── requirements.txt   # Python dependencies
├── setup_and_run.sh   # Quickstart script (macOS/Linux)
├── setup_and_run.ps1  # Quickstart script (Windows/PowerShell)
├── .env               # Your API key (not tracked by git)
└── .gitignore         # Ignores venv, .env, and large files
```

---

## Notes for Developers

- **Virtual environments** are ignored by `.gitignore` (`venv/`, `.env/`, `.venv/`, `env/`, `ENV/`).
- **Corpus and ChromaDB store** are tracked with Git LFS and should not be rebuilt unless you are developing the corpus pipeline.

---

## License

This project is for educational and demonstration purposes only.
