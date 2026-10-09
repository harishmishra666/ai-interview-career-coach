
import os
import re
import html
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from google import genai
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

from modules.resume_parser import extract_text_from_pdf
from modules.jd_analyzer import analyze_resume_and_jd
from modules.interview_agent import generate_interview_questions
from modules.evaluator import evaluate_answer


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

st.set_page_config(
    page_title="AI Career Coach",
    page_icon="🎯",
    layout="wide",
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "resume_text": "",
    "analyzer_report": "",
    "matcher_resume_text": "",
    "matcher_report": "",
    "matcher_upload_signature": "",
    "interview_questions": "",
    "evaluation_report": "",
    "generated_resume": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def api_ready():
    if client is None:
        st.error(
            "Gemini API key nahi mili. Project ki .env file mein "
            "GEMINI_API_KEY configure karein. API key chat mein share na karein."
        )
        return False
    return True


def generate_ai_response(prompt):
    if client is None:
        raise ValueError("GEMINI_API_KEY is not configured.")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini ne koi text response nahi diya.")

    return response.text


def safe_extract_pdf(uploaded_file):
    if uploaded_file is None:
        return ""

    uploaded_file.seek(0)
    text = extract_text_from_pdf(uploaded_file)
    uploaded_file.seek(0)

    return text.strip() if text else ""


def analyze_resume(resume_text, job_description=""):
    prompt = f"""
You are an expert ATS resume reviewer and career coach.

Analyze the supplied resume honestly. Do not invent qualifications,
skills, work experience, achievements, or certifications.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description if job_description.strip() else "No job description provided. Perform a general resume review."}

Use these exact headings:

ATS Compatibility Score: XX/100

1. Overall Assessment
2. Relevant Skills Found
3. Missing Skills and Keywords
4. Resume Strengths
5. Resume Weaknesses
6. Job Description Match Percentage
7. Project and Experience Relevance
8. ATS Formatting Issues
9. Actionable Improvements
10. Suggested Keywords

Give an estimated ATS compatibility score from 0 to 100.
If there is no job description, explain that the score is a general
resume-quality estimate rather than a job-specific match.
Explain that actual ATS results depend on the employer's software
and screening criteria.

Use clear, practical Markdown.
"""
    return generate_ai_response(prompt)


def build_resume_prompt(
    name,
    email,
    phone,
    location,
    role,
    education,
    skills,
    experience,
    projects,
    certifications,
):
    return f"""
You are a professional ATS-friendly resume writer.

Create a polished resume using only the information supplied below.
Never invent qualifications, dates, companies, skills, or achievements.
If information is missing, omit that section instead of making it up.
Return clean Markdown without code fences.

Full name: {name}
Email: {email}
Phone: {phone}
Location: {location}
Target role: {role}
Education: {education}
Skills: {skills}
Work experience and training: {experience}
Projects: {projects}
Certifications and achievements: {certifications}

Include a concise professional summary, education, skills, experience,
projects, and certifications when the information is available.
Use clear headings and concise bullet points.
"""


def create_resume_pdf(resume_text):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Professional Resume",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ResumeName",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#163A5F"),
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#163A5F"),
            spaceBefore=9,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=4,
        )
    )

    story = []
    first_heading = True

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 3))
            continue

        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            safe_heading = html.escape(heading)

            if first_heading:
                story.append(
                    Paragraph(safe_heading, styles["ResumeName"])
                )
                first_heading = False
            else:
                story.append(
                    Paragraph(safe_heading, styles["ResumeSection"])
                )
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=colors.HexColor("#B8C7D9"),
                    )
                )
            continue

        if line.startswith(("- ", "* ")):
            line = "• " + line[2:]

        safe_line = html.escape(line)
        safe_line = re.sub(
            r"\*\*(.+?)\*\*",
            r"<b>\1</b>",
            safe_line,
        )

        story.append(
            Paragraph(safe_line, styles["ResumeText"])
        )

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def display_report(report, report_prefix):
    score_match = re.search(
        r"ATS Compatibility Score\s*:\s*(\d{1,3})\s*(?:/100)?",
        report,
        re.IGNORECASE,
    )

    if score_match:
        score = max(0, min(100, int(score_match.group(1))))
        st.metric("Estimated ATS Score", f"{score}/100")
        st.progress(score / 100)
        st.caption(
            "Yeh AI estimate hai, kisi specific employer ke ATS ka official score nahi."
        )

    st.markdown(report)

    st.download_button(
        "Download Report",
        data=report,
        file_name=f"{report_prefix}.txt",
        mime="text/plain",
        key=f"download_{report_prefix}",
    )


# ==================================================
# HEADER
# ==================================================

st.title("🎯 AI Career Coach")

st.write(
    "Your AI-powered workspace for resume analysis, ATS compatibility, "
    "interview practice, and resume building."
)

st.caption("Powered by Gemini AI • Streamlit • Python")

