"""
Tradie in trAIning — AI-aided study companion prototype
---------------------------------------------------------
Students upload their own course materials (PDF, Word, PowerPoint, text,
or images of diagrams/notes). Instead of handing over a ready-made answer,
the app breaks the material into checkpoint sections, asks guiding
questions, offers hints, and only reveals the full explanation once the
student has had a go — all grounded in their own uploaded material.

Run with:
    streamlit run app.py

Requires an Anthropic API key set as an environment variable:
    export ANTHROPIC_API_KEY="your-key-here"      (Mac/Linux)
    setx ANTHROPIC_API_KEY "your-key-here"         (Windows)
"""

import os
import io
import json
import base64
import time

import streamlit as st
import anthropic

import pdfplumber
import docx
from pptx import Presentation
from PIL import Image

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Tradie in trAIning", page_icon="🛠️", layout="centered")

MODEL = "claude-sonnet-4-5"  # swap to whichever model you have access to

@st.cache_resource
def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("No ANTHROPIC_API_KEY found. Set it as an environment variable before running.")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)

client = get_client()

IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}


# ---------------------------------------------------------------------------
# Resilient API wrapper — so a flaky connection or a rate limit doesn't
# crash the whole app mid-demo. Retries a couple of times with a short
# backoff, then fails gracefully with a message instead of a stack trace.
# ---------------------------------------------------------------------------

def call_claude(max_retries: int = 2, **kwargs):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(timeout=30.0, **kwargs)
        except anthropic.RateLimitError as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
        except anthropic.APIConnectionError as e:
            last_error = e
            time.sleep(1.5 * (attempt + 1))
        except anthropic.APIStatusError as e:
            last_error = e
            break  # server-side error, retrying won't help
        except Exception as e:
            last_error = e
            break
    st.session_state.last_api_error = str(last_error)
    return None


# ---------------------------------------------------------------------------
# Material extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file) -> str:
    text = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n\n".join(text)


def extract_text_from_docx(file) -> str:
    document = docx.Document(file)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_text_from_pptx(file) -> str:
    prs = Presentation(file)
    chunks = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                chunks.append(shape.text)
    return "\n".join(chunks)


def extract_text_from_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore")


def describe_image_with_ai(file) -> str:
    """Send an image (diagram, drawing, scanned notes) to a vision-capable
    Claude model and get back a text description we can treat like any
    other extracted material."""
    image_bytes = file.read()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    media_type = f"image/{file.name.split('.')[-1].lower()}"
    if media_type == "image/jpg":
        media_type = "image/jpeg"

    response = call_claude(
        model=MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64_image},
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a study material uploaded by a student (could be a "
                            "diagram, hand-drawn sketch, scanned notes, or chart). Describe "
                            "everything relevant to studying it: key concepts, labels, "
                            "structure, and any text visible. Be thorough and factual — this "
                            "description will be used to generate study questions."
                        ),
                    },
                ],
            }
        ],
    )
    if response is None:
        return ""
    return response.content[0].text


def extract_material(uploaded_file) -> str:
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(uploaded_file)
    elif ext == "docx":
        return extract_text_from_docx(uploaded_file)
    elif ext == "pptx":
        return extract_text_from_pptx(uploaded_file)
    elif ext == "txt":
        return extract_text_from_txt(uploaded_file)
    elif ext in IMAGE_EXTS:
        return describe_image_with_ai(uploaded_file)
    else:
        return ""


# ---------------------------------------------------------------------------
# AI logic: preview outline, then break material into checkpoints
# ---------------------------------------------------------------------------

