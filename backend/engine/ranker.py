from __future__ import annotations

from typing import Any, Dict, List, Sequence

from sentence_transformers import SentenceTransformer, util

try:
    from backend.engine.bert_siamese import SiameseSimilarityService

    _siamese_service = SiameseSimilarityService()
except Exception:
    _siamese_service = None


_embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def siamese_ready() -> bool:
    if _siamese_service is None:
        return False

    metadata = getattr(_siamese_service, "metadata", {}) or {}
    return bool(metadata.get("trained", False))


def jaccard_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    set_a = {str(x).strip().lower() for x in a if str(x).strip()}
    set_b = {str(x).strip().lower() for x in b if str(x).strip()}

    if not set_a and not set_b:
        return 0.0

    return len(set_a & set_b) / max(len(set_a | set_b), 1)


def normalize_cosine_score(score: float) -> float:
    # cosine similarity [-1, 1] -> [0, 1]
    normalized = (float(score) + 1.0) / 2.0
    return max(0.0, min(normalized, 1.0))


def matching_skills(
    resume_skills: Sequence[str], job_skills: Sequence[str]
) -> List[str]:
    resume_set = {str(x).strip().lower() for x in resume_skills if str(x).strip()}
    job_set = {str(x).strip().lower() for x in job_skills if str(x).strip()}
    return [skill.title() for skill in sorted(resume_set & job_set)]


def rank_jobs_from_candidates(
    resume_text: str,
    resume_skills: List[str],
    candidate_jobs: List[Dict[str, Any]],
    semantic_scores: List[float],
    top_k: int = 15,
    use_siamese: bool = False,
) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []

    siamese_scores = None
    if use_siamese and siamese_ready():
        job_texts = [
            f"{job.get('job_title', '')}. {job.get('description', '')}"
            for job in candidate_jobs
        ]
        resume_emb_np = _siamese_service.embed_text(resume_text)
        job_emb_np = _siamese_service.embed_texts(job_texts)
        siamese_scores = _siamese_service.batch_predict_similarity(
            resume_emb_np,
            job_emb_np,
        )

    for idx, job in enumerate(candidate_jobs):
        raw_semantic = (
            float(semantic_scores[idx]) if idx < len(semantic_scores) else 0.0
        )
        semantic_score = normalize_cosine_score(raw_semantic)

        job_skills = job.get("required_skills", []) or []
        matched = matching_skills(resume_skills, job_skills)
        skill_score = jaccard_similarity(resume_skills, job_skills)
        internship_bonus = 0.05 if job.get("is_internship", False) else 0.0

        if siamese_scores is not None:
            siamese_score = max(0.0, min(float(siamese_scores[idx]), 1.0))
            final_score = (
                0.50 * semantic_score
                + 0.25 * skill_score
                + 0.20 * siamese_score
                + internship_bonus
            )
        else:
            siamese_score = None
            final_score = 0.75 * semantic_score + 0.20 * skill_score + internship_bonus

        final_score = max(0.0, min(final_score, 1.0))

        ranked.append(
            {
                "job_id": job.get("job_id"),
                "job_title": job.get("job_title"),
                "industry": job.get("industry"),
                "company": job.get("company"),
                "description": job.get("description"),
                "required_skills": job_skills,
                "matching_skills": matched,
                "is_internship": job.get("is_internship", False),
                "semantic_score": round(semantic_score, 4),
                "skill_score": round(skill_score, 4),
                "siamese_score": (
                    round(siamese_score, 4) if siamese_score is not None else None
                ),
                "score": round(final_score, 4),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]


def rank_jobs_for_resume(
    resume_text: str,
    resume_skills: List[str],
    jobs_db: List[Dict[str, Any]],
    top_k: int = 20,
    use_siamese: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fallback full-scan ranking when FAISS is not used.
    """
    if not jobs_db:
        return []

    resume_emb = _embedding_model.encode(resume_text, convert_to_tensor=True)

    job_texts = [
        f"{job.get('job_title', '')}. {job.get('description', '')}" for job in jobs_db
    ]
    job_embeddings = _embedding_model.encode(job_texts, convert_to_tensor=True)

    cosine_scores_tensor = util.cos_sim(resume_emb, job_embeddings)[0]
    cosine_scores = [float(x) for x in cosine_scores_tensor.tolist()]

    return rank_jobs_from_candidates(
        resume_text=resume_text,
        resume_skills=resume_skills,
        candidate_jobs=jobs_db,
        semantic_scores=cosine_scores,
        top_k=top_k,
        use_siamese=use_siamese,
    )


def rank_candidates_for_job(
    job_description: str,
    candidates_db: List[Dict[str, Any]],
    top_k: int = 20,
    use_siamese: bool = False,
) -> List[Dict[str, Any]]:
    if not candidates_db:
        return []

    candidate_texts = [
        str(candidate.get("resume_text", "")).strip() for candidate in candidates_db
    ]
    job_emb = _embedding_model.encode(job_description, convert_to_tensor=True)
    candidate_embs = _embedding_model.encode(candidate_texts, convert_to_tensor=True)

    cosine_scores_tensor = util.cos_sim(job_emb, candidate_embs)[0]
    cosine_scores = [
        normalize_cosine_score(float(x)) for x in cosine_scores_tensor.tolist()
    ]

    siamese_scores = None
    if use_siamese and siamese_ready():
        job_emb_np = _siamese_service.embed_text(job_description)
        candidate_embs_np = _siamese_service.embed_texts(candidate_texts)
        siamese_scores = _siamese_service.batch_predict_similarity(
            job_emb_np, candidate_embs_np
        )

    ranked: List[Dict[str, Any]] = []

    for idx, candidate in enumerate(candidates_db):
        semantic_score = cosine_scores[idx]

        if siamese_scores is not None:
            siamese_score = max(0.0, min(float(siamese_scores[idx]), 1.0))
            final_score = 0.75 * semantic_score + 0.25 * siamese_score
        else:
            siamese_score = None
            final_score = semantic_score

        final_score = max(0.0, min(final_score, 1.0))

        ranked.append(
            {
                "name": candidate.get("name"),
                "email": candidate.get("email"),
                "summary": candidate.get("summary", ""),
                "skills": candidate.get("skills", []),
                "semantic_score": round(semantic_score, 4),
                "siamese_score": (
                    round(siamese_score, 4) if siamese_score is not None else None
                ),
                "score": round(final_score, 4),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]
