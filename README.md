# CodeBase AI — AI-Powered GitHub Codebase Assistant

An AI-powered codebase assistant that helps developers understand, explore, and ask questions about GitHub repositories using **Retrieval-Augmented Generation (RAG)**. It indexes source code, retrieves relevant code snippets using semantic similarity, and generates contextual answers with file-level citations.

## Overview

Understanding a large codebase can be time-consuming, especially when working with unfamiliar projects. CodeBase AI simplifies code exploration by allowing users to import a GitHub repository and ask natural-language questions about its implementation.

Instead of sending an entire repository to an LLM, the system retrieves the most relevant code chunks and uses them as context for answer generation.

## Key Features

- **GitHub Repository Import:** Clone a GitHub repository and prepare its source files for indexing.
- **Intelligent Code Chunking:** Split source code into manageable chunks with configurable overlap.
- **Semantic Embeddings:** Generate 384-dimensional embeddings using Sentence Transformers.
- **Vector Search:** Store and retrieve code embeddings using PostgreSQL and pgvector.
- **RAG-Based Question Answering:** Retrieve relevant code snippets and pass them to Gemini for contextual responses.
- **Source Citations:** Include references to relevant code snippets to help users trace answers back to the repository.
- **REST API:** Provide repository management and chat functionality through FastAPI.
- **Modern Web Interface:** Use Next.js and TypeScript for the frontend.
- **Local Embedding Generation:** Generate embeddings locally rather than requiring a hosted embedding API.

## Architecture

```text
                  User
                   |
                   v
          Next.js + TypeScript
                   |
                   v
             FastAPI Backend
                   |
          +--------+---------+
          |                  |
          v                  v
    Repository Import     Chat Question
          |                  |
          v                  v
     Git Clone          Query Embedding
          |                  |
          v                  v
    File Filtering       PostgreSQL +
          |                pgvector
          v                  |
     Code Chunking           v
          |             Top-K Retrieval
          v                  |
   Sentence Transformers     |
          |                  |
          v                  v
    Code Embeddings ----> Retrieved Context
                             |
                             v
                        Gemini LLM
                             |
                             v
                  Answer with Citations
                             |
                             v
                        Web Interface
```

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Backend | Python, FastAPI |
| LLM | Google Gemini API |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimension | 384 |
| Database | PostgreSQL |
| Vector Search | pgvector |
| ORM | SQLAlchemy |
| Repository Management | Git |
| API Communication | REST |

## How It Works

### 1. Repository Import

The user provides a GitHub repository URL. The backend clones the repository and identifies eligible source files while applying configured file-count and file-size limits.

### 2. Code Chunking

Source files are divided into smaller chunks so that relevant portions of code can be retrieved independently. Chunk size and overlap are configurable.

### 3. Embedding Generation

The Sentence Transformers model converts each code chunk into a 384-dimensional vector representing its semantic content.

### 4. Vector Storage

The application stores repository metadata, code chunks, and their embeddings in PostgreSQL. The pgvector extension enables vector similarity operations directly in the database.

### 5. Semantic Retrieval

When a user asks a question, the application embeds the query and performs cosine-distance-based similarity search. It retrieves the most relevant code chunks associated with the selected repository.

### 6. Answer Generation

The retrieved code snippets are supplied to the Gemini model as contextual evidence. The model generates an answer grounded in the retrieved context and includes source references.

## Project Structure

```text
codebase-ai/
├── backend/
│   ├── main.py             # FastAPI application and API endpoints
│   ├── config.py           # Application configuration
│   ├── store.py            # PostgreSQL models and database operations
│   ├── rag.py              # Embeddings, retrieval, and answer generation
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Example environment configuration
│
├── frontend/
│   ├── src/                # Frontend application source
│   ├── public/             # Static assets, if present
│   ├── package.json        # Frontend dependencies and scripts
│   └── ...                 # Other Next.js configuration files
│
├── .gitignore
└── README.md
```

*The exact frontend structure may vary depending on your implementation.*

## Prerequisites

Install the following before running the application:

- Python 3.11 or a compatible version supported by your dependencies
- Node.js and npm
- PostgreSQL
- The PostgreSQL `pgvector` extension
- A Google Gemini API key
- Git

**Docker is not required.**

## Installation and Setup

### 1. Clone the Project

```bash
git clone https://github.com/YOUR_USERNAME/codebase-ai.git
cd codebase-ai
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Configure PostgreSQL

Create a PostgreSQL database for the application, then enable pgvector in that database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Configure your database connection URL in the backend environment file.

### 3. Set Up the Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside `backend/`, using `.env.example` as a template:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=your_supported_gemini_model
```

Replace the placeholders with your local PostgreSQL credentials and a valid Gemini API key. Use a model name supported by your API account.

Start the backend from the `backend/` directory:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API should be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

### 4. Set Up the Frontend

Open another terminal window:

```bash
cd codebase-ai/frontend
npm install
npm run dev -- --port 3001
```

Open the frontend at:

`http://localhost:3001`

Keep both the backend and frontend running while using the application.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check backend health |
| `GET` | `/api/repositories` | List indexed repositories |
| `POST` | `/api/repositories` | Import and index a repository |
| `GET` | `/api/repositories/{repo_id}` | Retrieve repository details |
| `POST` | `/api/repositories/{repo_id}/chat` | Ask a question about a repository |
| `DELETE` | `/api/repositories/{repo_id}` | Delete a repository |

For exact request and response schemas, use the FastAPI documentation at `/docs`.

## Example Use Cases

You can ask questions such as:

- How is authentication implemented in this repository?
- Where is the database connection configured?
- Explain the request flow for a particular API endpoint.
- Which files implement the main business logic?
- How does the frontend communicate with the backend?
- Explain the purpose of a particular function or class.

The quality of an answer depends on the retrieved code context and the underlying language model.

## Configuration

The backend supports configuration for:

| Setting | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Gemini API authentication |
| `GEMINI_MODEL` | Gemini model used for answer generation |
| `EMBEDDING_MODEL` | Sentence Transformers embedding model |
| `DATA_DIR` | Local application data directory |
| `REPO_DIR` | Directory for cloned repositories |
| `MAX_FILES` | Maximum number of files to process |
| `MAX_FILE_BYTES` | Maximum size of an individual file |
| `CHUNK_LINES` | Target number of lines per code chunk |
| `CHUNK_OVERLAP` | Overlap between adjacent chunks |

Default values are defined in the backend configuration. Environment variable names and defaults should match the current implementation.

