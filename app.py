"""
AI Teacher
----------
Upload a PDF of study material, have an LLM generate multiple-choice
questions from it, take the quiz right in the app, and get your score
plus explanations for every answer.
"""

import json
import os

import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

st.set_page_config(page_title="AI Teacher", page_icon="📚", layout="centered")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_model():
    """Build a Gemini model from an API key in env var or sidebar input."""
    api_key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def extract_text_from_pdf(uploaded_file) -> str:
    """Pull all readable text out of an uploaded PDF file."""
    reader = PdfReader(uploaded_file)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def generate_quiz(model, study_text: str, num_questions: int) -> list[dict]:
    """
    Ask the LLM to generate MCQs from the study text.
    Returns a list of dicts: {question, options, correct_index, explanation}
    """
    # Keep the prompt within a safe size; truncate very long documents.
    max_chars = 12000
    trimmed_text = study_text[:max_chars]

    prompt = f"""
You are an expert teacher who writes exam-quality multiple choice questions
strictly based on the study material given to you. Do not invent facts that
are not supported by the material.

Study material:
\"\"\"
{trimmed_text}
\"\"\"

Create exactly {num_questions} multiple choice questions based ONLY on the
study material above. For each question, provide exactly 4 options.

Respond with ONLY valid JSON (no markdown fences, no extra text) in this
exact shape:

{{
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_index": 0,
      "explanation": "string explaining why the correct option is right"
    }}
  ]
}}
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.4},
    )

    raw_content = response.text.strip()

    # Be defensive: strip markdown code fences if the model adds them anyway.
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        if raw_content.lower().startswith("json"):
            raw_content = raw_content[4:].strip()

    parsed = json.loads(raw_content)
    return parsed["questions"]


# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "answers" not in st.session_state:
    st.session_state.answers = {}

# ---------------------------------------------------------------------------
# Sidebar: API key + settings
# ---------------------------------------------------------------------------

st.sidebar.header("Settings")

if not os.environ.get("GOOGLE_API_KEY"):
    st.session_state.api_key = st.sidebar.text_input(
        "Google Gemini API key", type="password",
        help="Get a free one at aistudio.google.com. Not saved anywhere, only used for this session.",
    )
else:
    st.sidebar.success("API key loaded from environment.")

num_questions = st.sidebar.slider("Number of questions", min_value=3, max_value=15, value=5)

if st.sidebar.button("🔄 Start over"):
    st.session_state.quiz = None
    st.session_state.submitted = False
    st.session_state.answers = {}
    st.rerun()

# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

st.title("📚 AI Teacher")
st.caption("Upload your study material as a PDF and get quizzed on it.")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file and st.session_state.quiz is None:
    if st.button("Generate Quiz", type="primary"):
        model = get_model()
        if model is None:
            st.error("Please enter your Google Gemini API key in the sidebar first.")
        else:
            with st.spinner("Reading your PDF and writing questions..."):
                try:
                    study_text = extract_text_from_pdf(uploaded_file)
                    if not study_text:
                        st.error(
                            "Couldn't extract any text from this PDF. "
                            "It might be a scanned/image-only PDF."
                        )
                    else:
                        st.session_state.quiz = generate_quiz(
                            model, study_text, num_questions
                        )
                        st.session_state.submitted = False
                        st.session_state.answers = {}
                except Exception as exc:  # noqa: BLE001 - show any failure to the user
                    st.error(f"Something went wrong generating the quiz: {exc}")

# ---------------------------------------------------------------------------
# Quiz display
# ---------------------------------------------------------------------------

if st.session_state.quiz:
    st.divider()
    st.subheader("Test time!")

    for idx, q in enumerate(st.session_state.quiz):
        st.markdown(f"**Q{idx + 1}. {q['question']}**")
        choice = st.radio(
            label=f"question_{idx}",
            options=list(range(len(q["options"]))),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"radio_{idx}",
            index=None,
            label_visibility="collapsed",
        )
        st.session_state.answers[idx] = choice
        st.write("")

    if not st.session_state.submitted:
        if st.button("Submit test", type="primary"):
            st.session_state.submitted = True
            st.rerun()

    if st.session_state.submitted:
        st.divider()
        st.subheader("Results")

        score = 0
        total = len(st.session_state.quiz)

        for idx, q in enumerate(st.session_state.quiz):
            user_choice = st.session_state.answers.get(idx)
            correct_choice = q["correct_index"]
            is_correct = user_choice == correct_choice
            if is_correct:
                score += 1

            with st.container(border=True):
                st.markdown(f"**Q{idx + 1}. {q['question']}**")
                if user_choice is None:
                    st.write("You did not answer this question.")
                else:
                    st.write(f"Your answer: {q['options'][user_choice]}")
                st.write(f"Correct answer: {q['options'][correct_choice]}")
                if is_correct:
                    st.success("Correct!")
                else:
                    st.error("Incorrect")
                st.caption(f"Explanation: {q['explanation']}")

        st.divider()
        st.metric("Total score", f"{score} / {total}")
       