def generate_outline(material_text: str) -> dict:
    """Fast, cheap preview call: list the topics found in the material and
    suggest how many checkpoints would suit it. Shown to the student before
    they commit to a full guided session."""
    prompt = f"""You are helping build a study tool. Look at the course material below
and identify the distinct topics/sections it covers.

Respond with ONLY valid JSON, no markdown fences, no preamble, in this shape:
{{
  "topics": ["short topic name", "short topic name", ...],
  "suggested_count": <integer between 3 and 15, a sensible number of checkpoints for this material>
}}

COURSE MATERIAL:
{material_text[:12000]}
"""
    response = call_claude(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    if response is None:
        return None

    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def generate_checkpoints(material_text: str, num_checkpoints: int = 6, focus_topic: str = "") -> list:
    """Ask the model to break the material into a specific number of study
    checkpoints, each with a guiding question, a hint, and the full
    explanation (only shown after the student has attempted the question).
    If focus_topic is given, narrow the material to that topic only."""
    focus_instruction = (
        f'Focus specifically on the topic "{focus_topic}" — ignore parts of the '
        "material unrelated to it, unless there isn't enough content, in which case "
        "use the closest related material available.\n\n"
        if focus_topic.strip()
        else ""
    )
    prompt = f"""You are helping build a study tool. Given the course material below,
break it into exactly {num_checkpoints} checkpoints a student should work through in order.
{focus_instruction}
For each checkpoint, provide:
- "topic": short topic name
- "question": a guiding question that makes the student think, not a yes/no question
- "hint": a small nudge in the right direction, without giving the answer away
- "explanation": the full explanation, grounded strictly in the material provided

Respond with ONLY valid JSON: a list of exactly {num_checkpoints} objects with keys
topic, question, hint, explanation. No markdown fences, no preamble.

COURSE MATERIAL:
{material_text[:12000]}
"""
    response = call_claude(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    if response is None:
        return None  # API call failed after retries — caller shows fallback

    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Model didn't return clean JSON — don't crash, signal failure instead
        return None


def evaluate_answer(question: str, explanation: str, student_answer: str) -> str:
    """Give brief, encouraging feedback on the student's attempt before they
    see the full explanation."""
    prompt = f"""A student was asked: "{question}"
They answered: "{student_answer}"

The correct/full explanation (for your reference only, don't repeat it verbatim) is:
"{explanation}"

Give 2-3 sentences of feedback: what they got right, what's missing or off,
and encourage them to refine their answer. Do not give the full answer away."""
    response = call_claude(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    if response is None:
        return "(Couldn't reach the AI to check your answer right now — take a look at the full explanation below instead.)"
    return response.content[0].text


# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

if "checkpoints" not in st.session_state:
    st.session_state.checkpoints = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "revealed" not in st.session_state:
    st.session_state.revealed = False
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "outline" not in st.session_state:
    st.session_state.outline = None
if "material_text" not in st.session_state:
    st.session_state.material_text = None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("🛠️ Tradie in trAIning")
st.caption("Upload your own course material. This tool won't just hand you the answer — "
           "it guides you through it step by step, like an apprentice doing supervised reps.")

if st.session_state.checkpoints is None:
    uploaded_file = st.file_uploader(
        "Upload your course material",
        type=["pdf", "docx", "pptx", "txt", "png", "jpg", "jpeg"],
    )

    with st.expander("⚙️ Demo safety net (backup checkpoints if the API is down)"):
        st.caption(
            "Before your pitch: run once with real material, then paste the generated "
            "checkpoints JSON here (or your own hand-written backup). If the live API "
            "hiccups during the demo, load this instead of stalling in front of judges."
        )
        backup_json = st.text_area("Backup checkpoints (JSON)", height=100, key="backup_json")
        if st.button("Load backup checkpoints"):
            try:
                st.session_state.checkpoints = json.loads(backup_json)
                st.session_state.current_index = 0
                st.session_state.revealed = False
                st.session_state.feedback = None
                st.rerun()
            except json.JSONDecodeError:
                st.error("That doesn't look like valid JSON — check the format.")

    if uploaded_file is not None and st.session_state.outline is None:
        if st.button("Preview this material", type="primary"):
            with st.spinner("Reading your material..."):
                material_text = extract_material(uploaded_file)
                if not material_text.strip():
                    st.error("Couldn't extract any content from that file. Try a different one.")
                else:
                    outline = generate_outline(material_text)
                    if outline is None:
                        st.error(
                            "Couldn't reach the AI service just now "
                            f"({st.session_state.get('last_api_error', 'unknown error')}). "
                            "This can happen with a flaky connection or a rate limit — try again."
                        )
                    else:
                        st.session_state.material_text = material_text
                        st.session_state.outline = outline
                        st.rerun()

    if st.session_state.outline is not None:
        outline = st.session_state.outline
        st.subheader("This document could be divided into:")
        for topic in outline.get("topics", []):
            st.write(f"• {topic}")

        suggested = outline.get("suggested_count", 6)
        st.caption(f"Suggested checkpoints: {suggested}")

        num_checkpoints = st.number_input(
            "How many checkpoints do you want?",
            min_value=3, max_value=15, value=suggested, step=1,
        )
        focus_topic = st.text_input(
            "Focus on a specific topic only? (optional — leave blank to cover everything)"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Start guided study session", type="primary"):
                with st.spinner("Preparing your checkpoints..."):
                    checkpoints = generate_checkpoints(
                        st.session_state.material_text,
                        num_checkpoints=int(num_checkpoints),
                        focus_topic=focus_topic,
                    )
                    if checkpoints is None:
                        st.error(
                            "Couldn't reach the AI service just now "
                            f"({st.session_state.get('last_api_error', 'unknown error')}). "
                            "This can happen with a flaky connection or a rate limit — try again."
                        )
                    else:
                        st.session_state.checkpoints = checkpoints
                        st.session_state.current_index = 0
                        st.session_state.revealed = False
                        st.session_state.feedback = None
                        st.rerun()
        with col_b:
            if st.button("⟲ Upload a different file"):
                st.session_state.outline = None
                st.session_state.material_text = None
                st.rerun()

else:
    checkpoints = st.session_state.checkpoints
    idx = st.session_state.current_index

    if idx >= len(checkpoints):
        st.success("🎉 You've worked through all the checkpoints for this material!")
        st.write(f"You completed **{len(checkpoints)}** checkpoints.")
        if st.button("Start over with new material"):
            st.session_state.checkpoints = None
            st.session_state.current_index = 0
            st.session_state.revealed = False
            st.session_state.feedback = None
            st.session_state.outline = None
            st.session_state.material_text = None
            st.rerun()
    else:
        cp = checkpoints[idx]
        st.progress((idx) / len(checkpoints), text=f"Checkpoint {idx + 1} of {len(checkpoints)}")
        st.subheader(cp["topic"])
        st.write(cp["question"])

        with st.expander("Need a hint?"):
            st.info(cp["hint"])

        student_answer = st.text_area("Your answer", key=f"answer_{idx}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check my answer") and student_answer.strip():
                with st.spinner("Thinking..."):
                    st.session_state.feedback = evaluate_answer(
                        cp["question"], cp["explanation"], student_answer
                    )

        if st.session_state.feedback:
            st.write("**Feedback:**")
            st.write(st.session_state.feedback)

        with col2:
            if st.button("Reveal full explanation"):
                st.session_state.revealed = True

        if st.session_state.revealed:
            st.success(cp["explanation"])
            if st.button("Next checkpoint →", type="primary"):
                st.session_state.current_index += 1
                st.session_state.revealed = False
                st.session_state.feedback = None
                st.rerun()

    st.divider()
    if st.button("⟲ Start over with different material"):
        st.session_state.checkpoints = None
        st.session_state.current_index = 0
        st.session_state.revealed = False
        st.session_state.feedback = None
        st.session_state.outline = None
        st.session_state.material_text = None
        st.rerun()