from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from backend.db import SessionLocal, init_db
from backend.engine.candidate_store import upsert_candidate

DEFAULT_CSV_PATH = "backend/data/candidates.csv"


def pick_resume_text(row: pd.Series) -> str:
    for col in ["resume_text", "Resume", "resume", "text", "cv_text"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return ""


def pick_name(row: pd.Series, idx: int) -> str:
    for col in ["full_name", "name", "candidate_name"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return f"Candidate {idx + 1}"


def pick_email(row: pd.Series, idx: int) -> str:
    for col in ["email", "Email"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return f"candidate{idx + 1}@example.com"


def pick_phone(row: pd.Series) -> str | None:
    for col in ["phone", "Phone", "mobile"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return None


def pick_summary(row: pd.Series) -> str | None:
    for col in ["summary", "Summary", "profile"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return None


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    file_path = Path(csv_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    init_db()
    df = pd.read_csv(file_path)

    db = SessionLocal()
    imported = 0

    try:
        for idx, row in df.iterrows():
            resume_text = pick_resume_text(row)
            if not resume_text:
                continue

            upsert_candidate(
                db,
                full_name=pick_name(row, idx),
                email=pick_email(row, idx),
                phone=pick_phone(row),
                summary=pick_summary(row),
                resume_text=resume_text,
                original_filename=None,
            )
            imported += 1

        print(f"Candidate import complete. Imported/updated: {imported}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
