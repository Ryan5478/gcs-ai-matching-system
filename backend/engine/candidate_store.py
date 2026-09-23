from __future__ import annotations

import re
from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.engine.nlp_processor import extract_skills
from backend.models import Candidate

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embed_model = SentenceTransformer(EMBED_MODEL_NAME)


def clean_text(text: str | None) -> str:
    if text is None:
        return ""

    text = str(text).replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def skills_to_text(skills: list[str]) -> str:
    return ";".join(skills)


def skills_from_text(skills_text: str | None) -> list[str]:
    if not skills_text:
        return []
    return [s.strip() for s in skills_text.split(";") if s.strip()]


def embed_text(text: str) -> list[float]:
    cleaned = clean_text(text)
    vector = embed_model.encode(
        [cleaned],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    return vector.tolist()


def upsert_candidate(
    db: Session,
    *,
    full_name: str,
    email: str,
    phone: str | None,
    summary: str | None,
    resume_text: str,
    original_filename: str | None = None,
) -> Candidate:
    full_name = clean_text(full_name)
    email = clean_text(email)
    phone = clean_text(phone) if phone else None
    summary = clean_text(summary) if summary else None
    resume_text = clean_text(resume_text)
    original_filename = clean_text(original_filename) if original_filename else None

    skills = extract_skills(resume_text)
    embedding = embed_text(resume_text)

    existing = db.execute(
        select(Candidate).where(Candidate.email == email)
    ).scalar_one_or_none()

    if existing:
        existing.full_name = full_name
        existing.phone = phone
        existing.summary = summary
        existing.resume_text = resume_text
        existing.skills_text = skills_to_text(skills)
        existing.original_filename = original_filename
        existing.embedding = embedding
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    candidate = Candidate(
        full_name=full_name,
        email=email,
        phone=phone,
        summary=summary,
        resume_text=resume_text,
        skills_text=skills_to_text(skills),
        original_filename=original_filename,
        embedding=embedding,
        is_active=True,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_candidate_count(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(Candidate)) or 0)


def list_candidates(db: Session, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            select(Candidate)
            .where(Candidate.is_active.is_(True))
            .order_by(Candidate.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    results = []
    for candidate in rows:
        results.append(
            {
                "id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "summary": candidate.summary,
                "skills": skills_from_text(candidate.skills_text),
                "original_filename": candidate.original_filename,
            }
        )
    return results


def search_best_candidates(
    db: Session,
    *,
    job_description: str,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    query_embedding = embed_text(job_description)

    stmt = (
        select(
            Candidate,
            Candidate.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(Candidate.is_active.is_(True))
        .order_by(Candidate.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    results = []
    for candidate, distance in rows:
        distance = float(distance)
        score = max(0.0, min(1.0, 1.0 - distance))

        results.append(
            {
                "id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "summary": candidate.summary,
                "skills": skills_from_text(candidate.skills_text),
                "distance": round(distance, 4),
                "score": round(score, 4),
                "resume_text_internal": candidate.resume_text,
            }
        )

    return results
