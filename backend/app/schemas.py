from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class RepositoryCreate(BaseModel):
    url: HttpUrl
    branch: Optional[str] = "main"

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)

class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
