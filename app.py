
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
from modules.job_finder import search_adzuna_jobs
from modules.career_roadmap import generate_career_roadmap
from streamlit_mic_recorder import speech_to_text


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
    "gd_topic": "Should Artificial Intelligence replace human jobs?",
    "gd_transcript": "",
    "gd_last_recognized": "",
    "gd_feedback": "",
    "gd_history": [],
    "gd_target_role": "",

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
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
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
            line = "â€¢ " + line[2:]

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

st.title("\U0001F3AF AI Career Coach")

st.write(
    "Your AI-powered workspace for resume analysis, ATS compatibility, "
    "interview practice, and resume building."
)

st.caption("Powered by Gemini AI \u2022 Streamlit \u2022 Python")

if client is None:
    st.warning(
        "Gemini API key configure nahi hai. AI features use karne ke liye "
        "project ki .env file check karein."
    )

st.divider()


# ==================================================
# TABS
# ==================================================


# ==================================================
# SHARED RESUME UPLOADER: UPLOAD ONCE FOR ALL TABS
# ==================================================

st.subheader("\U0001F4E4 Upload Your Resume (Upload Once)")
st.caption(
    "Ek hi PDF Resume Analyzer, Job Matcher aur Mock Interview "
    "teeno mein use hoga."
)

shared_resume_file = st.file_uploader(
    "Choose your resume PDF",
    type=["pdf"],
    key="shared_resume_upload",
)

if shared_resume_file is not None:
    shared_signature = (
        f"{shared_resume_file.name}|{shared_resume_file.size}"
    )

    if shared_signature != st.session_state.get(
        "shared_resume_signature", ""
    ):
        try:
            extracted_text = safe_extract_pdf(shared_resume_file)

            if extracted_text:
                st.session_state.resume_text = extracted_text
                st.session_state.shared_resume_signature = (
                    shared_signature
                )
                st.session_state.analyzer_report = ""
                st.session_state.matcher_report = ""
                st.session_state.interview_questions = ""
                st.session_state.evaluation_report = ""
                st.success(
                    "Resume ready hai! Ab teeno features mein "
                    "isi resume ka use hoga."
                )
            else:
                st.warning(
                    "PDF se readable text nahi mila. "
                    "Text-based PDF try karein."
                )
        except Exception as exc:
            st.error(f"Resume read nahi ho saka: {exc}")

if st.session_state.resume_text:
    st.caption("\u2705 Shared resume loaded and ready.")
else:
    st.info("Shuru karne ke liye upar apna resume PDF upload karein.")


tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "\U0001F4C4 Resume Analyzer",
    "\U0001F3AF Job Matcher",
    "\U0001F3A4 Mock Interview",
    "\U0001F6E0\uFE0F Resume Builder",
    "Verbal GD Practice",
    "AI Job Finder & Apply Agent",
    "\U0001F5FA\uFE0F Career Roadmap",
])
with tab1:
    st.write("Analyze the resume uploaded once at the top of the page.")

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
    st.header("ResumeÃ¢â‚¬â€œJob Description Matcher")

    st.write(
        "Compare your resume with a target job description "
        "to identify matching skills and missing keywords."
    )

    matcher_resume_text = st.session_state.resume_text

    if matcher_resume_text:
        st.success("Shared resume ready hai; dobara upload karne ki zaroorat nahi.")
    else:
        st.info("Pehle page ke top par resume PDF upload karein.")

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

    interview_resume = st.session_state.resume_text

    if interview_resume:
        st.success("Shared resume interview ke liye ready hai.")
    else:
        st.info("Pehle page ke top par resume PDF upload karein.")

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

# ================================
# GD_PRACTICE_FEATURE_START
# TAB 5: VERBAL GD PRACTICE
# ================================

