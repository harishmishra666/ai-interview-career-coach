
import re

SKILL_KEYWORDS = {
    "python": ["python"],
    "sql": ["sql", "mysql", "postgresql", "sqlite"],
    "machine learning": ["machine learning", "scikit-learn", "sklearn"],
    "deep learning": ["deep learning", "pytorch", "tensorflow"],
    "generative ai": ["generative ai", "genai", "llm", "large language model"],
    "agentic ai": ["agentic ai", "ai agents", "multi-agent", "langgraph"],
    "automation": ["automation", "n8n", "workflow automation"],
    "data analysis": ["data analysis", "data analytics", "pandas", "power bi"],
    "api development": ["rest api", "fastapi", "flask", "django"],
    "git": ["git", "github", "version control"],
    "streamlit": ["streamlit"],
    "html/css": ["html", "css"],
    "cloud": ["aws", "azure", "google cloud", "gcp"],
}


def _normalize(text):
    """Normalize text for simple, case-insensitive skill matching."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def calculate_job_match(resume_text, job_description):
    """
    Calculate a transparent keyword-based resume/job match score.

    This is an approximate skill-overlap score, not an ATS score
    or a prediction of hiring success.
    """
    resume = _normalize(resume_text)
    description = _normalize(job_description)

    if not resume:
        return {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": [],
            "message": "Upload a resume to calculate the match.",
        }

    if not description:
        return {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": [],
            "message": "No job description is available for matching.",
        }

    relevant_skills = []

    for skill, aliases in SKILL_KEYWORDS.items():
        if any(alias in description for alias in aliases):
            relevant_skills.append(skill)

    if not relevant_skills:
        return {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": [],
            "message": "No supported skills were detected in this job description.",
        }

    matched = [
        skill
        for skill in relevant_skills
        if any(alias in resume for alias in SKILL_KEYWORDS[skill])
    ]
    missing = [
        skill for skill in relevant_skills if skill not in matched
    ]

    score = round((len(matched) / len(relevant_skills)) * 100)

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "message": "Approximate skill overlap; not a hiring prediction.",
    }
