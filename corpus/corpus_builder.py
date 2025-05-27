import os
import json
import tiktoken
from pathlib import Path
from git import Repo
from github import Github
from dotenv import load_dotenv
import hashlib

# Load environment variables from a .env file into the program's environment
load_dotenv()

# Retrieve GitHub token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Raise an error if the GitHub token is not found
if not GITHUB_TOKEN:
    raise ValueError("No GITHUB_TOKEN found. Please set it in your .env file.")

# Constants/settings
ORG_NAME = "visa"  # GitHub organization to scrape repos from
CLONE_DIR = "visa_repos"  # Local directory to clone repos into
CORPUS_PATH = "rag_corpus.jsonl"  # Output file to save the corpus
MAX_TOKENS = 512  # Max tokens per chunk for splitting files

# Initialize GitHub API client using token
g = Github(GITHUB_TOKEN)
# Initialize the tokenizer for counting and chunking tokens (OpenAI's cl100k_base)
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    # Count the number of tokens in the given text using the tokenizer
    return len(enc.encode(text))

def classify_file(file_path):
    # Classify file type for tagging, based on path and file extension
    ext = file_path.suffix
    path_str = str(file_path).lower()

    if "example" in path_str or ext in {".example", ".sample"}:
        return "code_example"
    elif ext in {".md", ".txt"} or "docs" in path_str:
        return "documentation"
    elif ext in {".json"} and "swagger" in path_str:
        return "api_reference"
    elif ext in {".jsx", ".tsx", ".vue"}:
        return "component_snippet"
    elif "config" in path_str or file_path.name in {"package.json", "vite.config.js"}:
        return "config"
    else:
        return "function_snippet"

def get_language(file_path):
    # Infer programming language from file extension for metadata tagging
    ext = file_path.suffix.lower()
    return {
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".vue": "Vue",
        ".md": "Markdown",
        ".json": "JSON",
        ".txt": "PlainText"
    }.get(ext, "PlainText")

def chunk_file(file_path):
    # Read file and chunk its content into token-limited segments
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        # Return empty list on read errors (binary files, permission issues, etc)
        return []

    tokens = enc.encode(text)
    chunks = []
    # Break tokens into segments with length <= MAX_TOKENS
    for i in range(0, len(tokens), MAX_TOKENS):
        sub = enc.decode(tokens[i:i + MAX_TOKENS])
        chunks.append(sub)
    return chunks

def build_corpus():
    # Main function to build the corpus from all repositories in the organization
    corpus = []

    # Access the GitHub organization
    org = g.get_organization(ORG_NAME)
    repos = org.get_repos()

    # Create local directory to clone repos into (if it doesn't exist)
    Path(CLONE_DIR).mkdir(exist_ok=True)

    for repo in repos:
        print(f"Processing repository: {repo.name}")
        repo_path = Path(CLONE_DIR) / repo.name

        # Clone repo if not already cloned locally
        if not repo_path.exists():
            print(f"Cloning {repo.name}...")
            Repo.clone_from(repo.clone_url, str(repo_path))

        # Recursively iterate over files with certain extensions to include
        for file_path in repo_path.rglob("*.*"):
            if file_path.suffix in {".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".txt"}:
                file_type = classify_file(file_path)
                language = get_language(file_path)
                chunks = chunk_file(file_path)

                # For each chunk, create a ChromaDB-compatible JSON object
                for i, chunk in enumerate(chunks):
                    # Use a hash of the full path to ensure uniqueness
                    unique_str = f"{ORG_NAME}_{repo.name}_{file_path}_{i}"
                    unique_id = hashlib.md5(unique_str.encode()).hexdigest()
                    corpus.append({
                        "id": unique_id,
                        "document": chunk,
                        "metadata": {
                            "repo": repo.name,  # Repository name
                            "file_path": str(file_path.relative_to(repo_path)),  # Relative file path
                            "chunk_index": i,  # Index of the chunk in the file
                            "token_count": count_tokens(chunk),  # Number of tokens in the chunk
                            "type": file_type,  # File type classification
                            "tags": file_type.upper(),  # Tag for filtering/searching
                            "language": language  # Programming language
                        }
                    })

    # Save corpus as JSON Lines for easy ingestion in ChromaDB
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        for item in corpus:
            f.write(json.dumps(item) + "\n")

    print(f"Corpus saved to {CORPUS_PATH} with {len(corpus)} chunks.")

if __name__ == "__main__":
    # Run the corpus builder if this script is executed directly
    build_corpus()
