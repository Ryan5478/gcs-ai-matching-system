from __future__ import annotations
from backend.engine.job_discovery import discover_jobs
import json
from backend.engine.groq_client import chat
from backend.schemas_ai import (
    FitScoreRequest,
    FitScoreResponse,
    AtsStrengthRequest,
    AtsStrengthResponse,
    CoverLetterRequest,
    CoverLetterResponse,
    JobDiscoveryRequest,
    JobDiscoveryResponse,
    DiscoveredJob,
)
import csv
import io
from dotenv import load_dotenv

load_dotenv()
from typing import Dict, List

from docx import Document
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from backend.auth import create_access_token, get_current_user_payload, require_roles
from backend.db import get_db, init_db
from backend.engine.ai_advisor import (
    build_candidate_advice,
    build_candidate_job_summary,
    build_employer_candidate_summary,
    build_job_advice,
)
from backend.engine.ai_employer_advisor import (
    build_employer_candidate_review,
    build_employer_hiring_summary,
)
from backend.engine.ai_resume_advisor import build_resume_advice
from backend.engine.candidate_store import (
    get_candidate_count,
    list_candidates,
    search_best_candidates,
    upsert_candidate,
)
from backend.engine.data_loader import load_jobs
from backend.engine.faiss_index import JobFaissIndex
from backend.engine.nlp_processor import extract_skills
from backend.engine.ranker import rank_jobs_from_candidates, siamese_ready
from backend.engine.reranker_service import (
    rerank_candidates_for_job,
    rerank_jobs_for_resume,
)
from backend.engine.user_store import authenticate_user, create_user
from backend.schemas_auth import RegisterRequest, TokenResponse
from backend.schemas_db import CandidateCreate, JobRequest

USE_SIAMESE = False
FAISS_SHORTLIST_K = 50
RECOMMENDATION_TOP_K = 15
EMPLOYER_SHORTLIST_K = 50
EMPLOYER_TOP_K = 20

app = FastAPI(title="Global Job Recommendation API")

import os

