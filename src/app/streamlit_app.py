"""FairSpeech Streamlit app - skeleton (week 3: runs on mock JSON).

Run:  streamlit run src/app/streamlit_app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

MOCK = Path(__file__).resolve().parents[2] / "data" / "mock" / "feedback_example.json"

st.set_page_config(page_title="FairSpeech", layout="centered")
st.title("FairSpeech interview practice")
st.caption("Skeleton running on mock data. Recording and upload are connected in week 4.")

record = json.loads(MOCK.read_text(encoding="utf-8"))

st.subheader("Transcript")
st.write(record["transcript"])

st.subheader("Fluency")
f = record["fluency"]
cols = st.columns(3)
cols[0].metric("Words per minute", f["wpm"])
cols[1].metric("Pauses", f["n_pauses"])
cols[2].metric("Fillers", f["filler_count"])

st.subheader("Feedback")
for flag in record["feedback"]:
    if not flag["shown"]:
        continue
    conf = flag["asr_confidence"]
    note = f" (ASR confidence {conf:.2f})" if conf is not None else ""
    st.markdown(f"**{flag['text']}** - {flag['message']}{note}")
