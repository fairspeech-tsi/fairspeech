# Data contracts

Status: **DRAFT v0.1** — segment table proposed by A, feedback JSON proposed by C. Confirm both in the group chat by Wed 21 Oct; C then marks them v1.0.

Changing a contract after v1.0: propose in the chat, C updates this file and `schemas/feedback.schema.json`, bump the version.

---

## 1. Segment table (owner: A)

One row per speaker turn. File: `data/interim/segments.csv` (UTF-8, comma-separated). *Columns below are a placeholder for A to replace or confirm.*

| Column | Type | Example | Notes |
|---|---|---|---|
| `segment_id` | string | `edacc_c012_s03_t0042` | Unique, stable across all files |
| `conversation_id` | string | `c012` | EdAcc conversation |
| `speaker_id` | string | `c012_s03` | Used for the speaker-level bootstrap |
| `accent_group` | string | `south_asian` | One of the 3–4 clusters A defines, or `native_ref` |
| `l1` | string | `Hindi` | As in EdAcc metadata |
| `audio_path` | string | `data/interim/audio/edacc_c012_s03_t0042.wav` | 16 kHz mono WAV |
| `start` | float | `312.48` | Seconds in the original recording |
| `end` | float | `327.91` | Seconds |
| `duration` | float | `15.43` | `end - start` |
| `human_transcript` | string | `I have led three projects…` | Verbatim EdAcc transcript, fillers kept |
| `split` | string | `train` | `train` / `val` / `test`, **conversation-disjoint**: both speakers of a conversation are in the same split, so each speaker appears in one split only (A → B by Sun 8 Nov) |

---

## 2. Transcript + feedback JSON (owner: C)

One JSON file **per segment per source**:
`data/processed/feedback/<source>/<segment_id>.json`, where `source` is `human`, `whisper`, `crisperwhisper` or `vosk`.

B writes `segment_id`, `source`, `transcript` and `words`. C's modules add `fluency` and `feedback`. Validated by `schemas/feedback.schema.json`; a full example is in `data/mock/feedback_example.json`.

### Top level

| Field | Type | Written by | Notes |
|---|---|---|---|
| `schema_version` | string | B/C | `"0.1"` |
| `segment_id` | string | B | Must match the segment table |
| `source` | string | B | `human` · `whisper` · `crisperwhisper` · `vosk` |
| `model` | string or null | B | e.g. `"openai/whisper-large-v3"`; null for `human` |
| `transcript` | string | B | Full text as produced, fillers kept |
| `words` | array | B | One object per word, in order (below) |
| `fluency` | object or null | C | Filled by the fluency and filler modules |
| `feedback` | array | C | Zero or more flags (below) |
| `created_at` | string | B/C | ISO 8601 UTC |

### `words[]`

| Field | Type | Notes |
|---|---|---|
| `i` | int | Word index, from 0 |
| `word` | string | As transcribed, without surrounding spaces |
| `start` | float or null | Seconds from segment start; null if unknown (e.g. human transcript) |
| `end` | float or null | Seconds |
| `confidence` | float or null | 0–1 word probability; null for `human` and models that do not provide it |

### `fluency`

| Field | Type | Notes |
|---|---|---|
| `wpm` | float | Words per minute over speaking time |
| `n_pauses` | int | Pauses ≥ 0.5 s between words |
| `mean_pause_s` | float | Mean pause length |
| `filler_count` | int | um, uh, erm, like (as filler), you know |

### `feedback[]`

| Field | Type | Notes |
|---|---|---|
| `flag_id` | string | `<segment_id>:<source>:<n>` |
| `type` | string | `grammar` · `filler` · `fluency` |
| `rule_id` | string | LanguageTool rule ID, or our own (e.g. `FILLER_UM`) |
| `category` | string | Grouped rule type, e.g. `subject_verb_agreement`, `article`, `tense`, `filler` |
| `word_start` | int | Index into `words` of the first flagged word |
| `word_end` | int | Index of the last flagged word (inclusive) |
| `text` | string | Flagged words as they appear |
| `message` | string | Short explanation for the learner |
| `suggestion` | string or null | Proposed correction |
| `asr_confidence` | float or null | Minimum word confidence over the flagged words |
| `label` | string or null | `false` (ASR-induced) · `genuine` · `ambiguous` (alignment unclear; excluded from training and counted) · null until alignment runs. It shows whether a flag is caused by a transcript difference, not whether the grammar checker is right |
| `shown` | bool | Whether the flag is shown after gating (true before gating) |

### Metric definitions (from the proposal, Appendix B)

- False feedback rate for accent group g: `FFR_g = false flags shown to g / all flags shown to g`.
- Gap: `max_g FFR_g - min_g FFR_g`. The worst group's FFR and the gap are reported separately.
- Genuine-flag recall: `kept genuine flags / all genuine flags`; the gate threshold keeps it at least 0.90 on the validation set, and it is reported again on the test set.

### Manual label check

While testing the alignment, C checks about 100 automatic labels by hand, sampled across accent groups and rule types, in `docs/label_check.csv` (`flag_id, auto_label, manual_label, note`). The share that agrees is reported as label accuracy.
