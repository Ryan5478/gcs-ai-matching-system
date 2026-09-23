from __future__ import annotations

from typing import Dict, List


def _fit_label(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.70:
        return "strong"
    if score >= 0.55:
        return "moderate"
    return "developing"


def _top_skills(skills: List[str], max_items: int = 4) -> str:
    if not skills:
        return "no clear overlapping skills yet"
    return ", ".join(skills[:max_items])


def build_job_advice(job: Dict) -> str:
    score = float(job.get("score", 0.0))
    fit = _fit_label(score)
    matching_skills = job.get("matching_skills", []) or []
    internship = job.get("is_internship", False)

    if internship and score >= 0.60:
        next_step = "This is a good practical option if you want an easier entry point."
    elif score >= 0.75:
        next_step = "You should prioritize this role in your applications."
    elif score >= 0.55:
        next_step = (
            "This role is worth applying to, but strengthen the missing areas first."
        )
    else:
        next_step = "Treat this as a stretch role and improve the missing skills before applying."

    return (
        f"This is a {fit} fit for your profile. "
        f"The strongest overlap is in {_top_skills(matching_skills)}. "
        f"{next_step}"
    )


def build_candidate_advice(candidate: Dict, job_title: str) -> str:
    score = float(candidate.get("score", 0.0))
    fit = _fit_label(score)
    skills = candidate.get("skills", []) or []

    if score >= 0.80:
        next_step = "Prioritize this candidate for shortlist or first interview."
    elif score >= 0.65:
        next_step = "This candidate is promising and should be reviewed carefully."
    else:
        next_step = "This candidate may fit partially, but needs deeper screening."

    return (
        f"This candidate looks like a {fit} fit for the {job_title} role. "
        f"Key strengths include {_top_skills(skills)}. "
        f"{next_step}"
    )


def build_candidate_job_summary(recommendations: List[Dict]) -> str:
    if not recommendations:
        return "No strong job matches were found from the current catalog."

    top = recommendations[0]
    title = top.get("job_title", "this role")
    company = top.get("company", "the employer")
    score = float(top.get("score", 0.0))
    fit = _fit_label(score)

    return (
        f"Your best current match is {title} at {company}. "
        f"Overall fit looks {fit}, so start with the top 3 ranked jobs and tailor your CV toward their required skills."
    )


def build_employer_candidate_summary(candidates: List[Dict], job_title: str) -> str:
    if not candidates:
        return f"No strong candidates were found yet for the {job_title} role."

    top = candidates[0]
    name = top.get("name", "the top candidate")
    score = float(top.get("score", 0.0))
    fit = _fit_label(score)

    return (
        f"The leading recommendation for {job_title} is {name}. "
        f"The overall fit looks {fit}, so begin interviews with the top-ranked candidates and compare their strongest skill areas."
    )
