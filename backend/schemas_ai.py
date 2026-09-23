from pydantic import BaseModel, Field
from typing import List, Literal, Dict


class FitScoreRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)
    job_title: str = ""


class FitScoreResponse(BaseModel):
    fit_score: int = Field(ge=0, le=100)
    verdict: Literal["strong_match", "moderate_match", "weak_match"]
    reasoning: str
    strengths: List[str]
    gaps: List[str]
    recommendation: str


class AtsStrengthRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)


class AtsStrengthResponse(BaseModel):
    overall_score: int = Field(default=0, ge=0, le=100)
    sections: Dict[str, int] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)


class CoverLetterRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)
    job_title: str = ""
    company: str = ""


class CoverLetterResponse(BaseModel):
    body: str


class JobDiscoveryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=200)
    max_results: int = Field(default=20, ge=1, le=30)


class DiscoveredJob(BaseModel):
    title: str
    url: str
    company: str = ""
    snippet: str = ""
    source: str = ""


class JobDiscoveryResponse(BaseModel):
    query: str
    results: List[DiscoveredJob]
    total_searched: int
    filtered_out: int
