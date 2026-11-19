"""About page: how FairSpeech works and how data is handled (notice text by D)."""
import streamlit as st

from src.app.notice import NOTICE_MARKDOWN, NOTICE_TITLE

st.title(NOTICE_TITLE)
st.markdown(NOTICE_MARKDOWN)