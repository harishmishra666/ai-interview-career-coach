
import json
import uuid
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_FILE = DATA_DIR / "project_studio.json"

CATEGORIES = [
    "Agentic AI",
    "Generative AI",
    "Machine Learning",
    "Python",
    "AI Automation",
    "Web Development",
    "Data Science",
    "AI/ML",
    "Startup / Business",
]

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced", "Expert"]

PROJECT_STATUSES = [
    "Not Started",
    "Planning",
    "In Progress",
    "Testing",
    "Completed",
    "On Hold",
]


def load_projects():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECTS_FILE.exists():
        return []

    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_projects(projects):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(PROJECTS_FILE, "w", encoding="utf-8") as file:
        json.dump(projects, file, indent=4, ensure_ascii=False)


def generate_response(generate_ai_response, prompt):
    try:
        return generate_ai_response(prompt)
    except Exception as exc:
        st.error(f"AI response generate nahi hua: {exc}")
        return None


def render_ideas_generator(generate_ai_response):
    st.subheader("💡 AI Project Ideas Generator")
    st.write(
        "Apni interest aur skill level ke according practical project ideas generate karo."
    )

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox(
            "Project Category",
            CATEGORIES,
            key="studio_idea_category",
        )

    with col2:
        difficulty = st.selectbox(
            "Difficulty Level",
            DIFFICULTIES,
            key="studio_idea_difficulty",
        )

    skills = st.text_input(
        "Your Current Skills",
        placeholder="Python, Streamlit, LangChain, n8n...",
        key="studio_idea_skills",
    )

    goal = st.selectbox(
        "Your Main Goal",
        [
            "Learning and Skill Development",
            "Resume and Portfolio",
            "Freelancing and Income",
            "Startup / Business",
            "Research and Innovation",
        ],
        key="studio_idea_goal",
    )

    count = st.slider(
        "Number of Project Ideas",
        min_value=1,
        max_value=10,
        value=5,
        key="studio_idea_count",
    )

    if st.button(
        "🚀 Generate Project Ideas",
        type="primary",
        key="studio_generate_ideas",
    ):
        prompt = f"""
You are an experienced AI project architect and technical mentor.

Generate {count} original and practical project ideas.

Category: {category}
Difficulty: {difficulty}
Current skills: {skills or "Not specified"}
User goal: {goal}

For every project provide:

1. Project title
2. Problem statement
3. Proposed solution
4. Real-world use case
5. Main features
6. Recommended technology stack
7. Skills required
8. Estimated development time
9. Resume and portfolio value
10. Monetization potential, if relevant
11. Possible future improvements

Keep the suggestions realistic and technically achievable.
Explain technical terms where necessary.
Do not promise guaranteed income.
"""

        with st.spinner("Generating project ideas..."):
            result = generate_response(generate_ai_response, prompt)

        if result:
            st.session_state.studio_generated_ideas = result

    if st.session_state.get("studio_generated_ideas"):
        st.markdown("---")
        st.markdown(st.session_state.studio_generated_ideas)


def render_project_planner(generate_ai_response):
    st.subheader("🗺️ AI Project Planner")
    st.write("Convert your project idea into a practical development roadmap.")

    title = st.text_input(
        "Project Name",
        key="studio_planner_title",
    )

    description = st.text_area(
        "Describe Your Project",
        height=120,
        key="studio_planner_description",
    )

    col1, col2 = st.columns(2)

    with col1:
        level = st.selectbox(
            "Your Experience",
            DIFFICULTIES,
            key="studio_planner_level",
        )

    with col2:
        duration = st.selectbox(
            "Available Development Time",
            ["1 Week", "2 Weeks", "1 Month", "2 Months", "3 Months", "Flexible"],
            key="studio_planner_duration",
        )

    if st.button(
        "🧠 Create Project Roadmap",
        type="primary",
        key="studio_create_plan",
    ):
        if not title.strip() or not description.strip():
            st.warning("Project name aur description dono enter karo.")
        else:
            prompt = f"""
Act as a senior software architect and technical project manager.

Create a complete implementation plan for this project.

Project: {title}
Description: {description}
Developer experience: {level}
Available time: {duration}

Include:

1. Project overview
2. Problem and solution
3. Recommended architecture
4. Technology stack with reasons
5. Complete folder structure
6. Module-wise responsibilities
7. Database design, if required
8. API design, if required
9. Development milestones
10. Step-by-step implementation roadmap
11. Testing strategy
12. Deployment process
13. Security considerations
14. Future improvements

Keep the roadmap beginner-friendly where appropriate.
Provide practical steps, not vague advice.
"""

            with st.spinner("Creating your project roadmap..."):
                result = generate_response(generate_ai_response, prompt)

            if result:
                st.session_state.studio_project_plan = result

    if st.session_state.get("studio_project_plan"):
        st.markdown("---")
        st.markdown(st.session_state.studio_project_plan)