_origins_env = os.environ.get("CORS_ORIGINS", "").strip()
ALLOWED_ORIGINS = (
    [o.strip() for o in _origins_env.split(",") if o.strip()]
    if _origins_env
    else ["*"]  # local dev default
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DB: List[Dict] = []
JOB_INDEX: JobFaissIndex | None = None

FAIRNESS_LOGS: List[Dict] = [
    {
        "group": "female",
        "selected": 42,
        "total": 100,
        "true_positive": 30,
        "actual_positive": 60,
    },
    {
        "group": "male",
        "selected": 55,
        "total": 100,
        "true_positive": 40,
        "actual_positive": 62,
    },
    {
        "group": "non_binary",
        "selected": 18,
        "total": 40,
        "true_positive": 11,
        "actual_positive": 20,
    },
]


def initialize_system() -> None:
    global JOBS_DB, JOB_INDEX
    JOBS_DB = load_jobs()
    JOB_INDEX = JobFaissIndex()
    JOB_INDEX.load_or_build(JOBS_DB)


def safe_div(a: float, b: float) -> float:
    return round(a / b, 4) if b else 0.0


def compute_fairness_metrics() -> Dict:
    group_metrics = []

    for row in FAIRNESS_LOGS:
        selection_rate = safe_div(row["selected"], row["total"])
        true_positive_rate = safe_div(row["true_positive"], row["actual_positive"])

        group_metrics.append(
            {
                "group": row["group"],
                "selected": row["selected"],
                "total": row["total"],
                "actual_positive": row["actual_positive"],
                "selection_rate": selection_rate,
                "true_positive_rate": true_positive_rate,
            }
        )

    selection_rates = [g["selection_rate"] for g in group_metrics]
    tprs = [g["true_positive_rate"] for g in group_metrics]

    demographic_parity_difference = (
        round(max(selection_rates) - min(selection_rates), 4)
        if selection_rates
        else 0.0
    )
    equal_opportunity_difference = round(max(tprs) - min(tprs), 4) if tprs else 0.0

    fairness_alert = (
        demographic_parity_difference > 0.1 or equal_opportunity_difference > 0.1
    )

    return {
        "group_metrics": group_metrics,
        "summary": {
            "demographic_parity_difference": demographic_parity_difference,
            "equal_opportunity_difference": equal_opportunity_difference,
            "fairness_alert": fairness_alert,
            "threshold": 0.1,
        },
    }


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    initialize_system()


def sanitize_resume_text(text: str | None) -> str:
    if not text:
        return ""

    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)

    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return sanitize_resume_text(extract_text_from_pdf(file_bytes))
    if filename.endswith(".docx"):
        return sanitize_resume_text(extract_text_from_docx(file_bytes))
    if filename.endswith(".txt"):
        return sanitize_resume_text(file_bytes.decode("utf-8", errors="ignore"))

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Use PDF, DOCX, or TXT.",
    )


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(
            db,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    token = create_access_token(
        {
            "sub": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
    }


@app.post("/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        {
            "sub": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
    }


@app.get("/auth/me")
def auth_me(current_user: dict = Depends(get_current_user_payload)):
    return current_user


@app.get("/")
def root():
    return {
        "message": "Global Job Recommendation API is running",
        "jobs_loaded": len(JOBS_DB),
        "faiss_ready": JOB_INDEX is not None and JOB_INDEX.is_ready(),
        "siamese_requested": USE_SIAMESE,
        "siamese_ready": siamese_ready(),
    }


@app.get("/health")
def health(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    return {
        "status": "ok",
        "jobs_loaded": len(JOBS_DB),
        "candidates_loaded": get_candidate_count(db),
        "faiss_ready": JOB_INDEX is not None and JOB_INDEX.is_ready(),
        "siamese_requested": USE_SIAMESE,
        "siamese_ready": siamese_ready(),
    }


@app.get("/admin/status")
def admin_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    fairness = compute_fairness_metrics()

    return {
        "system_status": "online",
        "jobs_loaded": len(JOBS_DB),
        "candidates_loaded": get_candidate_count(db),
        "faiss_ready": JOB_INDEX is not None and JOB_INDEX.is_ready(),
        "faiss_shortlist_k": FAISS_SHORTLIST_K,
        "recommendation_top_k": RECOMMENDATION_TOP_K,
        "siamese_requested": USE_SIAMESE,
        "siamese_ready": siamese_ready(),
        "fairness_monitoring": "active_demo",
        "retraining": "manual",
        "fairness_summary": fairness["summary"],
    }


@app.get("/admin/fairness")
def admin_fairness(
    current_user: dict = Depends(require_roles("admin")),
):
    return compute_fairness_metrics()


@app.post("/admin/reload-jobs")
def admin_reload_jobs(
    current_user: dict = Depends(require_roles("admin")),
):
    global JOBS_DB, JOB_INDEX

    JOBS_DB = load_jobs()
    JOB_INDEX = JobFaissIndex()
    JOB_INDEX.load_or_build(JOBS_DB)

    return {
        "message": "Jobs reloaded successfully",
        "jobs_loaded": len(JOBS_DB),
        "faiss_ready": JOB_INDEX.is_ready(),
    }


@app.post("/admin/rebuild-index")
def admin_rebuild_index(
    current_user: dict = Depends(require_roles("admin")),
):
    global JOB_INDEX

    if not JOBS_DB:
        raise HTTPException(status_code=500, detail="Jobs database is empty.")

    JOB_INDEX = JobFaissIndex()
    JOB_INDEX.build(JOBS_DB, save=True)

    return {
        "message": "FAISS index rebuilt successfully",
        "jobs_indexed": len(JOBS_DB),
        "faiss_ready": JOB_INDEX.is_ready(),
    }


@app.get("/candidates")
def get_candidates(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "employer")),
):
    return {
        "count": min(limit, get_candidate_count(db)),
        "candidates": list_candidates(db, limit=limit),
    }


@app.post("/candidates")
def add_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("candidate")),
):
    cleaned_resume_text = sanitize_resume_text(candidate.resume_text)

    if not cleaned_resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")

    saved = upsert_candidate(
        db,
        full_name=sanitize_resume_text(candidate.full_name),
        email=sanitize_resume_text(candidate.email),
        phone=sanitize_resume_text(candidate.phone) if candidate.phone else None,
        summary=sanitize_resume_text(candidate.summary) if candidate.summary else None,
        resume_text=cleaned_resume_text,
        original_filename=None,
    )

    return {
        "message": "Candidate saved successfully",
        "candidate_id": saved.id,
        "full_name": saved.full_name,
        "email": saved.email,
    }


