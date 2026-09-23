from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JOBS_FILE = DATA_DIR / "jobs_master.csv"


def _split_skills(value):
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text:
        return []

    return [item.strip() for item in text.split(";") if item.strip()]


def load_jobs():
    if not JOBS_FILE.exists():
        raise FileNotFoundError(f"jobs_master.csv not found at: {JOBS_FILE}")

    df = pd.read_csv(JOBS_FILE)

    jobs = []
    for _, row in df.iterrows():
        jobs.append(
            {
                "job_id": row.get("job_id", ""),
                "job_title": row.get("job_title", ""),
                "industry": row.get("industry", ""),
                "company": row.get("company", ""),
                "location_city": row.get("location_city", ""),
                "location_country": row.get("location_country", ""),
                "region": row.get("region", ""),
                "description": row.get("description", ""),
                "required_skills": _split_skills(row.get("required_skills", "")),
                "preferred_skills": _split_skills(row.get("preferred_skills", "")),
                "responsibilities": row.get("responsibilities", ""),
                "experience_level": row.get("experience_level", ""),
                "years_experience_min": row.get("years_experience_min", 0),
                "education_level": row.get("education_level", ""),
                "employment_type": row.get("employment_type", ""),
                "is_internship": str(row.get("is_internship", "")).strip().lower()
                == "true",
                "remote_type": row.get("remote_type", ""),
                "occupation_code": row.get("occupation_code", ""),
                "source_taxonomy": row.get("source_taxonomy", ""),
                "source_url": row.get("source_url", ""),
                "synthetic_record": str(row.get("synthetic_record", "")).strip().lower()
                == "true",
            }
        )

    return jobs
