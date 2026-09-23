from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from backend.db import SessionLocal, init_db
from backend.engine.candidate_store import upsert_candidate


def normalize_text(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)
    return text.strip()


def find_first_existing(row: pd.Series, possible_columns: list[str]) -> str:
    row_dict = {str(k).strip().lower(): v for k, v in row.items()}

    for col in possible_columns:
        value = row_dict.get(col.lower())
        value = normalize_text(value)
        if value:
            return value
    return ""


def build_resume_text(row: pd.Series) -> str:
    # Add or remove field names depending on the CSV you inspected
    sections = []

    name = find_first_existing(row, ["Name", "Full Name", "Candidate Name"])
    title = find_first_existing(row, ["Job Title", "Title", "Role", "Current Role"])
    summary = find_first_existing(
        row, ["Summary", "Professional Summary", "Objective", "Career Objective"]
    )
    skills = find_first_existing(row, ["Skills", "Technical Skills", "Key Skills"])
    experience = find_first_existing(
        row, ["Experience", "Work Experience", "Employment History"]
    )
    education = find_first_existing(
        row, ["Education", "Academic Background", "Qualifications"]
    )
    certifications = find_first_existing(row, ["Certifications", "Certificates"])
    projects = find_first_existing(row, ["Projects", "Project Experience"])
    achievements = find_first_existing(row, ["Achievements", "Awards"])
    raw_resume = find_first_existing(
        row, ["Resume", "Resume Text", "resume_text", "CV", "Text"]
    )

    if name:
        sections.append(f"Name: {name}")
    if title:
        sections.append(f"Title: {title}")
    if summary:
        sections.append(f"Summary: {summary}")
    if skills:
        sections.append(f"Skills: {skills}")
    if experience:
        sections.append(f"Experience: {experience}")
    if education:
        sections.append(f"Education: {education}")
    if certifications:
        sections.append(f"Certifications: {certifications}")
    if projects:
        sections.append(f"Projects: {projects}")
    if achievements:
        sections.append(f"Achievements: {achievements}")
    if raw_resume:
        sections.append(f"Resume Text: {raw_resume}")

    return "\n\n".join([s for s in sections if s.strip()])


def build_summary(row: pd.Series) -> str | None:
    title = find_first_existing(row, ["Job Title", "Title", "Role", "Current Role"])
    summary = find_first_existing(
        row, ["Summary", "Professional Summary", "Objective", "Career Objective"]
    )
    experience = find_first_existing(row, ["Experience", "Work Experience"])

    parts = []
    if title:
        parts.append(title)
    if summary:
        parts.append(summary)
    if experience:
        parts.append(experience[:300])

    text = " | ".join(parts).strip()
    return text or None


def build_email(row: pd.Series, idx: int, full_name: str) -> str:
    email = find_first_existing(row, ["Email", "Email Address", "Mail"])
    if email:
        return email

    slug = "".join(ch.lower() for ch in full_name if ch.isalnum())
    if not slug:
        slug = f"candidate{idx+1}"
    return f"{slug}{idx+1}@example.com"


def build_phone(row: pd.Series) -> str | None:
    phone = find_first_existing(row, ["Phone", "Phone Number", "Mobile", "Contact"])
    return phone or None


def build_name(row: pd.Series, idx: int) -> str:
    name = find_first_existing(row, ["Name", "Full Name", "Candidate Name"])
    return name or f"Candidate {idx+1}"


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "backend/data/resume_dataset.csv"
    file_path = Path(csv_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(file_path)
    print("Detected columns:")
    print(df.columns.tolist())

    init_db()
    db = SessionLocal()
    imported = 0
    skipped = 0

    try:
        for idx, row in df.iterrows():
            full_name = build_name(row, idx)
            email = build_email(row, idx, full_name)
            phone = build_phone(row)
            summary = build_summary(row)
            resume_text = build_resume_text(row)

            if not resume_text.strip():
                skipped += 1
                continue

            upsert_candidate(
                db,
                full_name=full_name,
                email=email,
                phone=phone,
                summary=summary,
                resume_text=resume_text,
                original_filename=None,
            )
            imported += 1

        print(f"Import complete. Imported/updated: {imported}, skipped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
