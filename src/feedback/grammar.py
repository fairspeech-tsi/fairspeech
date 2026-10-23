"""Grammar module (LanguageTool + spaCy). Week 1-2.

Input: a record with `transcript` and `words`.
Output: grammar flags appended to `record["feedback"]` (type "grammar").
"""
from src.text_normalise import normalise_token