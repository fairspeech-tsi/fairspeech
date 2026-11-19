"""About page: how FairSpeech works and how data is handled."""
import streamlit as st

st.title("About FairSpeech")
st.markdown(
    "FairSpeech checks whether speech-recognition errors turn into unfair "
    "feedback for speakers with different accents, and hides feedback that is "
    "likely caused by a recognition error rather than by the speaker."
)
st.subheader("Your data")
st.info("Placeholder: data notice and consent text from the MO2 document (D).")