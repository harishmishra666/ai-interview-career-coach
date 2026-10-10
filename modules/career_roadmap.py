
import json
import os
import re

from google import genai


def extract_json(text):
    """Extract a JSON object from an AI response."""
    text = (text or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI response mein valid JSON nahi mila.")

    return json.loads(text[start:end + 1])


def generate_career_roadmap(
    resume_text,
    target_role,
    experience_level,
    daily_hours,
    preferred_language="Hindi",
):
    """Generate a personalized career roadmap using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment mein available nahi hai."
        )

    if not resume_text or not resume_text.strip():
        raise ValueError(
            "Pehle Resume Analyzer mein resume upload karo."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an experienced AI career mentor and skills-gap analyst.

Create a realistic, personalized 30-day, 60-day, and 90-day
career roadmap using the candidate's resume and target role.

TARGET ROLE:
{target_role}

EXPERIENCE LEVEL:
{experience_level}

DAILY LEARNING TIME:
{daily_hours} hours

RESPONSE LANGUAGE:
{preferred_language}

CANDIDATE RESUME:
{resume_text[:12000]}

Instructions:
1. Identify skills supported by the resume.
2. Identify important missing or insufficiently demonstrated skills.
3. Do not claim a skill is missing if the resume gives clear evidence
   that the candidate already has it.
4. Distinguish between confirmed skills and skills that need verification.
5. Create practical weekly learning tasks for days 1-30, 31-60,
   and 61-90.
6. Include hands-on projects and measurable milestones.
7. Keep the plan realistic for the candidate's daily learning time.
8. Do not invent qualifications, certificates, job experience,
   or guaranteed employment outcomes.
9. Return ONLY valid JSON, without Markdown code fences.

Use exactly this JSON structure:
{{
  "career_summary": "Short personalized summary",
  "readiness_level": "Beginner, Developing, or Job-ready",
  "strengths": ["strength 1", "strength 2"],
  "existing_skills": [
    {{
      "skill": "Python",
      "evidence": "Evidence from resume"
    }}
  ],
  "skill_gaps": [
    {{
      "skill": "Skill name",
      "priority": "High, Medium, or Low",
      "reason": "Why it matters",
      "action": "How to improve it"
    }}
  ],
  "roadmap": [
    {{
      "phase": "Days 1-30",
      "goal": "Phase goal",
      "weeks": [
        {{
          "week": "Week 1",
          "tasks": [
            "Specific learning task",
            "Specific practice task"
          ],
          "deliverable": "Measurable output"
        }}
      ],
      "project": "Practical project for this phase",
      "milestone": "How to measure success"
    }}
  ],
  "interview_topics": [
    "Topic to practise"
  ],
  "next_actions": [
    "First action the candidate should take"
  ]
}}
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini ne koi text response nahi diya.")

    result = extract_json(response.text)

    required_fields = [
        "career_summary",
        "readiness_level",
        "strengths",
        "existing_skills",
        "skill_gaps",
        "roadmap",
        "interview_topics",
        "next_actions",
    ]

    missing = [
        field for field in required_fields
        if field not in result
    ]

    if missing:
        raise ValueError(
            "AI response mein fields missing hain: "
            + ", ".join(missing)
        )

    return result
