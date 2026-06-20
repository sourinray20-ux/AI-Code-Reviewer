"""
AI Code Reviewer
-----------------
A Streamlit tool that sends code submissions to Gemini 3 Flash Preview
and returns structured, senior-developer-style feedback: bugs,
inefficiencies, best-practice violations, security concerns, and
concrete suggested fixes.

Run with:
    streamlit run app.py

API key:
    Set the GEMINI_API_KEY environment variable, or paste it into the
    sidebar field at runtime. The key is never written to disk or to
    this source file.
"""

import os
import datetime as dt

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env in the working directory into os.environ, if present

MODEL_NAME = "gemini-3-flash-preview"

LANGUAGES = [
    "Auto-detect", "Python", "JavaScript", "TypeScript", "Java", "C",
    "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "SQL",
    "HTML/CSS", "Shell/Bash", "Other",
]

EXT_TO_LANGUAGE = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++", ".cs": "C#",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".swift": "Swift", ".kt": "Kotlin", ".sql": "SQL",
    ".html": "HTML/CSS", ".css": "HTML/CSS", ".sh": "Shell/Bash",
}

FOCUS_AREAS = [
    "Bugs & correctness",
    "Performance & inefficiencies",
    "Best practices & style",
    "Security",
    "Readability & maintainability",
]


# --------------------------------------------------------------------------
# Prompt construction
# --------------------------------------------------------------------------

def build_prompt(code: str, language: str, context: str, focus_areas: list[str]) -> str:
    focus_text = "\n".join(f"- {f}" for f in focus_areas) if focus_areas else "- All standard review categories"

    context_block = f"\nAdditional context from the author about intent:\n{context.strip()}\n" if context.strip() else ""

    return f"""You are a pragmatic, experienced senior software engineer doing a thorough,
constructive code review for a colleague. Be direct and specific. Reference
line numbers or function/variable names where possible. Explain *why*
something is a problem, not just that it is one. Don't pad the review with
generic praise; only mention what's genuinely good if it's worth noting.

Language: {language}
{context_block}
Focus areas requested:
{focus_text}

Review the following code submission and respond in clean Markdown using
exactly this structure:

## Summary
2-4 sentences on overall code quality and the most important takeaway.

## Bugs & Correctness Issues
For each issue: **[Severity: Critical/High/Medium/Low]** description, location,
why it's a problem, and a concrete fix (small code snippet if helpful).
If none found, say so explicitly.

## Performance & Inefficiencies
Same format as above, focused on algorithmic complexity, redundant work,
unnecessary allocations, blocking calls, etc.

## Best Practices & Style
Naming, structure, idioms for this language, error handling, documentation.

## Security Considerations
Injection risks, unsafe deserialization, secrets handling, input validation,
etc. State explicitly if nothing applies.

## Suggested Improvements
A short list of concrete, prioritized next edits. Include a revised code
snippet for the single most impactful fix.

## Overall Rating
A score out of 10 with a one-line justification.

Here is the code:

```{language.lower() if language != "Auto-detect" else ""}
{code}
```
"""


# --------------------------------------------------------------------------
# Gemini call
# --------------------------------------------------------------------------

def stream_review(api_key: str, prompt: str, thinking_level: str, temperature: float):
    """Generator yielding text chunks from Gemini 3 Flash Preview."""
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=temperature,
        thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
    )
    for chunk in client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    ):
        if chunk.text:
            yield chunk.text


# --------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------

st.set_page_config(page_title="AI Code Reviewer", page_icon="🧑‍💻", layout="wide")

st.markdown(
    """
    <style>
    .stTextArea textarea { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 0.9rem; }
    .review-meta { color: #888; font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: timestamp, language, code, review

# ---- Sidebar ----
with st.sidebar:
    st.header("⚙️ Settings")

    default_key = os.environ.get("GEMINI_API_KEY", "")
    if default_key:
        st.success("API key loaded from .env")
        with st.expander("Override key for this session"):
            override_key = st.text_input("Gemini API key", type="password", value="")
        api_key = override_key or default_key
    else:
        st.warning("No GEMINI_API_KEY found in .env")
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            help="Add GEMINI_API_KEY to a .env file next to app.py to skip this field permanently.",
        )

    st.caption(f"Model: `{MODEL_NAME}`")

    thinking_level = st.selectbox(
        "Review depth (thinking level)",
        options=["high", "low"],
        index=0,
        help="High = more thorough reasoning, slower. Low = faster, lighter review.",
    )

    temperature = st.slider(
        "Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.05,
        help="Lower = more consistent/focused feedback. Higher = more exploratory.",
    )

    focus_areas = st.multiselect(
        "Focus areas", options=FOCUS_AREAS, default=FOCUS_AREAS,
    )

    st.divider()
    if st.session_state.history:
        st.caption(f"{len(st.session_state.history)} review(s) this session")
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()

# ---- Main area ----
st.title("🧑‍💻 AI Code Reviewer")
st.caption("Paste code or upload a file. Get senior-developer-style feedback on bugs, inefficiencies, and best practices — powered by Gemini 3 Flash Preview.")

col_input, col_settings = st.columns([3, 1])

with col_input:
    uploaded = st.file_uploader(
        "Upload a code file (optional)",
        type=None,
        accept_multiple_files=False,
    )

    initial_code = ""
    detected_language = "Auto-detect"
    if uploaded is not None:
        try:
            initial_code = uploaded.read().decode("utf-8")
        except UnicodeDecodeError:
            st.error("Couldn't read that file as text. Please upload a plain-text source file.")
        ext = os.path.splitext(uploaded.name)[1].lower()
        detected_language = EXT_TO_LANGUAGE.get(ext, "Auto-detect")

    code = st.text_area(
        "Code to review",
        value=initial_code,
        height=400,
        placeholder="Paste your code here...",
    )

with col_settings:
    language = st.selectbox(
        "Language",
        options=LANGUAGES,
        index=LANGUAGES.index(detected_language) if detected_language in LANGUAGES else 0,
    )
    context = st.text_area(
        "What should this code do? (optional)",
        height=120,
        placeholder="e.g. parses a CSV and dedupes rows by user_id",
    )

run = st.button("🔍 Review my code", type="primary", use_container_width=True)

if run:
    if not api_key:
        st.error("Add your Gemini API key in the sidebar (or set GEMINI_API_KEY) before running a review.")
    elif not code.strip():
        st.error("Paste some code or upload a file first.")
    else:
        prompt = build_prompt(code, language, context, focus_areas)
        st.subheader("Review")
        try:
            full_text = st.write_stream(
                stream_review(api_key, prompt, thinking_level, temperature)
            )
            st.session_state.history.insert(0, {
                "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "language": language,
                "code": code,
                "review": full_text,
            })
            st.download_button(
                "Download this review as Markdown",
                data=full_text,
                file_name="code_review.md",
                mime="text/markdown",
            )
        except Exception as e:
            msg = str(e)
            st.error(f"Review failed: {msg}")
            if "API key" in msg or "401" in msg or "PERMISSION" in msg.upper():
                st.info("Double-check the API key in the sidebar — it may be invalid, expired, or missing access to this model.")
            elif "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper():
                st.info("You may have hit a rate limit or quota. Wait a moment and try again.")

# ---- History ----
if st.session_state.history:
    st.divider()
    st.subheader("📜 Past reviews (this session)")
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{item['timestamp']} — {item['language']}"):
            st.markdown(f"<span class='review-meta'>Code length: {len(item['code'])} chars</span>", unsafe_allow_html=True)
            st.markdown(item["review"])