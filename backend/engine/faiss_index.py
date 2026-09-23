from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class JobFaissIndex:
    """
    FAISS-backed vector index for job retrieval.

    - Uses normalized embeddings + IndexFlatIP so inner product behaves like cosine similarity.
    - Saves/loads the index from disk.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_dir: str | Path = "backend/models/faiss",
    ) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.index_dir / "jobs.faiss"
        self.meta_path = self.index_dir / "jobs.meta.json"

        self.index: faiss.Index | None = None
        self.dimension: int | None = None
        self.jobs_count: int = 0

    def _job_to_text(self, job: Dict[str, Any]) -> str:
        title = str(job.get("job_title", "")).strip()
        industry = str(job.get("industry", "")).strip()
        description = str(job.get("description", "")).strip()
        skills = job.get("required_skills", []) or []

        if isinstance(skills, list):
            skills_text = ", ".join(str(s).strip() for s in skills if str(s).strip())
        else:
            skills_text = str(skills)

        parts = [
            title,
            industry,
            description,
            f"Required skills: {skills_text}" if skills_text else "",
        ]
        return ". ".join(p for p in parts if p)

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def build(self, jobs_db: List[Dict[str, Any]], save: bool = True) -> None:
        if not jobs_db:
            raise ValueError("Cannot build FAISS index: jobs_db is empty.")

        texts = [self._job_to_text(job) for job in jobs_db]
        embeddings = self._encode_texts(texts)

        self.dimension = int(embeddings.shape[1])
        self.jobs_count = len(jobs_db)

        index = faiss.IndexFlatIP(self.dimension)
        index.add(embeddings)

        self.index = index

        if save:
            self.save()

    def save(self) -> None:
        if self.index is None or self.dimension is None:
            raise RuntimeError("Cannot save FAISS index before build/load.")

        faiss.write_index(self.index, str(self.index_path))

        metadata = {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "jobs_count": self.jobs_count,
        }
        with self.meta_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load(self) -> bool:
        if not self.index_path.exists() or not self.meta_path.exists():
            return False

        self.index = faiss.read_index(str(self.index_path))

        with self.meta_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.dimension = int(metadata["dimension"])
        self.jobs_count = int(metadata["jobs_count"])
        return True

    def load_or_build(self, jobs_db: List[Dict[str, Any]]) -> None:
        loaded = self.load()
        if not loaded:
            self.build(jobs_db, save=True)
            return

        # Rebuild if the stored index is out of sync with the current jobs catalog
        if self.jobs_count != len(jobs_db):
            self.build(jobs_db, save=True)

    def is_ready(self) -> bool:
        return self.index is not None

    def search(self, query_text: str, top_k: int = 20) -> Tuple[List[float], List[int]]:
        if self.index is None:
            raise RuntimeError("FAISS index is not ready.")

        if not query_text.strip():
            return [], []

        k = min(max(top_k, 1), self.jobs_count)

        query_embedding = self._encode_texts([query_text])
        scores, indices = self.index.search(query_embedding, k)

        score_list = [float(x) for x in scores[0].tolist() if x is not None]
        index_list = [int(x) for x in indices[0].tolist() if int(x) != -1]
        return score_list, index_list
