
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from database import create_tables, get_connection
from retention import get_revision_days, get_retention_status


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="LearnLyt",
    page_icon="📚",
    layout="wide"
)

create_tables()

st.markdown("""
<style>
.stApp {
    background-color: #f5f7fb;
}
[data-testid="stSidebar"] {
    background-color: #172554;
}
[data-testid="stSidebar"] * {
    color: white;
}
h1, h2, h3 {
    color: #172554;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

st.sidebar.title("📚 LearnLyt")
st.sidebar.caption("Knowledge Retention System")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Subjects",
        "Quiz",
        "Retention Analysis",
        "Revision"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("LearnLyt | Version 2.0")


# ---------------- FETCH DATA ----------------

conn = get_connection()

subjects = pd.read_sql_query(
    "SELECT * FROM subjects", conn
)

topics = pd.read_sql_query(
    """
    SELECT topics.id, topics.subject_id, topics.name,
           subjects.name AS subject_name
    FROM topics
    JOIN subjects ON topics.subject_id = subjects.id
    """,
    conn
)

results = pd.read_sql_query(
    """
    SELECT quiz_results.*, topics.name AS topic_name
    FROM quiz_results
    JOIN topics ON quiz_results.topic_id = topics.id
    ORDER BY quiz_results.id
    """,
    conn
)

revisions = pd.read_sql_query(
    """
    SELECT revision_schedule.*, topics.name AS topic_name
    FROM revision_schedule
    JOIN topics ON revision_schedule.topic_id = topics.id
    ORDER BY revision_schedule.id DESC
    """,
    conn
)

conn.close()


# ==================================================
# DASHBOARD
# ==================================================

if menu == "Dashboard":

    st.title("📊 LearnLyt Dashboard")
    st.write("Monitor your learning progress and knowledge retention.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Subjects", len(subjects))
    col2.metric("Topics", len(topics))
    col3.metric("Quizzes Attempted", len(results))

    average = (
        round(results["score"].mean(), 2)
        if not results.empty else 0
    )

    col4.metric("Average Score", f"{average}%")

    st.subheader("Recent Quiz Performance")

    if not results.empty:
        chart = px.line(
            results,
            x="id",
            y="score",
            markers=True,
            title="Quiz Score History",
            labels={"id": "Quiz Attempt", "score": "Score (%)"}
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Attempt a quiz to see your performance.")

    st.subheader("Learning Overview")

    if not topics.empty:
        st.dataframe(
            topics[["subject_name", "name"]],
            use_container_width=True
        )
    else:
        st.info("Add subjects and topics to get started.")


# ==================================================
# SUBJECTS
# ==================================================

elif menu == "Subjects":

    st.title("📚 Subject and Topic Management")

    st.subheader("Add Subject")

    with st.form("subject_form"):
        subject_name = st.text_input("Subject Name")
        add_subject = st.form_submit_button("Add Subject")

        if add_subject:
            if subject_name.strip():
                conn = get_connection()
                conn.execute(
                    "INSERT INTO subjects (name) VALUES (?)",
                    (subject_name.strip(),)
                )
                conn.commit()
                conn.close()

                st.success("Subject added successfully!")
                st.rerun()
            else:
                st.warning("Enter a subject name.")

    st.divider()
    st.subheader("Add Topic")

    if not subjects.empty:

        subject_options = {
            row["name"]: row["id"]
            for _, row in subjects.iterrows()
        }

        with st.form("topic_form"):
            selected_subject = st.selectbox(
                "Select Subject",
                list(subject_options.keys())
            )

            topic_name = st.text_input("Topic Name")
            add_topic = st.form_submit_button("Add Topic")

            if add_topic:
                if topic_name.strip():
                    conn = get_connection()
                    conn.execute(
                        """
                        INSERT INTO topics (subject_id, name)
                        VALUES (?, ?)
                        """,
                        (
                            int(subject_options[selected_subject]),
                            topic_name.strip()
                        )
                    )
                    conn.commit()
                    conn.close()

                    st.success("Topic added successfully!")
                    st.rerun()
                else:
                    st.warning("Enter a topic name.")

    else:
        st.info("Add a subject before adding topics.")

    st.divider()
    st.subheader("Available Subjects and Topics")

    if not topics.empty:
        st.dataframe(
            topics[["subject_name", "name"]],
            use_container_width=True
        )
    else:
        st.info("No topics available.")


# ==================================================
# QUIZ
# ==================================================

elif menu == "Quiz":

    st.title("📝 Knowledge Assessment Quiz")

    if topics.empty:
        st.warning("First add a subject and topic.")
    else:

        topic_options = {
            f"{row['subject_name']} - {row['name']}": row["id"]
            for _, row in topics.iterrows()
        }

        selected_topic = st.selectbox(
            "Select Topic",
            list(topic_options.keys())
        )

        topic_id = topic_options[selected_topic]

        # ADD QUESTIONS

        with st.expander("➕ Add Quiz Questions"):

            with st.form("add_question_form"):

                question = st.text_input("Question")

                option_a = st.text_input("Option A")
                option_b = st.text_input("Option B")
                option_c = st.text_input("Option C")
                option_d = st.text_input("Option D")

                correct_answer = st.selectbox(
                    "Correct Answer",
                    ["A", "B", "C", "D"]
                )

                explanation = st.text_area("Explanation")

                add_question = st.form_submit_button(
                    "Save Question"
                )

                if add_question:

                    if all([
                        question.strip(),
                        option_a.strip(),
                        option_b.strip(),
                        option_c.strip(),
                        option_d.strip()
                    ]):

                        conn = get_connection()

                        conn.execute(
                            """
                            INSERT INTO quiz_questions
                            (topic_id, question, option_a, option_b,
                             option_c, option_d, correct_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                int(topic_id),
                                question.strip(),
                                option_a.strip(),
                                option_b.strip(),
                                option_c.strip(),
                                option_d.strip(),
                                correct_answer,
                                explanation.strip()
                            )
                        )

                        conn.commit()
                        conn.close()

                        st.success("Question added successfully!")
                        st.rerun()

                    else:
                        st.warning("Fill in all question and option fields.")

        # LOAD QUESTIONS

        conn = get_connection()

        questions = pd.read_sql_query(
            """
            SELECT * FROM quiz_questions
            WHERE topic_id = ?
            ORDER BY id
            """,
            conn,
            params=(int(topic_id),)
        )

        conn.close()

        # DELETE QUESTIONS

        with st.expander("🗑️ Delete Quiz Questions"):

            if questions.empty:
                st.info("No questions available to delete.")

            else:

                question_ids = questions["id"].tolist()

                question_id = st.selectbox(
                    "Select question to delete",
                    question_ids,
                    format_func=lambda x: questions.loc[
                        questions["id"] == x, "question"
                    ].iloc[0],
                    key="delete_question"
                )

                if st.button("Delete Selected Question"):

                    conn = get_connection()

                    conn.execute(
                        "DELETE FROM quiz_questions WHERE id = ?",
                        (int(question_id),)
                    )

                    conn.commit()
                    conn.close()

                    st.success("Question deleted successfully!")
                    st.rerun()

        # ATTEMPT QUIZ

        st.subheader("Attempt Your Quiz")

        if questions.empty:

            st.info("No questions available. Add questions first.")

        else:

            with st.form("quiz_form"):

                answers = {}

                for _, q in questions.iterrows():

                    st.markdown(f"**{q['question']}**")

                    options = {
                        "A": q["option_a"],
                        "B": q["option_b"],
                        "C": q["option_c"],
                        "D": q["option_d"]
                    }

                    selected_answer = st.radio(
                        "Choose your answer",
                        ["A", "B", "C", "D"],
                        format_func=lambda x: f"{x}. {options[x]}",
                        key=f"quiz_{q['id']}"
                    )

                    answers[int(q["id"])] = selected_answer

                    st.divider()

                submit_quiz = st.form_submit_button("Submit Quiz")

            if submit_quiz:

                correct = 0

                for _, q in questions.iterrows():

                    if answers[int(q["id"])] == q["correct_answer"]:
                        correct += 1

                total = len(questions)
                score = round((correct / total) * 100, 2)

                conn = get_connection()

                previous = conn.execute(
                    """
                    SELECT score FROM quiz_results
                    WHERE topic_id = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (int(topic_id),)
                ).fetchone()

                previous_score = previous[0] if previous else None

                days = get_revision_days(score, previous_score)
                status = get_retention_status(score)

                next_date = date.today() + timedelta(days=days)

                conn.execute(
                    """
                    INSERT INTO quiz_results
                    (topic_id, score, correct_answers, total_questions, date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        int(topic_id),
                        score,
                        correct,
                        total,
                        str(date.today())
                    )
                )

                conn.execute(
                    """
                    INSERT INTO revision_schedule
                    (topic_id, next_revision, status)
                    VALUES (?, ?, ?)
                    """,
                    (
                        int(topic_id),
                        str(next_date),
                        "Pending"
                    )
                )

                conn.commit()
                conn.close()

                st.session_state["last_quiz"] = {
                    "score": score,
                    "correct": correct,
                    "total": total,
                    "days": days,
                    "date": next_date,
                    "status": status
                }

                st.rerun()

        if "last_quiz" in st.session_state:

            quiz = st.session_state["last_quiz"]

            st.divider()
            st.subheader("Latest Quiz Result")

            c1, c2, c3 = st.columns(3)

            c1.metric("Score", f"{quiz['score']}%")
            c2.metric(
                "Correct Answers",
                f"{quiz['correct']}/{quiz['total']}"
            )
            c3.metric("Retention Status", quiz["status"])

            st.success(
                f"Your next revision is scheduled for "
                f"{quiz['date']} (in {quiz['days']} days)."
            )