@app.post("/candidates/upload-resume")
async def upload_candidate_resume(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str | None = Form(None),
    summary: str | None = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("candidate")),
):
    if not JOBS_DB:
        raise HTTPException(
            status_code=500, detail="Job database is empty or failed to load."
        )

    if JOB_INDEX is None or not JOB_INDEX.is_ready():
        raise HTTPException(status_code=500, detail="FAISS job index is not ready.")

    file_bytes = await resume.read()
    resume_text = extract_resume_text(resume.filename, file_bytes)

    if not resume_text.strip():
        raise HTTPException(
            status_code=400, detail="Resume text could not be extracted."
        )

    candidate = upsert_candidate(
        db,
        full_name=sanitize_resume_text(full_name),
        email=sanitize_resume_text(email),
        phone=sanitize_resume_text(phone) if phone else None,
        summary=sanitize_resume_text(summary) if summary else None,
        resume_text=resume_text,
        original_filename=(
            sanitize_resume_text(resume.filename) if resume.filename else None
        ),
    )

    skills = extract_skills(resume_text)
    scores, indices = JOB_INDEX.search(resume_text, top_k=FAISS_SHORTLIST_K)

    candidate_jobs = []
    candidate_scores = []

    for pos, job_idx in enumerate(indices):
        if 0 <= job_idx < len(JOBS_DB):
            candidate_jobs.append(JOBS_DB[job_idx])
            candidate_scores.append(scores[pos])

    ranked_jobs = rank_jobs_from_candidates(
        resume_text=resume_text,
        resume_skills=skills,
        candidate_jobs=candidate_jobs,
        semantic_scores=candidate_scores,
        top_k=FAISS_SHORTLIST_K,
        use_siamese=USE_SIAMESE,
    )

    reranked_jobs = rerank_jobs_for_resume(
        resume_text=resume_text,
        jobs=ranked_jobs,
        top_k=RECOMMENDATION_TOP_K,
    )

    for job in reranked_jobs:
        job["advice"] = build_job_advice(job)

    resume_advice = build_resume_advice(
        resume_text=resume_text,
        extracted_skills=skills,
        recommendations=reranked_jobs,
    )

    return {
        "message": "Candidate saved and matched successfully",
        "candidate_id": candidate.id,
        "filename": resume.filename,
        "extracted_skills": skills,
        "recommendations_count": len(reranked_jobs),
        "advice_summary": build_candidate_job_summary(reranked_jobs),
        "resume_advice": resume_advice,
        "recommendations": reranked_jobs,
    }


@app.post("/match-resume")
async def match_resume(
    resume: UploadFile = File(...),
    current_user: dict = Depends(require_roles("candidate")),
):
    if not JOBS_DB:
        raise HTTPException(
            status_code=500,
            detail="Job database is empty or failed to load.",
        )

    if JOB_INDEX is None or not JOB_INDEX.is_ready():
        raise HTTPException(status_code=500, detail="FAISS job index is not ready.")

    file_bytes = await resume.read()
    resume_text = extract_resume_text(resume.filename, file_bytes)

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text could not be extracted.",
        )

    skills = extract_skills(resume_text)
    scores, indices = JOB_INDEX.search(resume_text, top_k=FAISS_SHORTLIST_K)

    candidate_jobs = []
    candidate_scores = []

    for pos, job_idx in enumerate(indices):
        if 0 <= job_idx < len(JOBS_DB):
            candidate_jobs.append(JOBS_DB[job_idx])
            candidate_scores.append(scores[pos])

    ranked_jobs = rank_jobs_from_candidates(
        resume_text=resume_text,
        resume_skills=skills,
        candidate_jobs=candidate_jobs,
        semantic_scores=candidate_scores,
        top_k=FAISS_SHORTLIST_K,
        use_siamese=USE_SIAMESE,
    )

    reranked_jobs = rerank_jobs_for_resume(
        resume_text=resume_text,
        jobs=ranked_jobs,
        top_k=RECOMMENDATION_TOP_K,
    )

    for job in reranked_jobs:
        job["advice"] = build_job_advice(job)

    resume_advice = build_resume_advice(
        resume_text=resume_text,
        extracted_skills=skills,
        recommendations=reranked_jobs,
    )

    return {
        "filename": resume.filename,
        "resume_text": resume_text,
        "extracted_skills": skills,
        "total_jobs_considered": len(JOBS_DB),
        "faiss_shortlist_count": len(candidate_jobs),
        "recommendations_count": len(reranked_jobs),
        "advice_summary": build_candidate_job_summary(reranked_jobs),
        "resume_advice": resume_advice,
        "recommendations": reranked_jobs,
    }


