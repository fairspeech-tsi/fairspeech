"""Data notice, consent text and feedback disclaimer (text by D, Juliet).

Kept in one place so the About page, the Practice page and the feedback
display always show the same wording. To change the text, edit it here only.
"""

NOTICE_TITLE = "About FairSpeech and your data"

NOTICE_MARKDOWN = """
FairSpeech is a coursework prototype that gives automatic feedback on your spoken English.

**What it does:** you record or upload a spoken answer. The app turns it into text,
checks grammar and filler words, and measures your speaking rate and pauses.

**What happens to your data:** your audio and results are used only during this
session and are kept only in the app's memory. Nothing is saved to disk, logged or
used to train a model. When you close or reload the page, they are deleted. Speech
recognition runs on the same computer that runs the app, using a small Whisper
model, so the audio is not sent to an outside service. The grammar check also runs
on the same computer.

**Automatic feedback:** the feedback is generated automatically and may contain
speech-recognition errors. A flagged item is not always a real mistake, especially
for different accents.

**Intended use:** personal practice only. The app is not for grading, assessing or
selecting people.

**Your choice:** you can stop at any time. Closing or reloading the page deletes
your audio and results.

**Questions:** [team contact or supervisor].
"""

CONSENT_LABEL = "I have read this notice and agree that my audio is processed as described."

FEEDBACK_DISCLAIMER = (
    "This feedback is generated automatically and may contain speech-recognition errors. "
    "A flagged item is not always a real mistake, especially for different accents."
)