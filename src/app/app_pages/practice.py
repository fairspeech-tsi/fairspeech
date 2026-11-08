"""Practice page (C): pick an answer, see transcript, fluency and feedback.

Uses mock records for now. In week 4 (FS-031) the picker is joined by
recording and upload, which run ASR and the feedback modules on the answer.
"""
import streamlit as st

from src.app.components import render_feedback, render_fluency
from src.app.data import list_examples, load_record

st.title("Interview practice")
st.caption("Running on mock data. Recording and upload are connected in week 4.")

examples = list_examples()
label = st.selectbox("Example answer", list(examples))

try:
    record = load_record(examples[label])
except ValueError as err:
    st.error(str(err))
    st.stop()

source = record["source"]
model = record["model"] or "human transcript"
st.caption(f"Source: {source} · {model}")

st.subheader("Transcript")
st.write(record["transcript"])

st.subheader("Fluency")
render_fluency(record["fluency"])

st.subheader("Feedback")
render_feedback(record)