with tab5:
    st.header("Verbal GD Practice Coach")
    st.write(
        "Microphone se bolkar GD practice karein. AI aapki contribution "
        "par feedback dega aur group mode mein virtual participant ka reply dega."
    )

    gd_topics = [
        "Should Artificial Intelligence replace human jobs?",
        "Is social media beneficial for students?",
        "Online education versus classroom education",
        "Does teamwork matter more than individual talent?",
        "Should college students do internships?",
        "Can technology solve environmental problems?",
    ]

    if st.button("Generate a new GD topic", key="gd_generate_topic"):
        if api_ready():
            try:
                with st.spinner("GD topic generate ho raha hai..."):
                    new_topic = generate_ai_response(
                        "Suggest one relevant group discussion topic for a college "
                        "student preparing for placements. Return only the topic."
                    ).strip()
                    if new_topic:
                        st.session_state.gd_topic = new_topic[:300]
                        st.session_state.gd_feedback = ""
                        st.session_state.gd_history = []
            except Exception as exc:
                st.error(f"Topic generate nahi hua: {exc}")

    st.text_input("GD Topic", key="gd_topic")
    st.text_input(
        "Target job role (optional)",
        key="gd_target_role",
        placeholder="e.g. AI Automation Engineer",
    )

    gd_mode = st.radio(
        "Practice mode",
        ["Solo speaking practice", "AI group discussion"],
        horizontal=True,
        key="gd_mode_choice",
    )

    gd_language = st.selectbox(
        "Speech recognition language",
        ["English (US)", "Hindi"],
        key="gd_language_choice",
    )
    language_code = "en-US" if gd_language == "English (US)" else "hi-IN"

    st.subheader("Speak your contribution")
    st.caption(
        "Allow microphone access if your browser asks. Speech recognition "
        "depends on browser support and language availability."
    )

    try:
        recognized_text = speech_to_text(
            language=language_code,
            start_prompt="Start speaking",
            stop_prompt="Stop recording",
            just_once=True,
            key="gd_speech_recognition",
        )
        if recognized_text and recognized_text.strip():
            if recognized_text.strip() != st.session_state.gd_last_recognized:
                st.session_state.gd_transcript = recognized_text.strip()
                st.session_state.gd_last_recognized = recognized_text.strip()
    except Exception as exc:
        st.warning(
            "Microphone recognition available nahi hua. Neeche transcript "
            f"manually type kar sakte hain. Details: {exc}"
        )

    contribution = st.text_area(
        "Your speech / transcript (you can edit it)",
        key="gd_transcript",
        height=150,
        placeholder="Speak using the microphone or type your contribution here...",
    )

    if gd_mode == "AI group discussion":
        st.caption(
            "Har contribution submit karne par AI participant ka response milega. "
            "Phir apni agli contribution type ya record karke submit karein."
        )

        if st.button("Submit contribution and get AI reply", type="primary",
                     key="gd_submit_contribution"):
            if not st.session_state.gd_topic.strip():
                st.warning("Pehle GD topic enter karein.")
            elif not contribution.strip():
                st.warning("Pehle bolkar ya type karke contribution dein.")
            elif api_ready():
                try:
                    context = "\n".join(st.session_state.gd_history[-12:])
                    resume_context = st.session_state.resume_text[:5000]
                    prompt = f"""
You are a respectful virtual participant in a student group discussion.
GD topic: {st.session_state.gd_topic}
Target role: {st.session_state.gd_target_role or "General placement"}
Resume context, if available: {resume_context or "Not provided"}
Previous discussion:
{context or "This is the opening contribution."}

Student's latest contribution:
{contribution}

Respond as one realistic GD participant in 80-120 words. Add a useful
argument, example, or respectful counterpoint. Do not dominate the discussion.
End with one short question to invite the student to respond.
"""
                    with st.spinner("AI participant is responding..."):
                        reply = generate_ai_response(prompt).strip()
                    st.session_state.gd_history.append(
                        "Student: " + contribution.strip()
                    )
                    st.session_state.gd_history.append(
                        "AI Participant: " + reply
                    )
                    st.session_state.gd_feedback = ""
                except Exception as exc:
                    st.error(f"AI reply generate nahi hua: {exc}")

        if st.session_state.gd_history:
            st.subheader("Discussion so far")
            for item in st.session_state.gd_history:
                st.markdown(item)

            if st.button("Evaluate my GD performance", key="gd_evaluate_group"):
                if api_ready():
                    try:
                        discussion = "\n\n".join(st.session_state.gd_history)
                        prompt = f"""
Act as a constructive group discussion coach.
Topic: {st.session_state.gd_topic}
Student's target role: {st.session_state.gd_target_role or "General placement"}
Evaluate ONLY observable performance from this transcript:
{discussion}

Give a score out of 10 for each: relevance, clarity, logical reasoning,
examples, respectful communication, and response to others.
Then give strengths, specific improvements, one improved sample contribution,
and three practice tips. Do not infer personality or emotion from text.
"""
                        with st.spinner("GD performance evaluate ho rahi hai..."):
                            st.session_state.gd_feedback = generate_ai_response(prompt)
                    except Exception as exc:
                        st.error(f"GD evaluation failed: {exc}")

    else:
        if st.button("Evaluate my speech", type="primary", key="gd_evaluate_solo"):
            if not st.session_state.gd_topic.strip():
                st.warning("Pehle GD topic enter karein.")
            elif not contribution.strip():
                st.warning("Pehle bolkar ya type karke contribution dein.")
            elif api_ready():
                try:
                    resume_context = st.session_state.resume_text[:5000]
                    prompt = f"""
You are a constructive verbal group discussion coach.
Topic: {st.session_state.gd_topic}
Target job role: {st.session_state.gd_target_role or "General placement"}
Resume context: {resume_context or "Not provided"}
Student's contribution:
{contribution}

Assess the answer's relevance, structure, clarity, reasoning, vocabulary,
examples, and respectful communication. Give scores out of 10 for relevant
categories, explain strengths and improvements, rewrite the answer more
effectively without inventing personal experiences, and give three practice tips.
Only evaluate the provided words; do not claim to measure actual confidence,
body language, or vocal emotion from the transcript.
"""
                    with st.spinner("Your speech is being evaluated..."):
                        st.session_state.gd_feedback = generate_ai_response(prompt)
                except Exception as exc:
                    st.error(f"Speech evaluation failed: {exc}")

    if st.session_state.gd_feedback:
        st.subheader("GD Feedback and Scorecard")
        st.markdown(st.session_state.gd_feedback)
        st.download_button(
            "Download GD Feedback",
            data=st.session_state.gd_feedback,
            file_name="gd_feedback.txt",
            mime="text/plain",
            key="gd_download_feedback",
        )

    if st.button("Reset GD practice", key="gd_reset"):
        st.session_state.gd_transcript = ""
        st.session_state.gd_last_recognized = ""
        st.session_state.gd_feedback = ""
        st.session_state.gd_history = []
        st.rerun()

