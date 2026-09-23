from __future__ import annotations

from collections import Counter
from typing import Dict, List


def detect_experience_level(resume_text: str) -> str:
    text = resume_text.lower()

    if any(
        x in text
        for x in ["10 years", "8 years", "senior", "lead", "manager", "head of"]
    ):
        return "senior"
    if any(
        x in text for x in ["5 years", "6 years", "7 years", "mid-level", "specialist"]
    ):
        return "mid-level"
    if any(
        x in text
        for x in [
            "intern",
            "attachment",
            "graduate",
            "entry level",
            "junior",
            "student",
        ]
    ):
        return "entry-level"

    return "mid-level"


def summarize_profile(
    skills: List[str], recommendations: List[Dict], experience_level: str
) -> str:
    top_roles = [
        job.get("job_title", "") for job in recommendations[:3] if job.get("job_title")
    ]
    top_roles_text = ", ".join(top_roles) if top_roles else "general professional roles"

    if skills:
        skill_text = ", ".join(skills[:5])
        return (
            f"You appear to be an {experience_level} candidate with strengths in "
            f"{skill_text}. Based on your resume, your strongest job directions are {top_roles_text}."
        )

    return (
        f"You appear to be an {experience_level} candidate. "
        f"Based on your resume, your strongest job directions are {top_roles_text}."
    )


def collect_missing_skills(
    candidate_skills: List[str], recommendations: List[Dict], limit: int = 6
) -> List[str]:
    candidate_set = {s.lower().strip() for s in candidate_skills}
    counter = Counter()

    for job in recommendations[:5]:
        for skill in job.get("required_skills", []) or []:
            normalized = skill.lower().strip()
            if normalized and normalized not in candidate_set:
                counter[skill.title()] += 1

    return [skill for skill, _ in counter.most_common(limit)]


def build_improvement_advice(
    experience_level: str, missing_skills: List[str]
) -> List[str]:
    advice = []

    if missing_skills:
        advice.append(
            f"Focus on improving these missing skills: {', '.join(missing_skills[:5])}."
        )

    if experience_level == "entry-level":
        advice.append(
            "Apply first to internships, trainee roles, and junior-level jobs."
        )
        advice.append(
            "Add projects, volunteer work, and certifications to make your profile stronger."
        )
    elif experience_level == "mid-level":
        advice.append(
            "Prioritize roles where your current skills already match at least half of the requirements."
        )
        advice.append(
            "Tailor your resume for each application by emphasizing relevant achievements."
        )
    else:
        advice.append(
            "Target senior roles where leadership, project ownership, and decision-making are clearly demonstrated."
        )
        advice.append(
            "Highlight measurable business impact, team leadership, and strategic work."
        )

    advice.append(
        "Customize your CV summary for the top roles instead of using one generic version."
    )
    advice.append("Apply first to the top 3 ranked roles before trying weaker matches.")

    return advice


def build_resume_advice(
    resume_text: str,
    extracted_skills: List[str],
    recommendations: List[Dict],
) -> Dict:
    experience_level = detect_experience_level(resume_text)
    profile_summary = summarize_profile(
        extracted_skills, recommendations, experience_level
    )
    missing_skills = collect_missing_skills(extracted_skills, recommendations)
    improvement_advice = build_improvement_advice(experience_level, missing_skills)

    best_roles = [
        job.get("job_title") for job in recommendations[:5] if job.get("job_title")
    ]
    best_industries = list(
        dict.fromkeys(
            [job.get("industry") for job in recommendations[:5] if job.get("industry")]
        )
    )

    return {
        "experience_level": experience_level,
        "profile_summary": profile_summary,
        "best_fit_roles": best_roles,
        "best_fit_industries": best_industries,
        "strongest_skills": extracted_skills[:8],
        "missing_skills": missing_skills,
        "improvement_advice": improvement_advice,
    }
