"""FairSpeech Streamlit app: entry point and page list.

Run from the repo root:
    streamlit run src/app/streamlit_app.py

To add a page: create a file in src/app/app_pages/ and add one st.Page line
below (see src/app/README.md).
"""
import sys
from pathlib import Path

import streamlit as st

# Streamlit only puts this file's folder on the import path. Add the repo root
# so pages can use "from src... import ...".
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="FairSpeech", page_icon=":material/record_voice_over:", layout="wide")

PAGES = Path(__file__).parent / "app_pages"

nav = st.navigation([
    st.Page(PAGES / "practice.py", title="Practice", icon=":material/mic:", default=True),
    st.Page(PAGES / "transcript.py", title="Transcript view", icon=":material/subject:"),
    st.Page(PAGES / "about.py", title="About", icon=":material/info:"),
])
nav.run()