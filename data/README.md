# Data

Nothing in `raw/`, `interim/` or `processed/` is committed: EdAcc audio and our outputs stay on each member's machine or the shared drive. Only `mock/` is in git.

| Folder | Contents | Owner |
|---|---|---|
| `raw/` | EdAcc as downloaded (CC-BY-SA, cite Sanabria et al., 2023) | A |
| `interim/` | Segmented audio (`audio/`) and `segments.csv` | A |
| `processed/` | ASR outputs and feedback JSON (`feedback/<source>/<segment_id>.json`), labels | B, C |
| `mock/` | Small example files for tests and the app | C |

Formats: [`docs/data_contracts.md`](../docs/data_contracts.md).
