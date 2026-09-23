from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobItem(BaseModel):
    title: str = Field(..., description="Job title")
    company: Optional[str] = Field(default=None)
    description: str = Field(..., description="Full job description")
    location: Optional[str] = None
    job_type: Optional[str] = Field(default="full-time")
    required_skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MatchRequest(BaseModel):
    candidate_resume: str = Field(..., min_length=10)
    jobs: List[JobItem] = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)


class SkillExtractionRequest(BaseModel):
    text: str = Field(..., min_length=3)


class TrainRequest(BaseModel):
    csv_path: str = Field(default="backend/data/Resume.csv")
    epochs: int = Field(default=3, ge=1, le=20)
    batch_size: int = Field(default=16, ge=4, le=256)
    learning_rate: float = Field(default=1e-3, gt=0)
    max_pairs_per_class: int = Field(default=40, ge=4, le=500)


class RecommendationItem(BaseModel):
    rank: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    score: float
    semantic_score: float
    skill_score: float
    career_fit_bonus: float
    matched_skills: List[str]
    missing_skills: List[str]
    reasons: List[str]


class MatchResponse(BaseModel):
    candidate_skills: List[str]
    candidate_profile: Dict[str, Any]
    recommendations: List[RecommendationItem]


class TrainingResponse(BaseModel):
    status: str
    csv_path: str
    pairs_generated: int
    train_accuracy: float
    model_dir: str
    message: str