# ================================
# GD_PRACTICE_FEATURE_END
# ================================


# ==================================================
# TAB 6: AI JOB FINDER & APPLY AGENT
# ==================================================

with tab6:
    st.header("AI Job Finder & Apply Agent")
    st.write(
        "Search job listings from Adzuna. Review each vacancy and "
        "open its original listing to check details and apply."
    )

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        job_keywords = st.text_input(
            "Job keywords",
            value="Python",
            key="adzuna_job_keywords",
            placeholder="Python, AI, Machine Learning...",
        )

    with col2:
        job_location = st.text_input(
            "Location",
            value="India",
            key="adzuna_job_location",
            placeholder="India, Lucknow, Remote...",
        )

    with col3:
        result_limit = st.selectbox(
            "Number of results",
            options=[5, 10, 15, 20],
            index=1,
            key="adzuna_result_limit",
        )

    if st.button(
        "Search Jobs",
        type="primary",
        key="adzuna_search_button",
    ):
        if not job_keywords.strip() or not job_location.strip():
            st.warning("Please enter both keywords and a location.")
        else:
            with st.spinner("Searching Adzuna job listings..."):
                try:
                    search_result = search_adzuna_jobs(
                        keywords=job_keywords.strip(),
                        location=job_location.strip(),
                        results_per_page=result_limit,
                    )
                    st.session_state["adzuna_search_results"] = search_result
                    st.session_state["adzuna_search_error"] = ""
                except Exception as exc:
                    st.session_state["adzuna_search_error"] = str(exc)
                    st.session_state["adzuna_search_results"] = None

    search_error = st.session_state.get("adzuna_search_error", "")
    if search_error:
        st.error(f"Job search failed: {search_error}")

    search_result = st.session_state.get("adzuna_search_results")

    if search_result is not None:
        jobs = search_result.get("jobs", [])
        st.subheader("Job Search Results")
        st.caption(
            f"Adzuna reports {search_result.get('total_results', 0)} "
            f"matching listings. Showing {len(jobs)} results."
        )

        if not jobs:
            st.info(
                "No matching jobs found. Try different keywords "
                "or another location."
            )

        for index, job in enumerate(jobs):
            with st.container(border=True):
                st.subheader(job.get("title", "Untitled role"))
                st.write(
                    f"**Company:** {job.get('company', 'Not specified')}"
                )
                st.write(
                    f"**Location:** {job.get('location', 'Not specified')}"
                )
                st.write(f"**Salary:** {job.get('salary', 'Not disclosed')}")

                description = job.get("description", "")
                with st.expander("View job description"):
                    if description:
                        st.write(description[:3000])
                        if len(description) > 3000:
                            st.caption("Description shortened for display.")
                    else:
                        st.write("No description provided by the listing.")

                apply_url = job.get("apply_url", "")
                if apply_url.startswith(("https://", "http://")):
                    st.link_button(
                        "View original listing & apply",
                        apply_url,
                        key=f"adzuna_apply_{index}",
                    )
                else:
                    st.warning("No valid listing link was provided.")

        st.caption(
            "Job listings provided by Adzuna. Review the original listing, "
            "requirements, employer, and application instructions before applying."
        )

    else:
        st.info(
            "Enter your job keywords and location, then click Search Jobs."
        )


