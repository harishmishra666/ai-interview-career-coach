
import json
import uuid
from pathlib import Path

import streamlit as st
from modules.academy_tutor import render_ai_tutor
from modules.academy_quiz import render_ai_quiz


# --------------------------------------------------
# PATHS AND LOCAL STORAGE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "academy_data"
UPLOAD_DIR = BASE_DIR / "academy_uploads"
VIDEO_DIR = UPLOAD_DIR / "videos"
MATERIAL_DIR = UPLOAD_DIR / "materials"

COURSES_FILE = DATA_DIR / "courses.json"

for folder in [DATA_DIR, VIDEO_DIR, MATERIAL_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# DEFAULT COURSES
# --------------------------------------------------

DEFAULT_COURSES = [
    {
        "id": "python-ai",
        "title": "Python for AI",
        "level": "Beginner",
        "language": "Hindi + English",
        "description": "Learn Python fundamentals and build a foundation for AI development.",
        "lessons": [
            {"id": "python-1", "title": "Python Basics",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "python-2", "title": "Variables and Data Types",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "python-3", "title": "Functions",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "python-4", "title": "Object Oriented Programming",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "python-5", "title": "Python for AI",
             "youtube_url": "", "video_file": "", "material_file": ""},
        ],
    },
    {
        "id": "generative-ai",
        "title": "Generative AI",
        "level": "Beginner to Intermediate",
        "language": "Hindi + English",
        "description": "Understand LLMs, prompt engineering and practical Generative AI applications.",
        "lessons": [
            {"id": "genai-1", "title": "Introduction to Generative AI",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "genai-2", "title": "Large Language Models",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "genai-3", "title": "Prompt Engineering",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "genai-4", "title": "RAG Basics",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "genai-5", "title": "AI Applications",
             "youtube_url": "", "video_file": "", "material_file": ""},
        ],
    },
    {
        "id": "n8n-automation",
        "title": "AI Automation with n8n",
        "level": "Beginner to Intermediate",
        "language": "Hindi + English",
        "description": "Learn to automate tasks and create AI-powered workflows.",
        "lessons": [
            {"id": "n8n-1", "title": "Introduction to n8n",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "n8n-2", "title": "Workflow Basics",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "n8n-3", "title": "API Integration",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "n8n-4", "title": "AI Agents",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "n8n-5", "title": "Automation Projects",
             "youtube_url": "", "video_file": "", "material_file": ""},
        ],
    },
    {
        "id": "agentic-ai",
        "title": "Agentic AI",
        "level": "Intermediate",
        "language": "Hindi + English",
        "description": "Explore AI agents, tools, memory and multi-step workflows.",
        "lessons": [
            {"id": "agent-1", "title": "Agent Fundamentals",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "agent-2", "title": "Tools and Functions",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "agent-3", "title": "Agent Memory",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "agent-4", "title": "Multi-Agent Systems",
             "youtube_url": "", "video_file": "", "material_file": ""},
            {"id": "agent-5", "title": "Agentic AI Projects",
             "youtube_url": "", "video_file": "", "material_file": ""},
        ],
    },
]


# --------------------------------------------------
# COURSE DATABASE FUNCTIONS
# --------------------------------------------------

def load_courses():
    if not COURSES_FILE.exists():
        save_courses(DEFAULT_COURSES)
        return DEFAULT_COURSES.copy()

    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        st.error("Course database could not be read.")

    return []


def save_courses(courses):
    temporary_file = COURSES_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(courses, file, indent=4, ensure_ascii=False)

    temporary_file.replace(COURSES_FILE)


def store_uploaded_file(uploaded_file, folder, allowed_extensions):
    if uploaded_file is None:
        return ""

    original_name = Path(uploaded_file.name)
    extension = original_name.suffix.lower()

    if extension not in allowed_extensions:
        raise ValueError("Unsupported file format.")

    unique_name = f"{uuid.uuid4().hex}{extension}"
    destination = folder / unique_name

    with open(destination, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(destination.relative_to(BASE_DIR))


def get_safe_file_path(relative_path):
    if not relative_path:
        return None

    try:
        path = (BASE_DIR / relative_path).resolve()
        path.relative_to(BASE_DIR.resolve())
        return path if path.is_file() else None
    except (ValueError, OSError):
        return None


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------

def render_admin_login():
    st.subheader("🔐 Admin Login")

    try:
        admin_password = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        admin_password = ""

    if not admin_password:
        st.error(
            "Admin password configured nahi hai. "
            "Please .streamlit/secrets.toml check karein."
        )
        return

    with st.form("academy_admin_login"):
        entered_password = st.text_input(
            "Admin Password",
            type="password"
        )

        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if entered_password == admin_password:
            st.session_state["academy_admin_logged_in"] = True
            st.success("Admin login successful!")
            st.rerun()
        else:
            st.error("Incorrect password.")


# --------------------------------------------------
# ADMIN PANEL
# --------------------------------------------------

def render_admin_panel():
    st.subheader("⚙️ Academy Admin Panel")

    st.success("Admin access active.")

    if st.button("Logout Admin"):
        st.session_state["academy_admin_logged_in"] = False
        st.rerun()

    courses = load_courses()

    admin_tab1, admin_tab2 = st.tabs([
        "➕ Create Course",
        "🎬 Add Lesson"
    ])

    # CREATE COURSE
    with admin_tab1:
        st.markdown("### Create a New Course")

        with st.form("create_academy_course"):
            title = st.text_input("Course Name")
            level = st.selectbox(
                "Course Level",
                ["Beginner", "Intermediate", "Advanced",
                 "Beginner to Intermediate"]
            )
            language = st.selectbox(
                "Course Language",
                ["Hindi", "English", "Hindi + English"]
            )
            description = st.text_area("Course Description")

            create_clicked = st.form_submit_button("Create Course")

        if create_clicked:
            if not title.strip() or not description.strip():
                st.error("Course name and description are required.")
            elif any(
                c["title"].strip().casefold() == title.strip().casefold()
                for c in courses
            ):
                st.error("A course with this name already exists.")
            else:
                courses.append({
                    "id": uuid.uuid4().hex,
                    "title": title.strip(),
                    "level": level,
                    "language": language,
                    "description": description.strip(),
                    "lessons": [],
                })

                save_courses(courses)
                st.success("Course created successfully!")
                st.rerun()

    # ADD LESSON
    with admin_tab2:
        st.markdown("### Add a Lesson to a Course")

        if not courses:
            st.info("Create a course first.")
        else:
            course_options = {
                course["title"]: course["id"]
                for course in courses
            }

            with st.form("add_academy_lesson"):
                selected_title = st.selectbox(
                    "Select Course",
                    list(course_options.keys())
                )

                lesson_title = st.text_input("Lesson Name")

                youtube_url = st.text_input(
                    "YouTube Video URL (optional)",
                    placeholder="https://www.youtube.com/watch?v=..."
                )

                video_file = st.file_uploader(
                    "Upload Video (MP4 / MOV / WEBM)",
                    type=["mp4", "mov", "webm"]
                )

                pdf_file = st.file_uploader(
                    "Upload Study Material (PDF)",
                    type=["pdf"]
                )

                lesson_clicked = st.form_submit_button("Add Lesson")

            if lesson_clicked:
                if not lesson_title.strip():
                    st.error("Please enter a lesson name.")
                elif not youtube_url.strip() and video_file is None:
                    st.error("Add a YouTube URL or upload a video.")
                else:
                    try:
                        selected_id = course_options[selected_title]
                        target_course = next(
                            c for c in courses if c["id"] == selected_id
                        )

                        video_path = store_uploaded_file(
                            video_file, VIDEO_DIR, {".mp4", ".mov", ".webm"}
                        )

                        pdf_path = store_uploaded_file(
                            pdf_file, MATERIAL_DIR, {".pdf"}
                        )

                        target_course.setdefault("lessons", []).append({
                            "id": uuid.uuid4().hex,
                            "title": lesson_title.strip(),
                            "youtube_url": youtube_url.strip(),
                            "video_file": video_path,
                            "material_file": pdf_path,
                        })

                        save_courses(courses)
                        st.success("Lesson added successfully!")
                        st.rerun()

                    except (ValueError, OSError, StopIteration) as error:
                        st.error(f"Could not add lesson: {error}")

    st.divider()
    st.markdown("### 📚 Existing Courses")

    if not courses:
        st.info("No courses available.")
    else:
        for course in courses:
            with st.expander(course["title"]):
                st.write(course["description"])
                st.write("Level:", course["level"])
                st.write("Language:", course["language"])
                st.write("Lessons:", len(course.get("lessons", [])))


# --------------------------------------------------
# STUDENT COURSE DASHBOARD
# --------------------------------------------------

def render_student_courses():
    st.subheader("📚 Course Dashboard")

    courses = load_courses()

    if not courses:
        st.info("No courses are available yet.")
        return

    course_titles = [course["title"] for course in courses]

    selected_title = st.selectbox(
        "Choose a course",
        course_titles,
        key="academy_course_select"
    )

    course = next(
        item for item in courses if item["title"] == selected_title
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Course Level", course["level"])

    with col2:
        st.metric("Language", course["language"])

    st.info(course["description"])

    lessons = course.get("lessons", [])

    st.divider()
    st.subheader("📖 Course Curriculum")

    if not lessons:
        st.info("No lessons added to this course yet.")
        return

    lesson_titles = [lesson["title"] for lesson in lessons]

    selected_lesson_title = st.selectbox(
        "Choose a lesson",
        lesson_titles,
        key=f"lesson_{course['id']}"
    )

    lesson = next(
        item for item in lessons
        if item["title"] == selected_lesson_title
    )

    st.write(f"**Selected course:** {course['title']}")
    st.write(f"**Current lesson:** {lesson['title']}")

    st.divider()
    st.subheader("▶️ Video Lecture")

    local_video = get_safe_file_path(lesson.get("video_file", ""))

    if local_video:
        st.video(str(local_video))
    elif lesson.get("youtube_url"):
        st.video(lesson["youtube_url"])
    else:
        st.info("Video has not been added yet.")

    pdf_path = get_safe_file_path(lesson.get("material_file", ""))

    if pdf_path:
        with open(pdf_path, "rb") as file:
            st.download_button(
                "📄 Download Study Material",
                data=file.read(),
                file_name=pdf_path.name,
                mime="application/pdf",
            )
    # --------------------------------------------------
    # AI QUIZ GENERATOR
    # --------------------------------------------------

    render_ai_quiz(
        course=course,
        lesson=lesson,
        pdf_path=pdf_path
    )

    # --------------------------------------------------
    # AI PERSONAL TUTOR
    # --------------------------------------------------

    render_ai_tutor(
        course=course,
        lesson=lesson,
        pdf_path=pdf_path
    )
# --------------------------------------------------
# MAIN ACADEMY
# --------------------------------------------------

def render_learning_academy():
    st.title("🎓 AI Learning Academy")

    st.write(
        "Learn AI, Python, Generative AI and Automation "
        "through structured video courses."
    )

    student_tab, admin_tab = st.tabs([
        "🎓 Student Learning",
        "🔐 Admin Panel"
    ])

    with student_tab:
        render_student_courses()

    with admin_tab:
        if st.session_state.get("academy_admin_logged_in", False):
            render_admin_panel()
        else:
            render_admin_login()

    st.divider()
    st.caption(
        "AI Learning Academy | Learn • Practice • Build"
    )
