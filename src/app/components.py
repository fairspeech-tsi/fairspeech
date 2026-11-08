"""Shared display pieces for the app pages.

Every page that shows a feedback record uses these, so a flag or a fluency
metric looks the same everywhere in the app.
"""
from __future__ import annotations

import streamlit as st

# Display order and headings of flag types.
TYPE_TITLES = {"grammar": "Grammar", "filler": "Fillers", "fluency": "Fluency"}


def render_fluency(fluency: dict | None) -> None:
    """Show speaking rate, long pauses, average pause and fillers as four metrics.

    Human transcripts have no word timings (fluency is None): show a short note instead.
    """
    if fluency is None:
        st.caption("Fluency needs word timings, which this transcript does not have.")
        return
    rate, pauses, avg_pause, fillers = st.columns(4)
    rate.metric("Speaking rate", f"{fluency['wpm']:.0f} wpm")
    pauses.metric("Long pauses", fluency["n_pauses"])
    avg_pause.metric("Average pause", f"{fluency['mean_pause_s']:.2f} s" if fluency["n_pauses"] else "–")
    fillers.metric("Fillers", fluency["filler_count"])


def render_flag(flag: dict) -> None:
    """One flag in a bordered box: words, message, suggestion and ASR confidence."""
    with st.container(border=True):
        st.markdown(f"**{flag['text']}** · {flag['message']}")
        if flag["suggestion"]:
            st.markdown(f"Try: *{flag['suggestion']}*")
        if flag["asr_confidence"] is not None:
            st.caption(f"Recognition confidence: {flag['asr_confidence']:.0%}")


def render_feedback(record: dict) -> None:
    """Show the flags a learner would see (shown = True), grouped by type.

    Flags hidden by the gate (shown = False) are only counted, so the page
    also works after gating. No shown flags: a short positive note.
    """
    flags = record["feedback"]
    shown = [f for f in flags if f["shown"]]
    hidden = len(flags) - len(shown)

    if not shown:
        st.success("No feedback for this answer.")
    for ftype, title in TYPE_TITLES.items():
        group = [f for f in shown if f["type"] == ftype]
        if not group:
            continue
        st.markdown(f"#### {title}")
        for flag in group:
            render_flag(flag)

    if hidden:
        st.caption(f"{hidden} more flag(s) hidden because they are likely speech-recognition errors.")