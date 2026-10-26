
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Integer,
    Text,
    create_engine,
    select,
    delete,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector

from .config import settings


if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Configure it in backend/.env."
    )

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    branch: Mapped[str] = mapped_column(String, nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    file_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repo_id: Mapped[str] = mapped_column(
        String, index=True, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(384), nullable=False
    )


def init_db():
    Base.metadata.create_all(bind=engine)


def save_repository(repo: dict):
    with SessionLocal() as db:
        statement = insert(Repository).values(**repo)
        statement = statement.on_conflict_do_update(
            index_elements=[Repository.id],
            set_={
                key: getattr(statement.excluded, key)
                for key in repo
                if key != "id"
            },
        )
        db.execute(statement)
        db.commit()


def list_repositories():
    with SessionLocal() as db:
        rows = db.scalars(
            select(Repository).order_by(Repository.created_at.desc())
        ).all()
        return [repository_to_dict(row) for row in rows]


def get_repository(repo_id: str):
    with SessionLocal() as db:
        row = db.get(Repository, repo_id)
        return repository_to_dict(row) if row else None


def delete_repository(repo_id: str):
    with SessionLocal() as db:
        db.execute(
            delete(CodeChunk).where(CodeChunk.repo_id == repo_id)
        )
        db.execute(
            delete(Repository).where(Repository.id == repo_id)
        )
        db.commit()


def repository_to_dict(row: Repository) -> dict:
    return {
        "id": row.id,
        "owner": row.owner,
        "name": row.name,
        "url": row.url,
        "branch": row.branch,
        "commit_sha": row.commit_sha,
        "status": row.status,
        "file_count": row.file_count,
        "created_at": row.created_at,
    }


def utc_now():
    return datetime.now(timezone.utc).isoformat()
