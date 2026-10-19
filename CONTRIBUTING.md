# Contributing to FairSpeech

## Branch rules

- `main` is protected: it always runs. Nobody pushes to `main` directly.
- Work on a short-lived branch named `<member>/<topic>`, for example:
  - `a/segment-table`
  - `b/whisper-confidence`
  - `c/grammar-module`
  - `d/mo2-draft`
- Open a pull request (PR) into `main` when the work runs. Small PRs are better than big ones.
- Each PR needs **one approval** from the assigned reviewer before merging:

  | Author | Reviewer |
  |---|---|
  | A | C |
  | B | A |
  | C | B |
  | D (documentation) | the owner of the area it describes |

- Merge with **Squash and merge**, then delete the branch.
- Code freeze: **Sun 6 Dec**. After that only bug fixes go into `main`.
- Fill in the pull request template, including the contribution split (e.g. `B 70%, A 30%`).

## Commits

- One logical change per commit, written in the imperative: `Add filler detection`, `Fix WPM for empty segments`.
- Mention the Kanban card in the PR description, e.g. `Closes #12`.
- Record contribution shares on the Kanban card as you go (e.g. `B 70%, A 30%`).

## Data and secrets

- **Never commit audio, the EdAcc download or model files.** `.gitignore` blocks them; do not force-add.
- Small mock files for tests and the app go in `data/mock/`.
- Tokens (e.g. Hugging Face) go in a local `.env` file, never in code.

## Shared formats

- Segment table and feedback JSON: see [`docs/data_contracts.md`](docs/data_contracts.md).
- Feedback JSON is validated against [`schemas/feedback.schema.json`](schemas/feedback.schema.json); run `pytest` before opening a PR.
- If you need to change a shared format, propose it in the group chat first; C updates the contract and the schema.

## Code style

- Python 3.10+, type hints on public functions, a docstring on every module and public function.
- Keep notebooks for exploration; move reusable code into `src/`.