# ==================================================
# TAB 7: AI CAREER ROADMAP & SKILL GAP ANALYZER
# ==================================================

with tab7:
    st.header("\U0001F5FA\uFE0F AI Career Roadmap & Skill Gap Analyzer")
    st.write(
        "Generate a personalized career plan, identify skill gaps, "
        "and plan your next 30, 60, and 90 days."
    )

    resume = st.session_state.get("resume_text", "")

    if not resume.strip():
        st.warning(
            "Pehle Resume Analyzer mein resume PDF upload karein."
        )
    else:
        st.success("Your shared resume is ready.")

        selected_role = st.selectbox(
            "Target job role",
            [
                "AI Automation Engineer",
                "Generative AI Engineer",
                "Agentic AI Engineer",
                "Python Developer",
                "Machine Learning Engineer",
                "Data Scientist",
                "Full Stack Developer",
                "AI Engineer",
                "Other",
            ],
            key="career_roadmap_target_role",
        )

        if selected_role == "Other":
            selected_role = st.text_input(
                "Enter your target job role",
                key="career_roadmap_custom_role",
            )

        experience = st.selectbox(
            "Current experience level",
            [
                "Student / Fresher",
                "Beginner",
                "0-2 years experience",
                "2+ years experience",
            ],
            key="career_roadmap_experience",
        )

        hours = st.select_slider(
            "Daily learning time (hours)",
            options=[0.5, 1, 2, 3, 4, 5, 6],
            value=2,
            key="career_roadmap_daily_hours",
        )

        language = st.selectbox(
            "Roadmap language",
            ["Hindi", "English", "Hinglish"],
            key="career_roadmap_language",
        )

        if st.button(
            "Generate My Career Roadmap",
            type="primary",
            key="generate_career_roadmap_button",
        ):
            if not selected_role.strip():
                st.warning("Please enter your target job role.")
            else:
                try:
                    with st.spinner(
                        "Analyzing your resume and generating roadmap..."
                    ):
                        result = generate_career_roadmap(
                            resume_text=resume,
                            target_role=selected_role,
                            experience_level=experience,
                            daily_hours=hours,
                            preferred_language=language,
                        )

                    st.session_state["career_roadmap_result"] = result
                    st.session_state["career_roadmap_error"] = ""

                except Exception as exc:
                    st.session_state["career_roadmap_error"] = str(exc)
                    st.session_state["career_roadmap_result"] = None

        error = st.session_state.get("career_roadmap_error", "")
        if error:
            st.error(f"Roadmap generation failed: {error}")

        result = st.session_state.get("career_roadmap_result")

        if result:
            st.divider()
            st.subheader("Career Readiness")
            st.write(result.get("career_summary", ""))
            st.metric(
                "Readiness Level",
                result.get("readiness_level", "Not specified"),
            )

            left, right = st.columns(2)

            with left:
                st.subheader("Your Strengths")
                for item in result.get("strengths", []):
                    st.markdown(f"- {item}")

            with right:
                st.subheader("Skills Found in Resume")
                for item in result.get("existing_skills", []):
                    if isinstance(item, dict):
                        st.markdown(
                            f"- **{item.get('skill', 'Skill')}**: "
                            f"{item.get('evidence', '')}"
                        )
                    else:
                        st.markdown(f"- {item}")

            st.divider()
            st.subheader("Skill Gap Analysis")

            gaps = result.get("skill_gaps", [])
            if not gaps:
                st.info("No specific skill gaps were returned.")
            else:
                for gap in gaps:
                    if not isinstance(gap, dict):
                        st.markdown(f"- {gap}")
                        continue

                    with st.expander(
                        f"{gap.get('skill', 'Skill')} | "
                        f"Priority: {gap.get('priority', 'Medium')}"
                    ):
                        st.write(
                            f"**Why it matters:** "
                            f"{gap.get('reason', 'Not specified')}"
                        )
                        st.write(
                            f"**Action plan:** "
                            f"{gap.get('action', 'Not specified')}"
                        )

            st.divider()
            st.subheader("30-60-90 Day Roadmap")

            for phase in result.get("roadmap", []):
                if not isinstance(phase, dict):
                    continue

                with st.expander(
                    f"{phase.get('phase', 'Phase')}: "
                    f"{phase.get('goal', '')}",
                    expanded=True,
                ):
                    for week in phase.get("weeks", []):
                        if not isinstance(week, dict):
                            continue

                        st.markdown(f"**{week.get('week', 'Week')}**")
                        for task in week.get("tasks", []):
                            st.markdown(f"- [ ] {task}")

                        st.write(
                            f"**Deliverable:** "
                            f"{week.get('deliverable', 'Not specified')}"
                        )

                    st.write(
                        f"**Project:** {phase.get('project', 'Not specified')}"
                    )
                    st.write(
                        f"**Milestone:** "
                        f"{phase.get('milestone', 'Not specified')}"
                    )

            st.subheader("Interview Topics")
            for topic in result.get("interview_topics", []):
                st.markdown(f"- {topic}")

            st.subheader("Next Actions")
            for action in result.get("next_actions", []):
                st.markdown(f"- [ ] {action}")

            st.caption(
                "AI-generated guidance. Verify suggestions against your "
                "actual skills and experience."
            )
# FOOTER
# ==================================================

st.divider()

st.caption(
    "AI Career Coach | Always review AI-generated content before "
    "using it in job applications. Never include false qualifications "
    "or achievements."
)
