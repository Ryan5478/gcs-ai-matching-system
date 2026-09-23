from __future__ import annotations

from pydantic import BaseModel


class CandidateCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    summary: str | None = None
    resume_text: str


class CandidateRead(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None = None
    summary: str | None = None
    skills: list[str]
    original_filename: str | None = None


class JobRequest(BaseModel):
    job_title: str
    job_description: str
