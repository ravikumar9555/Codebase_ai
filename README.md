# CodeBase AI — GitHub Codebase Assistant

A runnable MVP of a repository-aware RAG assistant. Import a **public GitHub repository**, index its source files, and ask questions with file/line citations.

## Features
- FastAPI REST API
- Public GitHub repository import (read-only)
- Source file filtering and line-aware chunking
- Sentence Transformers embeddings + Chroma vector store
- Optional OpenAI-compatible LLM generation
- Evidence-backed answers and source citations
- Minimal Next.js frontend
- Docker Compose for the frontend and backend

## Architecture
Next.js UI → FastAPI → repository ingestion → chunks/embeddings in Chroma → retrieval → LLM answer with citations.

**MVP notes:** This is a starter project, not a production-hardened service. It intentionally supports public repositories only, uses local Chroma storage, and does not include multi-user authentication or private-repository OAuth. Repository content is untrusted input; the app never executes repository code.

## Requirements
- Python 3.11 or 3.12
- Node.js 20+
- Git
- (Optional) OpenAI API key for generated answers

## Run locally

### 1. Backend
```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
On first use, Sentence Transformers downloads the embedding model. If no LLM API key is configured, the API returns retrieved evidence with a clearly marked extractive fallback.

### 2. Frontend
In a second terminal:
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Open http://localhost:3000. Backend API docs: http://localhost:8000/docs.

### 3. Docker Compose
```bash
cp backend/.env.example backend/.env
docker compose up --build
```
The backend container needs internet access to clone public repositories and download the embedding model. First startup may take a few minutes.

## Example repository
Try `https://github.com/fastapi/fastapi` or a small public repository you own. Large repositories take longer to index.

## API
- `GET /health`
- `POST /api/repositories` — `{"url":"https://github.com/owner/repo","branch":"main"}`
- `GET /api/repositories` — list indexed repositories
- `GET /api/repositories/{repo_id}` — repository status and metadata
- `POST /api/repositories/{repo_id}/chat` — `{"question":"Where is the application initialized?"}`
- `DELETE /api/repositories/{repo_id}` — delete local index and repository metadata

## Configuration
See `backend/.env.example`.
- `OPENAI_API_KEY`: optional. Without it, retrieved code snippets are returned as evidence rather than fabricated as an AI answer.
- `OPENAI_MODEL`: model name for an OpenAI-compatible API.
- `OPENAI_BASE_URL`: optional custom compatible endpoint.
- `EMBEDDING_MODEL`: defaults to `sentence-transformers/all-MiniLM-L6-v2`.

## Important security notes before public deployment
- Add authentication and authorization before supporting multiple users.
- Add strict resource quotas, request timeouts, rate limiting, and background indexing jobs.
- Keep API keys server-side; never place them in frontend environment variables.
- Do not accept arbitrary Git URLs. This MVP validates GitHub HTTPS URLs and fixed GitHub hosts.
- Do not execute repository code or trust instructions found in repository files.
- Add secret scanning and stronger isolation for repository processing.