@app.post("/best-candidates")
def best_candidates(
    job: JobRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("employer")),
):
    job_title = sanitize_resume_text(job.job_title)
    job_description = sanitize_resume_text(job.job_description)

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    candidate_shortlist = search_best_candidates(
        db,
        job_description=job_description,
        top_k=EMPLOYER_SHORTLIST_K,
    )

    reranked_candidates = rerank_candidates_for_job(
        job_description=job_description,
        candidates=candidate_shortlist,
        top_k=EMPLOYER_TOP_K,
    )

    for candidate in reranked_candidates:
        candidate["advice"] = build_candidate_advice(candidate, job_title)
        candidate["employer_review"] = build_employer_candidate_review(
            candidate=candidate,
            job_title=job_title,
            job_description=job_description,
        )
        candidate.pop("resume_text_internal", None)

    return {
        "job_title": job_title,
        "candidates_count": len(reranked_candidates),
        "advice_summary": build_employer_candidate_summary(
            reranked_candidates, job_title
        ),
        "hiring_summary": build_employer_hiring_summary(reranked_candidates, job_title),
        "candidates": reranked_candidates,
    }


@app.post("/admin/upload-candidates-csv")
async def admin_upload_candidates_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="ignore")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV has no header row")

    def pick(row: dict, *names: str) -> str:
        normalized = {
            (k or "").strip().lower(): (v or "").strip() for k, v in row.items()
        }
        for n in names:
            if n in normalized and normalized[n]:
                return normalized[n]
        return ""

    saved = 0
    skipped = 0
    errors: List[Dict] = []

    for idx, row in enumerate(reader, start=2):
        full_name = pick(row, "full_name", "name")
        email = pick(row, "email", "email_address")
        phone = pick(row, "phone", "phone_number")
        summary = pick(row, "summary", "headline", "title")
        resume_text = pick(row, "resume_text", "resume", "cv", "bio", "description")

        if not full_name or not email or not resume_text:
            skipped += 1
            errors.append(
                {
                    "row": idx,
                    "reason": "Missing required field (full_name, email, or resume_text)",
                }
            )
            continue

        try:
            upsert_candidate(
                db,
                full_name=sanitize_resume_text(full_name),
                email=sanitize_resume_text(email),
                phone=sanitize_resume_text(phone) if phone else None,
                summary=sanitize_resume_text(summary) if summary else None,
                resume_text=sanitize_resume_text(resume_text),
                original_filename=file.filename,
            )
            saved += 1
        except Exception as e:
            errors.append({"row": idx, "reason": str(e)})

    return {
        "message": "CSV import complete",
        "filename": file.filename,
        "saved": saved,
        "skipped": skipped,
        "errors_count": len(errors),
        "errors": errors[:20],
    }


import json
from backend.schemas_ai import (
    FitScoreRequest,
    FitScoreResponse,
    AtsStrengthRequest,
    AtsStrengthResponse,
    CoverLetterRequest,
    CoverLetterResponse,
)

FIT_SCORE_SYSTEM = """You are a senior technical recruiter. Given a candidate's resume 
and a job description, return ONLY a valid JSON object with these exact keys:
- fit_score: integer 0-100
- verdict: "strong_match" | "moderate_match" | "weak_match"
- reasoning: 2-3 sentence explanation of the score
- strengths: list of 3-5 specific technical skills the candidate has that match
- gaps: list of 2-4 specific skills or experiences the candidate is missing
- recommendation: one actionable sentence for the candidate

Do not include markdown fences. Do not include any text outside the JSON."""

ATS_STRENGTH_SYSTEM = """You are an ATS (Applicant Tracking System) expert and senior resume \
reviewer. Analyze the resume and return ONLY a valid JSON object with these exact keys:

- overall_score: integer 0-100, the resume's overall ATS readiness
- sections: object with these integer keys (0-100 each):
    - impact: how well achievements are quantified and outcome-oriented
    - clarity: readability, conciseness, action verbs
    - keywords: density of ATS-relevant technical and role keywords
    - formatting: parsability (no tables/graphics, standard sections, dates)
    - achievements: presence of concrete, measurable results
- issues: list of 3-6 specific problems found (be concrete, cite the resume)
- improvements: list of 3-6 specific, actionable fixes (imperative voice)

Do not include any text outside the JSON. No markdown fences. No preamble."""

