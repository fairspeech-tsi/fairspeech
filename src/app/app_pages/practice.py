"""Practice page (C): record or upload an answer, or pick a mock example.

Recording and upload are only shown after the user has read the data notice
and ticked the consent box (MO2). The consent lives in the session only, so a
reload asks again. Recording and upload themselves are connected in FS-031.
"""
import streamlit as st

from src.app.components import render_feedback, render_fluency
from src.app.data import list_examples, load_record
from src.app.notice import CONSENT_LABEL, NOTICE_MARKDOWN, NOTICE_TITLE


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
        st.info("Recording and upload are coming in the next update.")

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