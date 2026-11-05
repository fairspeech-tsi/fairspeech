# Grammar examples

Example outputs of the grammar module (`src/feedback/grammar.py`) in the shared
feedback JSON format (`docs/data_contracts.md`). Regenerate with:

    python -m scripts.make_grammar_examples

Folders follow the contract layout: `<source>/<segment_id>.json`.

## Pairs

The sentences are **hand-written**, not EdAcc data. Each pair mimics a common
ASR error on accented speech, so the expected label of every Whisper flag is
known. Whisper confidences are **illustrative** (0.42 on the misrecognised
word, 0.95 elsewhere), not model outputs. `label` is null in the files: the
alignment step fills it.

| Segment | Human | Whisper | Whisper flag | Expected label |
|---|---|---|---|---|
| mock_pair1 | I have led three projects… | I **has** led three projects… | has: subject_verb_agreement | false |
| mock_pair2 | she works in a bank… | She **work** in a bank… | work: subject_verb_agreement | false |
| mock_pair3 | we discussed an idea… | We discussed **a** idea… | a: article | false |
| mock_pair4 | he don't like… | He don't like… | don't: subject_verb_agreement (also in human) | genuine |
| mock_pair5 | um I think the deadline… | Um, I think the deadline… | none: punctuation and casing differ only | no flag |

Pairs 1–3: the speaker was right, the ASR was wrong. Pair 4: a real speaker
error that both sources keep. Pair 5: shows that normalisation stops
punctuation and casing differences from creating flags.