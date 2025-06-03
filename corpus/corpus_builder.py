import os
import json
import tiktoken
from pathlib import Path
from git import Repo
from github import Github
from dotenv import load_dotenv
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import re

# Load environment variables from a .env file into the program's environment
load_dotenv()

# Retrieve GitHub token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("No GITHUB_TOKEN found. Please set it in your .env file.")

# Constants/settings
ORG_NAME = "visa"
CLONE_DIR = "visa_repos"
CORPUS_PATH = "rag_corpus.jsonl"
MAX_TOKENS = 512
BASE_DOC_URL = "https://developer.visa.com"
MAX_WEB_PAGES = 400

# Initialize GitHub API client using token
g = Github(GITHUB_TOKEN)
enc = tiktoken.get_encoding("cl100k_base")

visited = set()
to_visit = set([BASE_DOC_URL])

def count_tokens(text):
    return len(enc.encode(text))

def classify_file(file_path):
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
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return []
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), MAX_TOKENS):
        sub = enc.decode(tokens[i:i + MAX_TOKENS])
        chunks.append(sub)
    return chunks

def chunk_text(text, max_tokens=MAX_TOKENS, overlap=50):
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens - overlap):
        chunk = enc.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

def is_valid_link(link):
    parsed = urlparse(link)
    return link.startswith(BASE_DOC_URL) and not any(
        skip in parsed.path for skip in ["/static", "/images", "/fonts", "/contact"]
    )

def generate_tags(text, file_type, language, source_url=None):
    tags = set()
    tags.add(file_type)
    tags.add(language.lower())
    if "curl" in text or "POST /v" in text:
        tags.add("api_call_example")
    if re.search(r"https://sandbox\.api\.visa\.com", text):
        tags.add("visa_api")
    if "token" in text.lower():
        tags.add("tokenization")
    if "authentication" in text.lower():
        tags.add("authentication")
    if "fraud" in text.lower():
        tags.add("fraud_detection")
    if source_url:
        parsed = urlparse(source_url)
        parts = parsed.path.strip("/").split("/")
        tags.update([p.replace("-", "_") for p in parts if p])
    return list(tags)

def clean_metadata(meta):
    # Ensure all metadata values are not None and are serializable
    return {k: (v if v is not None else "") for k, v in meta.items()}

def scrape_visa_docs():
    docs = []
    for _ in tqdm(range(MAX_WEB_PAGES)):
        if not to_visit:
            break
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, 'html.parser')
            text = ' '.join(soup.get_text(separator=' ').split())
            links = {urljoin(BASE_DOC_URL, a['href']) for a in soup.find_all('a', href=True)}
            to_visit.update([l for l in links if is_valid_link(l)])
            if len(text) < 100:
                continue
            for i, chunk in enumerate(chunk_text(text)):
                doc_id = hashlib.md5((url + chunk).encode()).hexdigest()
                tags = generate_tags(chunk, "visa_docs", "English", url)
                metadata = clean_metadata({
                    "source": url,
                    "file_path": "",
                    "chunk_index": i,
                    "token_count": count_tokens(chunk),
                    "type": "visa_docs",
                    "tags": tags,
                    "language": "English"
                })
                docs.append({
                    "id": doc_id,
                    "document": chunk,
                    "metadata": metadata
                })
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
    return docs

def build_corpus():
    corpus = []
    org = g.get_organization(ORG_NAME)
    repos = org.get_repos()
    Path(CLONE_DIR).mkdir(exist_ok=True)
    for repo in repos:
        print(f"Processing repository: {repo.name}")
        repo_path = Path(CLONE_DIR) / repo.name
        if not repo_path.exists():
            print(f"Cloning {repo.name}...")
            Repo.clone_from(repo.clone_url, str(repo_path))
        for file_path in repo_path.rglob("*.*"):
            if file_path.suffix in {".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".txt"}:
                file_type = classify_file(file_path)
                language = get_language(file_path)
                chunks = chunk_file(file_path)
                for i, chunk in enumerate(chunks):
                    unique_str = f"{ORG_NAME}_{repo.name}_{file_path}_{i}"
                    unique_id = hashlib.md5(unique_str.encode()).hexdigest()
                    tags = generate_tags(chunk, file_type, language)
                    # Construct the GitHub URL for the file (assuming 'main' branch)
                    github_url = f"https://github.com/{ORG_NAME}/{repo.name}/blob/main/{file_path.relative_to(repo_path)}"
                    repo_url = f"https://github.com/{ORG_NAME}/{repo.name}"
                    metadata = clean_metadata({
                        "source": github_url if file_path else repo_url,
                        "file_path": str(file_path.relative_to(repo_path)),
                        "chunk_index": i,
                        "token_count": count_tokens(chunk),
                        "type": file_type,
                        "tags": tags,
                        "language": language
                    })
                    corpus.append({
                        "id": unique_id,
                        "document": chunk,
                        "metadata": metadata
                    })
    print("Scraping Visa developer docs...")
    corpus.extend(scrape_visa_docs())
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        for item in corpus:
            f.write(json.dumps(item) + "\n")
    print(f"Corpus saved to {CORPUS_PATH} with {len(corpus)} chunks.")

if __name__ == "__main__":
    build_corpus()