if client is None:
    st.warning(
        "Gemini API key configure nahi hai. AI features use karne ke liye "
        "project ki .env file check karein."
    )

st.divider()


# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📄 Resume Analyzer",
        "🎯 Job Matcher",
        "🎤 Mock Interview",
        "🛠️ Resume Builder",
    ]
)


# ==================================================
# TAB 1: RESUME ANALYZER
# ==================================================

with tab1:
    st.header("AI Resume Analyzer")

    st.write(
        "Upload a PDF resume to review its strengths, weaknesses, "
        "keywords, and estimated ATS compatibility."
    )

    analyzer_file = st.file_uploader(
        "Upload Resume PDF",
        type=["pdf"],
        key="analyzer_upload",
    )

    if analyzer_file is not None:
        try:
            resume_text = safe_extract_pdf(analyzer_file)

            if resume_text:
                st.session_state.resume_text = resume_text
                st.success("Resume successfully read ho gaya.")
            else:
                st.warning(
                    "PDF se readable text nahi mila. Scanned PDF ke liye OCR ki zarurat ho sakti hai."
                )

        except Exception as exc:
            st.error(f"Resume read nahi ho saka: {exc}")

    if st.session_state.resume_text:
        with st.expander("Extracted Resume Text"):
            st.text(st.session_state.resume_text[:15000])

        if st.button(
            "Analyze My Resume",
            type="primary",
            key="analyze_resume",
        ):
            if api_ready():
                try:
                    with st.spinner("Resume analyze ho raha hai..."):
                        st.session_state.analyzer_report = analyze_resume(
                            st.session_state.resume_text
                        )
                except Exception as exc:
                    st.error(
                        f"Analysis fail hua: {exc}"
                    )

    if st.session_state.analyzer_report:
        st.subheader("Resume Analysis Report")
        display_report(
            st.session_state.analyzer_report,
            "resume_analysis",
        )


# ==================================================
# TAB 2: JOB MATCHER
# ==================================================

with tab2:
    st.header("Resume–Job Description Matcher")

    st.write(
        "Compare your resume with a target job description "
        "to identify matching skills and missing keywords."
    )

    job_resume_file = st.file_uploader(
        "Upload Resume PDF",
        type=["pdf"],
        key="matcher_resume_upload",
    )

    # Initialize the text-area state before creating the widget.
    if job_resume_file is not None:
        upload_signature = (
            f"{job_resume_file.name}|{job_resume_file.size}"
        )

        # Read a newly selected PDF only once. This also lets the user
        # edit the extracted text without it being overwritten every rerun.
        if (
            upload_signature
            != st.session_state.matcher_upload_signature
        ):
            try:
                uploaded_resume_text = safe_extract_pdf(
                    job_resume_file
                )

                if uploaded_resume_text:
                    st.session_state.matcher_resume_text = (
                        uploaded_resume_text
                    )
                    st.session_state.matcher_upload_signature = (
                        upload_signature
                    )
                    st.success("Matcher resume ready hai.")
                else:
                    st.warning(
                        "PDF se text nahi mila. Dusri PDF try karein."
                    )

            except Exception as exc:
                st.error(f"Resume read nahi ho saka: {exc}")

    matcher_resume_text = st.text_area(
        "Resume text",
        height=200,
        key="matcher_resume_text",
        placeholder=(
            "Upload a PDF above or paste your resume text here."
        ),
    )

    job_description = st.text_area(
        "Paste Job Description",
        height=220,
        key="job_description",
        placeholder=(
            "Paste the job title, responsibilities, required skills, "
            "and qualifications here."
        ),
    )

    if st.button(
        "Match Resume with Job",
        type="primary",
        key="match_resume",
    ):
        if not matcher_resume_text.strip():
            st.warning(
                "Pehle resume upload karein ya resume text paste karein."
            )
        elif not job_description.strip():
            st.warning("Job description paste karein.")
        elif api_ready():
            try:
                with st.spinner(
                    "Resume aur job description compare ho rahe hain..."
                ):
                    st.session_state.matcher_report = (
                        analyze_resume_and_jd(
                            matcher_resume_text,
                            job_description,
                        )
                    )

                st.success("Job matching analysis complete!")

            except Exception as exc:
                st.error(f"Job matching fail hua: {exc}")

    if st.session_state.matcher_report:
        st.subheader("Job Matching Report")
        display_report(
            st.session_state.matcher_report,
            "job_match_report",
        )


# ==================================================
# TAB 3: MOCK INTERVIEW
# ==================================================

