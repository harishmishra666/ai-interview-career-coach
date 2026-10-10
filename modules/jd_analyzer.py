import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


def analyze_resume_and_jd(resume_text, job_description):

    prompt = f"""
You are an expert AI Career Coach and ATS Resume Analyzer.

Analyze the following resume against the given job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide the analysis in the following format:

1. Match Percentage
2. Skills Found
3. Missing Skills
4. Resume Strengths
5. Resume Weaknesses
6. Suggested Job Role
7. Skill Gap Analysis
8. Specific Recommendations

Keep the response clear, practical and professional.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt
    )

    return response.text