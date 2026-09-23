from __future__ import annotations

from typing import Dict, List


def shortlist_status(score: float) -> str:
    if score >= 0.80:
        return "shortlist"
    if score >= 0.65:
        return "review"
    return "do_not_shortlist_yet"


def shortlist_reason(score: float, skills: List[str]) -> str:
    top_skills = ", ".join(skills[:4]) if skills else "limited clearly extracted skills"

    if score >= 0.80:
        return (
            f"This candidate should be shortlisted because the overall fit is strong "
            f"and the profile shows relevant strengths in {top_skills}."
        )
    if score >= 0.65:
        return (
            f"This candidate is worth manual review because the fit is moderate. "
            f"There are useful strengths in {top_skills}, but the role match is not yet fully convincing."
        )
    return (
        f"This candidate should not be prioritized yet because the current match is weak. "
        f"The visible strengths are {top_skills}, but they do not strongly align with the role at this stage."
    )


def build_strengths(skills: List[str]) -> List[str]:
    if not skills:
        return ["No strong skill evidence was extracted from the current resume text."]
    return [f"Demonstrates background in {skill}." for skill in skills[:4]]


def build_concerns(score: float, skills: List[str], summary: str | None) -> List[str]:
    concerns: List[str] = []

    if score < 0.80:
        concerns.append(
            "Overall role match is not yet strong enough for immediate confidence."
        )

    if len(skills) < 3:
        concerns.append(
            "The resume shows a limited number of clearly extracted role-relevant skills."
        )

    if not summary or len(summary.strip()) < 20:
        concerns.append(
            "The candidate summary is too brief to assess experience depth properly."
        )

    if not concerns:
        concerns.append("No major concerns from the current automated screening.")
    return concerns


def build_interview_advice(
    candidate: Dict,
    job_title: str,
    job_description: str,
) -> List[str]:
    skills = candidate.get("skills", []) or []
    score = float(candidate.get("score", 0.0))
    advice: List[str] = []

    advice.append(
        f"Ask the candidate to explain their most relevant experience for the {job_title} role in practical terms."
    )

    if skills:
        advice.append(f"Probe depth in these areas: {', '.join(skills[:4])}.")
    else:
        advice.append(
            "Probe for concrete technical or functional skills because the resume did not expose many clearly extractable strengths."
        )

    if score >= 0.80:
        advice.append(
            "Focus the interview on project ownership, measurable impact, and ability to perform quickly in the role."
        )
        advice.append(
            "Use scenario questions to confirm the candidate can apply their strengths in real work situations."
        )
    elif score >= 0.65:
        advice.append(
            "Use the interview to verify whether the candidate's experience transfers well to this role."
        )
        advice.append("Test for missing depth areas before moving to final shortlist.")
    else:
        advice.append(
            "Use an initial screening interview only if you want to explore potential rather than direct fit."
        )
        advice.append(
            "Confirm whether the candidate has hidden experience not obvious in the resume."
        )

    if "manager" in job_title.lower() or "lead" in job_title.lower():
        advice.append("Assess leadership, prioritization, and stakeholder management.")
    else:
        advice.append(
            "Assess execution ability, problem-solving, and hands-on competence."
        )

    return advice


def build_employer_candidate_review(
    candidate: Dict,
    job_title: str,
    job_description: str,
) -> Dict:
    score = float(candidate.get("score", 0.0))
    skills = candidate.get("skills", []) or []
    summary = candidate.get("summary", "")

    decision = shortlist_status(score)

    return {
        "shortlist_status": decision,
        "shortlist_reason": shortlist_reason(score, skills),
        "strengths": build_strengths(skills),
        "concerns": build_concerns(score, skills, summary),
        "interview_advice": build_interview_advice(
            candidate, job_title, job_description
        ),
    }


def build_employer_hiring_summary(candidates: List[Dict], job_title: str) -> str:
    if not candidates:
        return f"No strong candidates were found yet for the {job_title} role."

    top = candidates[0]
    top_name = top.get("name", "the leading candidate")
    top_score = float(top.get("score", 0.0))
    status = shortlist_status(top_score)

    if status == "shortlist":
        return (
            f"The top recommendation for {job_title} is {top_name}. "
            f"This candidate should move forward to interview first, followed by the next strongest matches."
        )
    if status == "review":
        return f"The leading candidates for {job_title} look promising but need manual review before final shortlisting."
    return (
        f"The current pool does not show a strong direct match for {job_title}. "
        f"Consider widening the candidate pool or adjusting the role requirements."
    )