with tab3:
    st.header("AI Mock Interview")

    st.write(
        "Generate interview questions, practise your answers, "
        "and receive AI feedback."
    )

    interview_resume = st.text_area(
        "Resume / Candidate Background",
        value=st.session_state.resume_text,
        height=150,
        key="interview_resume",
        placeholder="Paste your resume or professional background.",
    )

    interview_jd = st.text_area(
        "Target Job Description (optional)",
        height=130,
        key="interview_job_description",
        placeholder="Paste the target job description.",
    )

    if st.button(
        "Generate Interview Questions",
        type="primary",
        key="generate_questions",
    ):
        if not interview_resume.strip():
            st.warning("Resume text ya candidate background enter karein.")
        elif api_ready():
            try:
                with st.spinner("Interview questions generate ho rahe hain..."):
                    st.session_state.interview_questions = (
                        generate_interview_questions(
                            interview_resume,
                            interview_jd,
                        )
                    )
            except Exception as exc:
                st.error(f"Questions generate nahi hue: {exc}")

    if st.session_state.interview_questions:
        st.subheader("Practice Questions")
        st.markdown(st.session_state.interview_questions)

        st.download_button(
            "Download Interview Questions",
            data=st.session_state.interview_questions,
            file_name="mock_interview_questions.txt",
            mime="text/plain",
            key="download_interview_questions",
        )

    st.divider()
    st.subheader("Evaluate Your Answer")

    interview_question = st.text_area(
        "Interview Question",
        key="interview_question",
        placeholder="Paste one interview question here.",
    )

    candidate_answer = st.text_area(
        "Your Answer",
        height=180,
        key="candidate_answer",
        placeholder="Write the answer you would give in an interview.",
    )

    if st.button(
        "Evaluate My Answer",
        type="primary",
        key="evaluate_answer",
    ):
        if not interview_question.strip():
            st.warning("Interview question enter karein.")
        elif not candidate_answer.strip():
            st.warning("Apna answer enter karein.")
        elif api_ready():
            try:
                with st.spinner("Answer evaluate ho raha hai..."):
                    st.session_state.evaluation_report = evaluate_answer(
                        interview_question,
                        candidate_answer,
                    )
            except Exception as exc:
                st.error(f"Answer evaluation fail hua: {exc}")

    if st.session_state.evaluation_report:
        st.subheader("Interview Feedback")
        st.markdown(st.session_state.evaluation_report)

        st.download_button(
            "Download Interview Feedback",
            data=st.session_state.evaluation_report,
            file_name="interview_feedback.txt",
            mime="text/plain",
            key="download_interview_feedback",
        )


# ==================================================
# TAB 4: RESUME BUILDER
# ==================================================

with tab4:
    st.header("AI Resume Builder")

    st.write(
        "Enter your genuine details to create a professional, "
        "ATS-friendly resume and download it as a PDF."
    )

    with st.form("resume_builder_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        location = st.text_input("City / Location")

        target_role = st.text_input(
            "Target Job Role",
            placeholder="e.g. AI Automation Engineer",
        )

        education = st.text_area(
            "Education",
            height=100,
            placeholder="Degree, university, year, and marks if relevant.",
        )

        skills = st.text_area(
            "Skills",
            height=100,
            placeholder="List your technical and professional skills.",
        )

        experience = st.text_area(
            "Work Experience / Training",
            height=120,
            placeholder="Role, organization, duration, and responsibilities.",
        )

        projects = st.text_area(
            "Projects",
            height=120,
            placeholder="Project name, technologies, and your contribution.",
        )

        certifications = st.text_area(
            "Certifications / Achievements",
            height=80,
        )

        build_clicked = st.form_submit_button(
            "Generate Professional Resume",
            type="primary",
        )

    if build_clicked:
        if not full_name.strip():
            st.warning("Full name enter karein.")
        elif not target_role.strip():
            st.warning("Target job role enter karein.")
        elif not any(
            value.strip()
            for value in [
                education,
                skills,
                experience,
                projects,
            ]
        ):
            st.warning(
                "Education, skills, experience, ya projects mein se "
                "kam se kam ek section bharein."
            )
        elif api_ready():
            try:
                with st.spinner("Professional resume ban raha hai..."):
                    st.session_state.generated_resume = (
                        generate_ai_response(
                            build_resume_prompt(
                                full_name,
                                email,
                                phone,
                                location,
                                target_role,
                                education,
                                skills,
                                experience,
                                projects,
                                certifications,
                            )
                        )
                    )

                st.success("Resume successfully generate ho gaya!")

            except Exception as exc:
                st.error(f"Resume generate nahi hua: {exc}")

    if st.session_state.generated_resume:
        st.subheader("Resume Preview")
        st.markdown(st.session_state.generated_resume)

        try:
            pdf_data = create_resume_pdf(
                st.session_state.generated_resume
            )

            st.download_button(
                "Download Resume as PDF",
                data=pdf_data,
                file_name="professional_resume.pdf",
                mime="application/pdf",
                type="primary",
                key="download_resume_pdf",
            )

        except Exception as exc:
            st.error(f"PDF create nahi ho saka: {exc}")

        st.download_button(
            "Download Resume as Markdown",
            data=st.session_state.generated_resume,
            file_name="professional_resume.md",
            mime="text/markdown",
            key="download_resume_markdown",
        )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "AI Career Coach | Always review AI-generated content before "
    "using it in job applications. Never include false qualifications "
    "or achievements."
)