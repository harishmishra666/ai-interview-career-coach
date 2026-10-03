import streamlit as st
from modules.resume_parser import extract_text_from_pdf
from modules.jd_analyzer import analyze_resume_and_jd
from modules.interview_agent import generate_interview_questions
from modules.evaluator import evaluate_answer


st.set_page_config(
    page_title="AI Interview & Career Coach",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Interview & Career Coach")

st.write(
    "Analyze your resume, match it with a job description "
    "and prepare for interviews using AI."
)

st.divider()


# ==============================
# STEP 1: RESUME UPLOAD
# ==============================

st.subheader("📄 Step 1: Upload Resume")

uploaded_file = st.file_uploader(
    "Upload your Resume (PDF)",
    type=["pdf"]
)

resume_text = ""

if uploaded_file is not None:

    st.success("Resume uploaded successfully!")

    with st.spinner("Extracting resume text..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    if resume_text:

        st.success("Resume text extracted successfully!")

        with st.expander("📋 View Extracted Resume Text"):

            st.text_area(
                "Resume Content",
                resume_text,
                height=300
            )

    else:

        st.error("Could not extract text from this PDF.")


st.divider()


# ==============================
# STEP 2: JOB DESCRIPTION
# ==============================

st.subheader("💼 Step 2: Enter Job Description")

job_description = st.text_area(
    "Paste the Job Description here",
    placeholder=(
        "Example: We are looking for an AI Engineer "
        "with Python, Machine Learning, Generative AI, "
        "LLM and automation experience..."
    ),
    height=250
)

if job_description:

    st.success("Job Description added successfully!")


st.divider()


# ==============================
# STEP 3: CAREER ANALYSIS
# ==============================

st.subheader("🤖 Step 3: AI Career Analysis")

if resume_text and job_description:

    if st.button("🚀 Analyze Resume & Job Description"):

        with st.spinner(
            "Gemini AI is analyzing your resume..."
        ):

            try:

                analysis = analyze_resume_and_jd(
                    resume_text,
                    job_description
                )

                st.success(
                    "AI analysis completed!"
                )

                st.subheader(
                    "📊 Career Analysis Report"
                )

                st.markdown(analysis)

            except Exception as e:

                st.error(
                    f"Analysis failed: {e}"
                )

else:

    st.info(
        "📌 Upload your Resume and enter a Job Description "
        "to start AI analysis."
    )


st.divider()


# ==============================
# STEP 4: INTERVIEW PREPARATION
# ==============================

st.subheader("🎤 Step 4: AI Interview Preparation")

if resume_text and job_description:

    if st.button("🎯 Generate Interview Questions"):

        with st.spinner(
            "Gemini AI is creating personalized interview questions..."
        ):

            try:

                interview_questions = generate_interview_questions(
                    resume_text,
                    job_description
                )

                st.success(
                    "Interview preparation generated successfully!"
                )

                st.subheader(
                    "📝 Personalized Interview Preparation"
                )

                st.markdown(interview_questions)

            except Exception as e:

                st.error(
                    f"Interview question generation failed: {e}"
                )

else:

    st.info(
        "📌 Upload your Resume and enter a Job Description "
        "to generate personalized interview questions."
    )


st.divider()


# ==============================
# STEP 5: AI MOCK INTERVIEW
# ==============================

st.subheader("🎤 Step 5: AI Mock Interview")

if resume_text and job_description:

    st.write(
        "Practice an interview question and get AI-powered "
        "feedback on your answer."
    )

    interview_question = st.text_area(
        "🧑‍💼 Interview Question",
        placeholder=(
            "Example: Tell me about yourself and your "
            "experience in AI and Automation."
        ),
        height=120
    )

    candidate_answer = st.text_area(
        "💬 Your Answer",
        placeholder="Type your interview answer here...",
        height=200
    )

    if st.button("📊 Evaluate My Answer"):

        if not interview_question or not candidate_answer:

            st.warning(
                "Please enter both the interview question "
                "and your answer."
            )

        else:

            with st.spinner(
                "🤖 Gemini AI is evaluating your answer..."
            ):

                try:

                    evaluation = evaluate_answer(
                        interview_question,
                        candidate_answer
                    )

                    st.success(
                        "Answer evaluation completed!"
                    )

                    st.subheader(
                        "📊 AI Interview Feedback"
                    )

                    st.markdown(evaluation)

                except Exception as e:

                    st.error(
                        f"Evaluation failed: {e}"
                    )

else:

    st.info(
        "📌 Upload your Resume and enter a Job Description "
        "to use the AI Mock Interview."
    )