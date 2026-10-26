
from contextlib import asynccontextmanager
from pathlib import Path
import shutil
import subprocess
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import RepositoryCreate, ChatRequest, ChatResponse, Citation
from .store import (
    init_db,
    save_repository,
    list_repositories,
    get_repository,
    delete_repository,
    utc_now,
)
from .repo_ingest import safe_clone, iter_source_files, chunk_text
from .rag import (
    index_chunks,
    retrieve,
    generate_answer,
    delete_repository_chunks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CodeBase AI API",
    description="RAG-powered assistant for public GitHub repositories.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/repositories")
def repositories():
    return list_repositories()


@app.post("/api/repositories")
def add_repository(payload: RepositoryCreate):
    repo_id = str(uuid.uuid4())
    local_path = None

    try:
        requested_branch = (
            None
            if not payload.branch or payload.branch.strip() == "main"
            else payload.branch.strip()
        )

        local_path, owner, name, sha = safe_clone(
            str(payload.url),
            requested_branch,
            repo_id,
        )

        actual_branch = subprocess.run(
            [
                "git",
                "-C",
                str(local_path),
                "branch",
                "--show-current",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

        chunks = []
        file_count = 0

        for file_path, content in iter_source_files(local_path):
            file_count += 1
            chunks.extend(chunk_text(file_path, content))

        if not chunks:
            raise ValueError(
                "No supported source files were found in this repository."
            )

        indexed = index_chunks(repo_id, chunks)

        record = {
            "id": repo_id,
            "owner": owner,
            "name": name,
            "url": f"https://github.com/{owner}/{name}",
            "branch": actual_branch or requested_branch or "default",
            "commit_sha": sha,
            "status": "ready",
            "file_count": file_count,
            "created_at": utc_now(),
        }

        save_repository(record)

        return {
            **record,
            "chunk_count": indexed,
        }

    except ValueError as e:
        try:
            delete_repository_chunks(repo_id)
        except Exception:
            pass

        if local_path:
            shutil.rmtree(local_path, ignore_errors=True)

        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        try:
            delete_repository_chunks(repo_id)
        except Exception:
            pass

        if local_path:
            shutil.rmtree(local_path, ignore_errors=True)

        raise HTTPException(
            status_code=500,
            detail=f"Repository indexing failed: {type(e).__name__}: {e}",
        ) from e


@app.get("/api/repositories/{repo_id}")
def repository_detail(repo_id: str):
    repo = get_repository(repo_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repo


@app.post(
    "/api/repositories/{repo_id}/chat",
    response_model=ChatResponse,
)
def chat(repo_id: str, payload: ChatRequest):
    repo = get_repository(repo_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    chunks = retrieve(
        repo_id,
        payload.question,
        limit=8,
    )

    answer = generate_answer(
        payload.question,
        chunks,
    )

    citations = [
        Citation(
            file_path=chunk["file_path"],
            start_line=chunk["start_line"],
            end_line=chunk["end_line"],
            content=chunk["content"],
            score=chunk["score"],
        )
        for chunk in chunks
    ]

    return ChatResponse(
        answer=answer,
        citations=citations,
    )


@app.delete("/api/repositories/{repo_id}")
def remove_repository(repo_id: str):
    repo = get_repository(repo_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    try:
        delete_repository_chunks(repo_id)
        delete_repository(repo_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Repository deletion failed: {type(e).__name__}: {e}",
        ) from e

    shutil.rmtree(
        Path(settings.repo_dir) / repo_id,
        ignore_errors=True,
    )

    return {
        "deleted": True,
        "repository_id": repo_id,
    }
