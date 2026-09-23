from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

from backend.engine.bert_siamese import SiameseSimilarityService
from backend.engine.nlp_processor import clean_text

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

TEXT_COLUMNS = ["Resume", "resume", "resume_text", "text", "content"]
LABEL_COLUMNS = ["Category", "category", "job_category", "domain", "label"]


@dataclass
class TrainArtifacts:
    csv_path: str
    pairs_generated: int
    train_accuracy: float
    model_dir: str


class PairDataset(Dataset):
    def __init__(self, emb_a: np.ndarray, emb_b: np.ndarray, labels: np.ndarray):
        self.emb_a = torch.tensor(emb_a, dtype=torch.float32)
        self.emb_b = torch.tensor(emb_b, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32).view(-1, 1)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        return self.emb_a[idx], self.emb_b[idx], self.labels[idx]


def detect_columns(df: pd.DataFrame) -> Tuple[str, str]:
    text_col = next((c for c in TEXT_COLUMNS if c in df.columns), None)
    label_col = next((c for c in LABEL_COLUMNS if c in df.columns), None)
    if text_col is None or label_col is None:
        raise ValueError(
            f"Could not detect required columns. Expected text in {TEXT_COLUMNS} and label in {LABEL_COLUMNS}. Found: {list(df.columns)}"
        )
    return text_col, label_col


def load_resume_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    text_col, label_col = detect_columns(df)
    df = df[[text_col, label_col]].dropna().copy()
    df.columns = ["text", "label"]
    df["text"] = df["text"].astype(str).map(clean_text)
    df["label"] = df["label"].astype(str).str.strip()
    df = df[df["text"].str.len() > 20]
    df = df[df["label"].str.len() > 0]
    return df.reset_index(drop=True)


def build_pairs(
    df: pd.DataFrame, max_pairs_per_class: int = 40
) -> List[Tuple[str, str, int]]:
    pairs: List[Tuple[str, str, int]] = []
    grouped: Dict[str, List[str]] = df.groupby("label")["text"].apply(list).to_dict()
    labels = list(grouped.keys())

    for label, texts in grouped.items():
        texts = list(dict.fromkeys(texts))
        if len(texts) < 2:
            continue

        pos_count = 0
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                pairs.append((texts[i], texts[j], 1))
                pos_count += 1
                if pos_count >= max_pairs_per_class:
                    break
            if pos_count >= max_pairs_per_class:
                break

        other_labels = [l for l in labels if l != label and grouped[l]]
        neg_count = 0
        for text in texts[:max_pairs_per_class]:
            sampled_labels = (
                random.sample(other_labels, k=min(len(other_labels), 3))
                if other_labels
                else []
            )
            for other_label in sampled_labels:
                other_text = random.choice(grouped[other_label])
                pairs.append((text, other_text, 0))
                neg_count += 1
                if neg_count >= max_pairs_per_class:
                    break
            if neg_count >= max_pairs_per_class:
                break

    random.shuffle(pairs)
    return pairs


def prepare_embeddings(
    service: SiameseSimilarityService, pairs: Sequence[Tuple[str, str, int]]
):
    unique_texts = list({text for pair in pairs for text in pair[:2]})
    text_to_emb = {
        text: emb for text, emb in zip(unique_texts, service.embed_texts(unique_texts))
    }
    emb_a = np.array([text_to_emb[a] for a, _, _ in pairs], dtype=np.float32)
    emb_b = np.array([text_to_emb[b] for _, b, _ in pairs], dtype=np.float32)
    labels = np.array([label for _, _, label in pairs], dtype=np.float32)
    return emb_a, emb_b, labels


def train_siamese(
    csv_path: str,
    model_dir: str = "backend/models",
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 1e-3,
    max_pairs_per_class: int = 40,
) -> TrainArtifacts:
    service = SiameseSimilarityService(model_dir=model_dir)
    df = load_resume_dataset(csv_path)
    pairs = build_pairs(df, max_pairs_per_class=max_pairs_per_class)
    if len(pairs) < 10:
        raise ValueError(
            "Not enough training pairs could be generated from Resume.csv. Add more labeled resumes."
        )

    emb_a, emb_b, labels = prepare_embeddings(service, pairs)
    X_train_a, X_val_a, X_train_b, X_val_b, y_train, y_val = train_test_split(
        emb_a, emb_b, labels, test_size=0.2, random_state=RANDOM_SEED, stratify=labels
    )

    train_loader = DataLoader(
        PairDataset(X_train_a, X_train_b, y_train), batch_size=batch_size, shuffle=True
    )
    val_loader = DataLoader(PairDataset(X_val_a, X_val_b, y_val), batch_size=batch_size)

    optimizer = torch.optim.Adam(service.head.parameters(), lr=learning_rate)
    criterion = nn.BCELoss()

    device = service.device
    for _ in range(epochs):
        service.head.train()
        for batch_a, batch_b, batch_y in train_loader:
            batch_a = batch_a.to(device)
            batch_b = batch_b.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            preds = service.head(batch_a, batch_b)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()

    service.head.eval()
    preds_all = []
    labels_all = []
    with torch.no_grad():
        for batch_a, batch_b, batch_y in val_loader:
            batch_a = batch_a.to(device)
            batch_b = batch_b.to(device)
            pred = service.head(batch_a, batch_b).squeeze(1).detach().cpu().numpy()
            preds_all.extend((pred >= 0.5).astype(int).tolist())
            labels_all.extend(batch_y.squeeze(1).numpy().astype(int).tolist())

    accuracy = accuracy_score(labels_all, preds_all)
    metadata = {
        "trained": True,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "pairs_generated": len(pairs),
        "train_accuracy": round(float(accuracy), 4),
        "csv_path": csv_path,
    }
    service.metadata = metadata
    service.save(metadata=metadata)

    return TrainArtifacts(
        csv_path=csv_path,
        pairs_generated=len(pairs),
        train_accuracy=float(accuracy),
        model_dir=model_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train the Siamese resume matching model"
    )
    parser.add_argument("--csv", dest="csv_path", default="backend/data/Resume.csv")
    parser.add_argument("--model-dir", dest="model_dir", default="backend/models")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--max-pairs-per-class", type=int, default=40)
    args = parser.parse_args()

    result = train_siamese(
        csv_path=args.csv_path,
        model_dir=args.model_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_pairs_per_class=args.max_pairs_per_class,
    )
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
