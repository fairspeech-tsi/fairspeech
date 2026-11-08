# FairSpeech app

Run from the repo root:

    streamlit run src/app/streamlit_app.py

## Structure

| File | What it holds | Owner |
|---|---|---|
| `streamlit_app.py` | Entry point: page config and the page list | C |
| `data.py` | `list_examples()`, `load_record(path)`: find and load feedback JSON (validated, cached) | C |
| `components.py` | `render_fluency()`, `render_feedback()`, `render_flag()`: shared display pieces | C |
| `app_pages/practice.py` | Practice: pick an answer, see transcript, fluency and feedback | C |
| `app_pages/transcript.py` | Transcript view with confidence-marked flags (FS-005) | A |
| `app_pages/about.py` | How it works and the data notice (MO2) | D / C |

## How to add a page

1. Create a file in `src/app/app_pages/`, e.g. `fairness.py`:

   ```python
   """Fairness results (A)."""
   import streamlit as st

   from src.app.data import list_examples, load_record

   st.title("Fairness results")
   ```

2. Add one line to the list in `streamlit_app.py`:

   ```python
   st.Page(PAGES / "fairness.py", title="Fairness", icon=":material/balance:"),
   ```

3. Restart the app (new page files need a restart; edits to existing pages
   reload on save).

Rules:

- Load records with `load_record()`, not `json.load()`, so every page validates
  the same way.
- Show flags with `render_flag()` / `render_feedback()`, so they look the same
  on every page.
- Do not call `st.set_page_config()` in a page; it is set once in `streamlit_app.py`.
- Icons: any name from [Material Symbols](https://fonts.google.com/icons), as `:material/<name>:`.