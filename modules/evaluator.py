import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


def evaluate_answer(question, answer):

    prompt = f"""
You are an expert AI Interview Evaluator.

Evaluate the candidate's interview answer.

INTERVIEW QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Provide the evaluation in this format:

## Score
Give a score out of 10.

## Answer Quality
Briefly evaluate the quality of the answer.

## Strengths
List 3 strengths.

## Areas for Improvement
List 3 specific improvements.

## Better Answer
Provide an example of a stronger and more professional answer.

## Follow-up Question
Generate one relevant follow-up interview question.

Keep the evaluation practical, constructive and professional.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt
    )

    return response.text