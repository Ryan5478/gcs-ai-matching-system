from __future__ import annotations

import os
from typing import Callable, Dict, List, Any

import numpy as np
from sentence_transformers import CrossEncoder


class PairReranker:
    def __init__(self) -> None:
        model_name = os.getenv(
            "CROSS_ENCODER_MODEL",
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
        )
        self.model = CrossEncoder(model_name)

    @staticmethod
    def _normalize_scores(scores: List[float]) -> List[float]:
        if not scores:
            return []

        arr = np.asarray(scores, dtype=np.float32)
        min_val = float(arr.min())
        max_val = float(arr.max())

        if abs(max_val - min_val) < 1e-8:
            return [0.5 for _ in scores]

        norm = (arr - min_val) / (max_val - min_val)
        return norm.astype(float).tolist()

    def rerank_items(
        self,
        query_text: str,
        items: List[Dict[str, Any]],
        pair_builder: Callable[[Dict[str, Any]], str],
        *,
        base_score_key: str = "score",
        rerank_weight: float = 0.35,
        top_k: int | None = None,
    ) -> List[Dict[str, Any]]:
        if not items:
            return []

        pairs = [(query_text, pair_builder(item)) for item in items]
        raw_scores = self.model.predict(pairs, show_progress_bar=False)

        if hasattr(raw_scores, "tolist"):
            raw_scores = raw_scores.tolist()

        raw_scores = [float(x) for x in raw_scores]
        reranker_scores = self._normalize_scores(raw_scores)

        reranked: List[Dict[str, Any]] = []

        for item, reranker_score in zip(items, reranker_scores):
            base_score = float(item.get(base_score_key, 0.0))
            final_score = ((1.0 - rerank_weight) * base_score) + (
                rerank_weight * reranker_score
            )
            final_score = max(0.0, min(final_score, 1.0))

            new_item = dict(item)
            new_item["base_score"] = round(base_score, 4)
            new_item["reranker_score"] = round(reranker_score, 4)
            new_item["score"] = round(final_score, 4)
            reranked.append(new_item)

        reranked.sort(key=lambda x: x["score"], reverse=True)

        if top_k is not None:
            return reranked[:top_k]
        return reranked


_reranker_instance: PairReranker | None = None


def get_reranker() -> PairReranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = PairReranker()
    return _reranker_instance


def rerank_jobs_for_resume(
    resume_text: str,
    jobs: List[Dict[str, Any]],
    *,
    top_k: int = 15,
) -> List[Dict[str, Any]]:
    reranker = get_reranker()

    def build_job_text(job: Dict[str, Any]) -> str:
        title = str(job.get("job_title", "")).strip()
        company = str(job.get("company", "")).strip()
        industry = str(job.get("industry", "")).strip()
        description = str(job.get("description", "")).strip()
        skills = ", ".join(job.get("required_skills", []) or [])
        return (
            f"Job Title: {title}\n"
            f"Company: {company}\n"
            f"Industry: {industry}\n"
            f"Description: {description}\n"
            f"Required Skills: {skills}"
        )

    return reranker.rerank_items(
        query_text=resume_text,
        items=jobs,
        pair_builder=build_job_text,
        base_score_key="score",
        rerank_weight=0.35,
        top_k=top_k,
    )


def rerank_candidates_for_job(
    job_description: str,
    candidates: List[Dict[str, Any]],
    *,
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    reranker = get_reranker()

    def build_candidate_text(candidate: Dict[str, Any]) -> str:
        resume_text = candidate.get("resume_text_internal", "") or ""
        summary = candidate.get("summary", "") or ""
        skills = ", ".join(candidate.get("skills", []) or [])
        return f"Summary: {summary}\n" f"Skills: {skills}\n" f"Resume: {resume_text}"

    return reranker.rerank_items(
        query_text=job_description,
        items=candidates,
        pair_builder=build_candidate_text,
        base_score_key="score",
        rerank_weight=0.35,
        top_k=top_k,
    )
