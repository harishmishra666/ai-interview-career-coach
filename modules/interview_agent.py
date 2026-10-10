import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


def generate_interview_questions(resume_text, job_description):

    prompt = f"""
You are an expert AI Interview Coach.

Based on the candidate's resume and the job description,
generate a personalized interview preparation set.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Generate:

## Technical Interview Questions
Create 8 questions specifically related to the candidate's
skills, projects and the job description.

## HR Interview Questions
Create 5 HR questions personalized to this candidate.

## Scenario-Based Questions
Create 5 practical workplace or technical scenarios.

## Preparation Tips
Give 5 specific tips for this candidate.

Do not provide answers yet.
Keep the questions practical and relevant to the candidate.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt
    )

    return response.text