COVER_LETTER_SYSTEM = """You are a professional cover-letter writer for technical roles. \
Given a candidate's resume and a job description, write a concise, compelling cover letter BODY.

Rules:
- Return ONLY the body paragraphs — no greeting, no "Dear Hiring Manager", no signature, no "Sincerely".
- 3 paragraphs, roughly 200-280 words total.
- Paragraph 1: hook — why this specific role and company, referencing something concrete from the job description.
- Paragraph 2: strongest evidence — 2-3 specific achievements or skills from the resume that directly match the job's needs. Use concrete details.
- Paragraph 3: close — enthusiasm + a forward-looking sentence. No "I look forward to hearing from you."
- Tone: confident, specific, human. No clichés ("passionate team player", "hit the ground running").
- Never invent experience. Only use what's in the resume.
- Output plain text. No markdown, no bullet points, no headers."""


@app.post("/ai/match", response_model=FitScoreResponse)
def ai_match(
    payload: FitScoreRequest,
    current_user: dict = Depends(require_roles("candidate", "employer", "admin")),
):
    user_prompt = f"""JOB TITLE: {payload.job_title}

JOB DESCRIPTION:
{payload.job_description}

CANDIDATE RESUME:
{payload.resume_text}
"""
    raw = chat(
        FIT_SCORE_SYSTEM, user_prompt, model="openai/gpt-oss-20b", max_tokens=800
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Model returned invalid JSON")
    return FitScoreResponse(**data)


def _normalize_ats(data: dict) -> dict:
    """Map common alias keys the model may use to our schema's canonical names."""
    aliases = {
        "improvements": ["recommendations", "tips", "suggestions", "fixes", "actions"],
        "issues": ["problems", "concerns", "weaknesses", "areas_for_improvement"],
        "overall_score": ["score", "ats_score", "total_score"],
        "sections": ["breakdown", "subscores", "categories"],
    }
    for canonical, alts in aliases.items():
        if canonical not in data:
            for alt in alts:
                if alt in data:
                    data[canonical] = data.pop(alt)
                    break

    data.setdefault("overall_score", 0)
    data.setdefault("sections", {})
    data.setdefault("issues", [])
    data.setdefault("improvements", [])

    # Coerce every section value to int (model sometimes returns strings or floats)
    if isinstance(data.get("sections"), dict):
        cleaned = {}
        for k, v in data["sections"].items():
            try:
                cleaned[k] = int(round(float(v)))
            except (ValueError, TypeError):
                continue
        data["sections"] = cleaned

    return data


@app.post("/ai/resume-strength", response_model=AtsStrengthResponse)
def ai_resume_strength(
    payload: AtsStrengthRequest,
    current_user: dict = Depends(require_roles("candidate", "employer", "admin")),
):
    user_prompt = f"RESUME:\n{payload.resume_text}\n"
    raw = chat(
        ATS_STRENGTH_SYSTEM,
        user_prompt,
        model="openai/gpt-oss-20b",
        max_tokens=800,
    )

    # Strip accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail=f"Model returned invalid JSON: {raw[:200]}",
        )

    data = _normalize_ats(data)
    return AtsStrengthResponse(**data)


@app.post("/ai/cover-letter", response_model=CoverLetterResponse)
def ai_cover_letter(
    payload: CoverLetterRequest,
    current_user: dict = Depends(require_roles("candidate", "employer", "admin")),
):
    user_prompt = (
        f"ROLE: {payload.job_title}\n"
        f"COMPANY: {payload.company or 'the company'}\n\n"
        f"JOB DESCRIPTION:\n{payload.job_description}\n\n"
        f"CANDIDATE RESUME:\n{payload.resume_text}\n"
    )

    raw = chat(
        COVER_LETTER_SYSTEM,
        user_prompt,
        model="openai/gpt-oss-20b",
        max_tokens=1200,
    )

    body = raw.strip()

    # Strip any accidental markdown fences
    if body.startswith("```"):
        body = body.split("```")[1]
        body = body.strip()

    if not body:
        raise HTTPException(status_code=502, detail="Model returned empty cover letter")

    return CoverLetterResponse(body=body)


@app.post("/jobs/discover", response_model=JobDiscoveryResponse)
def jobs_discover(
    payload: JobDiscoveryRequest,
    current_user: dict = Depends(require_roles("candidate", "employer", "admin")),
):
    try:
        data = discover_jobs(payload.query, max_results=payload.max_results)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return JobDiscoveryResponse(
        query=payload.query,
        results=[DiscoveredJob(**r) for r in data["results"]],
        total_searched=data["total_searched"],
        filtered_out=data["filtered_out"],
    )
