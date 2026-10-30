import streamlit as st
import logging
from database.db import init_db
from database import operations as db_ops
from chains import teaching_chain, scenario_chain, evaluation_chain
from chains.llm import LLMConnectionError, mask_api_key
from utils.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    LANGSMITH_TRACING,
    validate_openrouter_config,
    validate_langsmith_config,
)
from utils.validators import validate_topic, validate_difficulty, validate_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Technical Learning Mentor",
    page_icon="🎓",
    layout="wide",
)

# Initialize database once
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Session state defaults
for key, default in {
    "current_session_id": None,
    "topic": "",
    "difficulty": "beginner",
    "explanation": "",
    "scenario": "",
    "answer": "",
    "evaluation": None,
    "step": "topic",  # topic -> scenario -> answer -> evaluation
    "active_page": "Dashboard",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def show_config_warnings():
    errors = validate_openrouter_config()
    warnings = validate_langsmith_config()
    if errors:
        for e in errors:
            st.error(f"Configuration: {e}")
        st.info("Add your OPENROUTER_API_KEY to the .env file, then restart the app.")
        return False
    if warnings:
        for w in warnings:
            st.warning(w)
    return True


def render_sidebar():
    st.sidebar.title("🎓 AI Technical Mentor")
    st.sidebar.markdown("---")

    pages = [
        "Dashboard",
        "Learn a Topic",
        "Practice Scenario",
        "Evaluate My Answer",
        "Learning History",
        "Progress Dashboard",
        "About Project",
    ]

    for page in pages:
        if st.sidebar.button(page, use_container_width=True, key=f"nav_{page}"):
            st.session_state.active_page = page

    st.sidebar.markdown("---")
    st.sidebar.subheader("Configuration")
    st.sidebar.text(f"Model: {OPENROUTER_MODEL}")
    st.sidebar.text(f"API Key: {mask_api_key(OPENROUTER_API_KEY)}")
    st.sidebar.text(f"LangSmith: {'ON' if LANGSMITH_TRACING else 'OFF'}")
    st.sidebar.markdown("---")
    if st.sidebar.button("Start New Session", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.topic = ""
        st.session_state.explanation = ""
        st.session_state.scenario = ""
        st.session_state.answer = ""
        st.session_state.evaluation = None
        st.session_state.step = "topic"
        st.rerun()


def render_dashboard():
    st.title("🎓 AI Technical Learning Mentor")
    st.markdown("Your personal AI-powered technical learning companion.")
    st.markdown("---")

    config_ok = show_config_warnings()
    if not config_ok:
        return

    st.subheader("Welcome!")
    st.write(
        "This mentor guides you through a structured learning process: "
        "**Learn a concept → Apply it to a scenario → Explain your answer → Get feedback.**"
    )

    st.subheader("Quick Start")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1. Learn a Topic", use_container_width=True):
            st.session_state.active_page = "Learn a Topic"
            st.rerun()
    with col2:
        if st.button("2. View History", use_container_width=True):
            st.session_state.active_page = "Learning History"
            st.rerun()
    with col3:
        if st.button("3. Check Progress", use_container_width=True):
            st.session_state.active_page = "Progress Dashboard"
            st.rerun()

    st.markdown("---")
    st.subheader("Recent Sessions")
    sessions = db_ops.get_all_sessions()
    if not sessions:
        st.info("No learning sessions yet. Start by learning a topic!")
    else:
        for s in sessions[:5]:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.write(f"**{s['topic']}**")
                    st.caption(f"Difficulty: {s['difficulty']} • Status: {s['status']}")
                with c2:
                    st.write(f"Created: {s['created_at'][:16]}")
                with c3:
                    if s["total_score"] is not None:
                        st.metric("Score", f"{s['total_score']}/10")
                    else:
                        st.write("Not evaluated yet")
                if st.button("Open", key=f"open_{s['id']}"):
                    st.session_state.current_session_id = s["id"]
                    st.session_state.active_page = "Learning History"
                    st.rerun()
                st.divider()


def render_learn_topic():
    st.title("📚 Learn a Topic")
    show_config_warnings()

    st.subheader("Step 1: Choose a Technical Topic")
    topic = st.text_input(
        "Enter any technical topic you want to learn:",
        value=st.session_state.topic,
        placeholder="e.g. LangChain, RAG, Model Context Protocol, Python",
    )

    difficulty = st.selectbox(
        "Select difficulty level:",
        options=["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(st.session_state.difficulty),
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        generate_btn = st.button("Generate Explanation", type="primary", use_container_width=True)
    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.topic = ""
            st.session_state.explanation = ""
            st.session_state.scenario = ""
            st.session_state.answer = ""
            st.session_state.evaluation = None
            st.session_state.step = "topic"
            st.session_state.current_session_id = None
            st.rerun()

    if generate_btn:
        if not topic.strip():
            st.error("Please enter a topic.")
            return
        try:
            validate_topic(topic)
            validate_difficulty(difficulty)
            st.session_state.topic = topic.strip()
            st.session_state.difficulty = difficulty

            with st.spinner("AI is preparing your lesson..."):
                explanation = teaching_chain.run_teaching_chain(st.session_state.topic)
            st.session_state.explanation = explanation

            # Create session in DB
            session_id = db_ops.create_session(st.session_state.topic, st.session_state.difficulty)
            st.session_state.current_session_id = session_id
            db_ops.save_topic_explanation(session_id, explanation)

            st.session_state.step = "scenario"
            st.rerun()
        except LLMConnectionError as exc:
            st.error(str(exc))
        except Exception as exc:
            logger.exception("Learn topic error")
            st.error(f"Unexpected error: {exc}")

    if st.session_state.explanation:
        st.markdown("---")
        st.subheader(f"Topic: {st.session_state.topic}")
        st.markdown(st.session_state.explanation)

        st.markdown("---")
        st.subheader("Step 2: Generate a Practical Scenario")
        st.write("Now let's apply what you learned to a real-world scenario.")

        if st.button("Generate Scenario", type="primary", use_container_width=True):
            with st.spinner("AI is creating your scenario..."):
                scenario = scenario_chain.run_scenario_chain(
                    st.session_state.topic,
                    st.session_state.explanation,
                    st.session_state.difficulty,
                )
            st.session_state.scenario = scenario
            if st.session_state.current_session_id:
                db_ops.save_scenario(
                    st.session_state.current_session_id,
                    "Practical Scenario",
                    scenario,
                    st.session_state.difficulty,
                )
            st.session_state.step = "answer"
            st.rerun()


def render_scenario():
    st.title("🎯 Practice Scenario")
    show_config_warnings()

    if not st.session_state.explanation:
        st.info("Please learn a topic first.")
        if st.button("Go to Learn a Topic"):
            st.session_state.active_page = "Learn a Topic"
            st.rerun()
        return

    st.subheader(f"Topic: {st.session_state.topic}")
    st.markdown("### Your Scenario")
    st.markdown(st.session_state.scenario)

    st.markdown("---")
    st.subheader("Step 3: Submit Your Answer")
    st.write("Explain how you would solve this scenario. Take your time!")

    answer = st.text_area(
        "Your answer:",
        value=st.session_state.answer,
        height=300,
        placeholder="Describe your approach, architecture, and reasoning...",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        submit_btn = st.button("Submit for Evaluation", type="primary", use_container_width=True)
    with col2:
        if st.button("Regenerate Scenario", use_container_width=True):
            st.session_state.scenario = ""
            st.rerun()

    if submit_btn:
        if not answer.strip():
            st.error("Please write your answer before submitting.")
            return
        try:
            validate_answer(answer)
            st.session_state.answer = answer.strip()
            if st.session_state.current_session_id:
                db_ops.save_student_answer(st.session_state.current_session_id, answer.strip())
            st.session_state.step = "evaluation"
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_evaluation():
    st.title("📊 Evaluate My Answer")
    show_config_warnings()

    if not st.session_state.scenario or not st.session_state.answer:
        st.info("Please complete the scenario and submit an answer first.")
        if st.button("Go to Practice Scenario"):
            st.session_state.active_page = "Practice Scenario"
            st.rerun()
        return

    st.subheader(f"Topic: {st.session_state.topic}")
    st.markdown("### Scenario")
    st.info(st.session_state.scenario)
    st.markdown("### Your Answer")
    st.write(st.session_state.answer)

    st.markdown("---")

    if st.session_state.evaluation is None:
        if st.button("Get AI Evaluation", type="primary", use_container_width=True):
            try:
                with st.spinner("AI is evaluating your answer..."):
                    result = evaluation_chain.run_evaluation_chain(
                        st.session_state.topic,
                        st.session_state.scenario,
                        st.session_state.answer,
                    )
                st.session_state.evaluation = result.to_dict()

                # Generate recommendations
                recs = evaluation_chain.generate_recommendations(
                    st.session_state.topic, st.session_state.evaluation
                )
                st.session_state.evaluation["recommendations_text"] = recs

                if st.session_state.current_session_id:
                    db_ops.save_evaluation(
                        st.session_state.current_session_id,
                        st.session_state.evaluation["total_score"],
                        st.session_state.evaluation["technical_score"],
                        st.session_state.evaluation["conceptual_score"],
                        st.session_state.evaluation["practical_score"],
                        st.session_state.evaluation["strengths"],
                        st.session_state.evaluation["weaknesses"],
                        st.session_state.evaluation["missing_concepts"],
                        st.session_state.evaluation["corrected_explanation"],
                        st.session_state.evaluation["suggested_answer"],
                        st.session_state.evaluation["recommendations"],
                    )
                st.rerun()
            except LLMConnectionError as exc:
                st.error(str(exc))
            except Exception as exc:
                logger.exception("Evaluation error")
                st.error(f"Unexpected error: {exc}")
    else:
        eval_data = st.session_state.evaluation
        st.subheader("Evaluation Results")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Score", f"{eval_data['total_score']} / 10")
        with col2:
            st.metric("Technical", f"{eval_data['technical_score']} / 10")
        with col3:
            st.metric("Conceptual", f"{eval_data['conceptual_score']} / 10")
        with col4:
            st.metric("Practical", f"{eval_data['practical_score']} / 10")

        st.progress(eval_data["total_score"] / 10.0)

        st.markdown("### Strengths")
        st.write(eval_data["strengths"])

        st.markdown("### Areas for Improvement")
        st.write(eval_data["weaknesses"])

        if eval_data.get("missing_concepts"):
            st.markdown("### Missing Concepts")
            st.write(eval_data["missing_concepts"])

        st.markdown("### Corrected Explanation")
        st.info(eval_data["corrected_explanation"])

        st.markdown("### Suggested Improved Answer")
        st.write(eval_data["suggested_answer"])

        st.markdown("### Personalized Recommendations")
        st.write(eval_data.get("recommendations_text", eval_data.get("recommendations", "")))

        if st.button("Start New Topic", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.topic = ""
            st.session_state.explanation = ""
            st.session_state.scenario = ""
            st.session_state.answer = ""
            st.session_state.evaluation = None
            st.session_state.step = "topic"
            st.rerun()


def render_history():
    st.title("📜 Learning History")
    show_config_warnings()

    sessions = db_ops.get_all_sessions()
    if not sessions:
        st.info("No learning sessions yet. Start learning to build your history!")
        return

    st.write(f"Total sessions: {len(sessions)}")

    # Show current session detail if selected
    if st.session_state.current_session_id:
        detail = db_ops.get_session_details(st.session_state.current_session_id)
        if detail:
            st.markdown("---")
            st.subheader(f"Session: {detail['topic']}")
            st.write(f"Difficulty: {detail['difficulty']} | Status: {detail['status']}")
            st.write(f"Created: {detail['created_at'][:16]}")
            if detail.get("evaluation"):
                ev = detail["evaluation"]
                st.metric("Score", f"{ev['total_score']} / 10")
            if st.button("Back to list"):
                st.session_state.current_session_id = None
                st.rerun()
        return

    for s in sessions:
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1:
                st.write(f"**{s['topic']}**")
                st.caption(f"Difficulty: {s['difficulty']}")
            with c2:
                st.write(f"{s['created_at'][:16]}")
                st.caption(f"Status: {s['status']}")
            with c3:
                if s["total_score"] is not None:
                    st.metric("Score", f"{s['total_score']}/10")
                else:
                    st.write("Pending")
            with c4:
                if st.button("Open", key=f"hist_open_{s['id']}"):
                    st.session_state.current_session_id = s["id"]
                    st.rerun()
            st.divider()


def render_progress():
    st.title("📈 Progress Dashboard")
    show_config_warnings()

    stats = db_ops.get_progress_stats()

    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Sessions", stats["total_sessions"])
    with c2:
        st.metric("Completed", stats["completed"])
    with c3:
        st.metric("Average Score", f"{stats['avg_score']} / 10")
    with c4:
        st.metric("Highest Score", f"{stats['max_score']} / 10")

    st.markdown("---")

    if stats["total_sessions"] == 0:
        st.info("No learning data yet. Complete some sessions to see your progress!")
        return

    st.subheader("Topic-wise Performance")
    if stats["topic_performance"]:
        import pandas as pd
        df = pd.DataFrame(stats["topic_performance"])
        st.bar_chart(df.set_index("topic")["avg_score"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No evaluated topics yet.")

    st.subheader("Activity Over Time")
    if stats["activity_over_time"]:
        import pandas as pd
        df2 = pd.DataFrame(stats["activity_over_time"])
        st.line_chart(df2.set_index("day")["count"])
    else:
        st.info("No activity recorded yet.")


def render_about():
    st.title("ℹ️ About Project")
    st.markdown("""
    # AI Technical Learning Mentor

    A structured AI-powered learning platform that helps students master technical concepts
    through a guided process: **Learn → Apply → Answer → Evaluate → Improve**.

    ## How It Works
    1. **Learn a Topic** – AI generates a beginner-friendly explanation.
    2. **Practice Scenario** – AI creates a realistic technical scenario.
    3. **Submit Answer** – You explain your solution.
    4. **Evaluate** – AI scores your answer and gives feedback.
    5. **Recommendations** – Personalized next steps based on your results.

    ## Technology Stack
    - Python, LangChain, LangChain-OpenAI
    - OpenRouter API (LLM access)
    - Streamlit (frontend)
    - SQLite (data storage)
    - LangSmith (tracing and monitoring)
    - pytest (testing)

    ## Data Privacy
    Your API key is stored locally in `.env` and is never sent to GitHub or logged.
    Learning data is stored in a local SQLite database.
    """)


def main():
    render_sidebar()

    page = st.session_state.active_page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Learn a Topic":
        render_learn_topic()
    elif page == "Practice Scenario":
        render_scenario()
    elif page == "Evaluate My Answer":
        render_evaluation()
    elif page == "Learning History":
        render_history()
    elif page == "Progress Dashboard":
        render_progress()
    elif page == "About Project":
        render_about()


if __name__ == "__main__":
    main()
