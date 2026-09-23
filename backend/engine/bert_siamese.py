from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer


@dataclass
class ModelConfig:
    embed_model_name: str = os.getenv(
        "DEFAULT_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_dim: int = 384


class SiameseHead(nn.Module):
    def __init__(self, embedding_dim: int = 384):
        super().__init__()
        feature_dim = embedding_dim * 4
        self.network = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
        )

    def forward(self, emb_a: torch.Tensor, emb_b: torch.Tensor) -> torch.Tensor:
        features = torch.cat(
            [emb_a, emb_b, torch.abs(emb_a - emb_b), emb_a * emb_b], dim=1
        )
        logits = self.network(features)
        return torch.sigmoid(logits)


class SiameseSimilarityService:
    def __init__(self, model_dir: str | os.PathLike = "backend/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.config = ModelConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.embedder = SentenceTransformer(
            self.config.embed_model_name, device=str(self.device)
        )
        self.head = SiameseHead(self.config.embedding_dim).to(self.device)
        self.metadata = {"trained": False}
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        weights_path = self.model_dir / "siamese_head.pt"
        metadata_path = self.model_dir / "metadata.json"
        if weights_path.exists():
            state = torch.load(weights_path, map_location=self.device)
            self.head.load_state_dict(state)
        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def save(self, metadata: dict | None = None) -> None:
        torch.save(self.head.state_dict(), self.model_dir / "siamese_head.pt")
        payload = metadata or self.metadata
        with (self.model_dir / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def embed_texts(self, texts: Sequence[str], normalize: bool = True) -> np.ndarray:
        embeddings = self.embedder.encode(
            list(texts), normalize_embeddings=normalize, show_progress_bar=False
        )
        return np.asarray(embeddings, dtype=np.float32)

    def embed_text(self, text: str, normalize: bool = True) -> np.ndarray:
        return self.embed_texts([text], normalize=normalize)[0]

    def _to_tensor(self, array_like: np.ndarray | Sequence[float]) -> torch.Tensor:
        arr = np.asarray(array_like, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr[None, :]
        return torch.tensor(arr, dtype=torch.float32, device=self.device)

    @torch.no_grad()
    def predict_similarity_from_embeddings(
        self, emb_a: np.ndarray | Sequence[float], emb_b: np.ndarray | Sequence[float]
    ) -> float:
        self.head.eval()
        ta = self._to_tensor(emb_a)
        tb = self._to_tensor(emb_b)
        score = self.head(ta, tb).squeeze().item()
        return float(score)

    @torch.no_grad()
    def predict_similarity(self, text_a: str, text_b: str) -> float:
        emb_a = self.embed_text(text_a)
        emb_b = self.embed_text(text_b)
        return self.predict_similarity_from_embeddings(emb_a, emb_b)

    def batch_predict_similarity(
        self, anchor_embedding: np.ndarray, candidate_embeddings: np.ndarray
    ) -> List[float]:
        self.head.eval()
        anchor = np.repeat(anchor_embedding[None, :], len(candidate_embeddings), axis=0)
        ta = self._to_tensor(anchor)
        tb = self._to_tensor(candidate_embeddings)
        with torch.no_grad():
            preds = self.head(ta, tb).squeeze(1).detach().cpu().numpy()
        return preds.astype(float).tolist()