def render_project_mentor(generate_ai_response):
    st.subheader("👨‍💻 AI Project Mentor")
    st.write(
        "Get coding guidance, debugging help, code explanations and testing suggestions."
    )

    project_context = st.text_input(
        "Project Context",
        placeholder="Example: AI Resume Analyzer built with Streamlit",
        key="studio_mentor_context",
    )

    task = st.selectbox(
        "What do you need help with?",
        [
            "Explain a programming concept",
            "Write or improve code",
            "Debug an error",
            "Review my code",
            "Create test cases",
            "Improve project architecture",
            "Deployment guidance",
        ],
        key="studio_mentor_task",
    )

    question = st.text_area(
        "Describe your problem or question",
        height=130,
        key="studio_mentor_question",
    )

    code = st.text_area(
        "Paste your code or error message (optional)",
        height=180,
        key="studio_mentor_code",
    )

    if st.button(
        "💬 Ask AI Mentor",
        type="primary",
        key="studio_ask_mentor",
    ):
        if not question.strip():
            st.warning("Please enter your question first.")
        else:
            prompt = f"""
Act as a senior software developer and patient technical mentor.

Project context: {project_context or "Not provided"}
Requested help: {task}
User question: {question}

Code or error:
{code or "Not provided"}

Give a practical and technically accurate response.

When writing code:
- Provide complete code for the relevant solution.
- Mention the file name where it belongs.
- Explain important changes.
- Mention required dependencies.
- Include testing steps.
- Do not invent project files or functions.
- Clearly state any assumptions.
"""

            with st.spinner("Your AI mentor is working..."):
                result = generate_response(generate_ai_response, prompt)

            if result:
                st.session_state.studio_mentor_response = result

    if st.session_state.get("studio_mentor_response"):
        st.markdown("---")
        st.markdown(st.session_state.studio_mentor_response)


def render_project_showcase():
    st.subheader("📁 Project Showcase")
    st.write(
        "Save your projects, track development progress and maintain your portfolio."
    )

    projects = load_projects()

    with st.expander("➕ Add New Project", expanded=not projects):
        with st.form("studio_add_project_form"):
            title = st.text_input("Project Name")
            category = st.selectbox("Category", CATEGORIES)
            description = st.text_area("Project Description")
            github = st.text_input("GitHub Repository URL")
            demo = st.text_input("Live Demo URL")
            status = st.selectbox("Current Status", PROJECT_STATUSES)
            progress = st.slider("Progress", 0, 100, 0)

            submitted = st.form_submit_button(
                "Save Project",
                type="primary",
            )

            if submitted:
                if not title.strip():
                    st.error("Project name is required.")
                else:
                    projects.append(
                        {
                            "id": str(uuid.uuid4()),
                            "title": title.strip(),
                            "category": category,
                            "description": description.strip(),
                            "github": github.strip(),
                            "demo": demo.strip(),
                            "status": status,
                            "progress": progress,
                        }
                    )
                    save_projects(projects)
                    st.success("Project saved successfully!")
                    st.rerun()

    if not projects:
        st.info("Abhi koi project save nahi hai. Add New Project se shuru karo.")
        return

    st.markdown("---")

    completed = sum(
        1 for project in projects
        if project.get("status") == "Completed"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Projects", len(projects))
    col2.metric("Completed", completed)
    col3.metric("In Progress", sum(
        1 for project in projects
        if project.get("status") == "In Progress"
    ))

    for project in projects:
        with st.expander(f"📌 {project.get('title', 'Untitled Project')}"):
            st.write(project.get("description", ""))
            st.caption(f"Category: {project.get('category', 'N/A')}")

            new_status = st.selectbox(
                "Project Status",
                PROJECT_STATUSES,
                index=(
                    PROJECT_STATUSES.index(project["status"])
                    if project.get("status") in PROJECT_STATUSES
                    else 0
                ),
                key=f"studio_status_{project['id']}",
            )

            new_progress = st.slider(
                "Development Progress",
                0,
                100,
                int(project.get("progress", 0)),
                key=f"studio_progress_{project['id']}",
            )

            if project.get("github"):
                st.markdown(f"[GitHub Repository]({project['github']})")

            if project.get("demo"):
                st.markdown(f"[Live Demo]({project['demo']})")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Update Project",
                    key=f"studio_update_{project['id']}",
                ):
                    project["status"] = new_status
                    project["progress"] = new_progress
                    save_projects(projects)
                    st.success("Project updated.")
                    st.rerun()

            with col2:
                if st.button(
                    "Delete Project",
                    key=f"studio_delete_{project['id']}",
                ):
                    projects = [
                        item for item in projects
                        if item.get("id") != project["id"]
                    ]
                    save_projects(projects)
                    st.rerun()


def render_project_studio(generate_ai_response):
    st.markdown(
        """
        <div style="
            padding: 24px;
            border-radius: 14px;
            background: linear-gradient(120deg, #14213d, #263f73);
            color: white;
            margin-bottom: 22px;
        ">
            <h2 style="margin: 0;">🚀 AI Project Studio</h2>
            <p style="margin: 8px 0 0 0;">
                Generate ideas, plan architecture, solve coding problems
                and build your project portfolio.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    idea_tab, planner_tab, mentor_tab, showcase_tab = st.tabs(
        [
            "💡 Ideas Generator",
            "🗺️ Project Planner",
            "👨‍💻 AI Mentor",
            "📁 Project Showcase",
        ]
    )

    with idea_tab:
        render_ideas_generator(generate_ai_response)

    with planner_tab:
        render_project_planner(generate_ai_response)

    with mentor_tab:
        render_project_mentor(generate_ai_response)

    with showcase_tab:
        render_project_showcase()
