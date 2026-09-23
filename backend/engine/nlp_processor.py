import re
import pandas as pd
from pathlib import Path

SKILLS_FILE = Path(__file__).resolve().parent.parent / "data" / "skills_master.csv"


def load_skills():
    if SKILLS_FILE.exists():
        df = pd.read_csv(SKILLS_FILE)
        return sorted(
            set(str(x).strip().lower() for x in df["skill"].dropna().tolist())
        )
    return []


MASTER_SKILLS = load_skills()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-\+/\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_skills(text: str):
    text = normalize_text(text)
    found = []

    for skill in MASTER_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found.append(skill.title())

    return sorted(set(found))