# ==================================================
# RETENTION ANALYSIS
# ==================================================

elif menu == "Retention Analysis":

    st.title("📈 Retention Analysis")

    if results.empty:

        st.info("Attempt quizzes to view retention analysis.")

    else:

        average = round(results["score"].mean(), 2)

        st.metric("Overall Average Score", f"{average}%")

        st.subheader("Quiz Performance History")

        st.dataframe(
            results[["topic_name", "score", "date"]],
            use_container_width=True
        )

        st.subheader("Average Score by Topic")

        topic_average = (
            results.groupby("topic_name")["score"]
            .mean()
            .reset_index()
        )

        chart = px.bar(
            topic_average,
            x="topic_name",
            y="score",
            color="score",
            title="Topic-wise Retention Performance",
            labels={
                "topic_name": "Topic",
                "score": "Average Score (%)"
            }
        )

        st.plotly_chart(chart, use_container_width=True)

        st.subheader("Topics That Need Improvement")

        weak_topics = topic_average[
            topic_average["score"] < 60
        ]

        if not weak_topics.empty:
            st.dataframe(
                weak_topics,
                use_container_width=True
            )
        else:
            st.success("No topics currently below 60%.")


# ==================================================
# REVISION SCHEDULER
# ==================================================

elif menu == "Revision":

    st.title("📅 Adaptive Revision Scheduler")

    if revisions.empty:

        st.info("No revision schedules available. Attempt a quiz first.")

    else:

        st.subheader("All Revision Records")

        st.dataframe(
            revisions[
                ["topic_name", "next_revision", "status"]
            ],
            use_container_width=True
        )

        st.divider()
        st.subheader("Due Revisions")

        due_revisions = revisions[
            (revisions["status"] == "Pending") &
            (revisions["next_revision"] <= str(date.today()))
        ]

        if due_revisions.empty:

            st.success("No pending revisions are due today.")

        else:

            for _, revision in due_revisions.iterrows():

                st.write(
                    f"📘 **{revision['topic_name']}** "
                    f"- Due: {revision['next_revision']}"
                )

                if st.button(
                    "Mark as Completed",
                    key=f"complete_{revision['id']}"
                ):

                    conn = get_connection()

                    conn.execute(
                        """
                        UPDATE revision_schedule
                        SET status = 'Completed'
                        WHERE id = ?
                        """,
                        (int(revision["id"]),)
                    )

                    conn.commit()
                    conn.close()

                    st.success("Revision marked as completed!")
                    st.rerun()

    st.divider()

    st.caption(
        "LearnLyt schedules revision based on quiz performance "
        "using a rule-based adaptive algorithm."
    )
