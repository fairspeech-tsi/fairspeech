"""Practice page (C): record or upload an answer, or pick a mock example.

Recording and upload are only shown after the user has read the data notice
and ticked the consent box (MO2). Consent, audio and results live in the
session only, so a reload deletes them and asks again.
"""
import hashlib

import streamlit as st

from src.app.components import render_feedback, render_fluency
from src.app.data import list_examples, load_record
from src.app.notice import CONSENT_LABEL, NOTICE_MARKDOWN, NOTICE_TITLE
from src.app.pipeline import analyse

UPLOAD_TYPES = ["wav", "mp3", "flac", "ogg"]


def show_record(record: dict) -> None:
    """Transcript, fluency and feedback for one record."""
    model = record["model"] or "human transcript"
    st.caption(f"Source: {record['source']} · {model}")
    st.subheader("Transcript")
    st.write(record["transcript"])
    st.subheader("Fluency")
    render_fluency(record["fluency"])
    st.subheader("Feedback")
    render_feedback(record)


st.title("Interview practice")
answer_tab, examples_tab = st.tabs(["Record or upload", "Examples"])

with answer_tab:
    with st.container(border=True):
        st.markdown(f"#### {NOTICE_TITLE}")
        st.markdown(NOTICE_MARKDOWN)
        consent = st.checkbox(CONSENT_LABEL, key="consent")

    if not consent:
        st.info("Tick the box above to record or upload an answer.")
    else:
        recorded = st.audio_input("Record your answer")
        uploaded = st.file_uploader("…or upload an audio file", type=UPLOAD_TYPES)
        audio = recorded or uploaded
        audio_bytes = audio.getvalue() if audio else None
        audio_id = hashlib.sha256(audio_bytes).hexdigest() if audio_bytes else None

        if st.button("Get feedback", type="primary", disabled=audio_bytes is None):
            with st.spinner("Transcribing and checking your answer…"):
                try:
                    st.session_state["answer"] = analyse(audio_bytes)
                    st.session_state["answer_id"] = audio_id
                except RuntimeError as err:
                    st.error(str(err))

        # Show the result only for the audio it was made from.
        if audio_id and st.session_state.get("answer_id") == audio_id:
            answer = st.session_state["answer"]
            if answer["words"]:
                show_record(answer)
            else:
                st.warning("No speech was recognised. Please try again.")

with examples_tab:
    st.caption("Mock examples, no audio involved.")
    examples = list_examples()
    label = st.selectbox("Example answer", list(examples))
    try:
        record = load_record(examples[label])
    except ValueError as err:
        st.error(str(err))
    else:
        show_record(record)