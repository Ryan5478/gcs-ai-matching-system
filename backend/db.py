from __future__ import annotations

import os
from typing import Generator

import psycopg
from pgvector.psycopg import register_vector
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:5478@localhost:5432/jobmatch",
)

# psycopg (raw driver) needs the URL without the SQLAlchemy dialect prefix
RAW_DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

class Base(DeclarativeBase):
    pass


def ensure_vector_extension() -> None:
    with psycopg.connect(RAW_DATABASE_URL, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")


engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    try:
        register_vector(dbapi_connection)
    except Exception:
        # Allows startup in environments where pgvector is not ready yet
        pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    ensure_vector_extension()

    from backend.models import Candidate, User  # noqa: F401

    Base.metadata.create_all(bind=engine)
