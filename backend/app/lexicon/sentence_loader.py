"""Sentence and Lexique file loading utilities.

This module provides two independent data pipelines:

1. **Lexique morphological database** — ``read_lexique_entries`` iterates over
   ``Lexique4.tsv`` once and yields structured rows.  ``load_lexique_forms``
   builds the surface-form → lemma map used for sentence word matching, and
   ``parse_info_ver`` / ``verb_form_type_from_features`` are used by the
   conjugation import script.

2. **Sentence pairs** — ``load_sentence_pairs`` reads a Tatoeba-style sentence
   TSV and produces one record per (French, English) pair, with word-match
   metadata attached.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿŒœÆæ]+(?:['’][\wÀ-ÖØ-öø-ÿŒœÆæ]+)?", re.UNICODE)


# ── Lexique conjugation tag helpers ───────────────────────────────────

_MOOD_MAP = {
    "ind": "indicative",
    "sub": "subjunctive",
    "imp": "imperative",
    "cnd": "conditional",
    "par": "participle",
    "inf": "infinitive",
}

_TENSE_MAP = {
    "pre": "present",
    "imp": "imperfect",
    "fut": "future",
    "pas": "past",
    "p": "past",
}


def parse_info_ver(tag: str) -> dict | None:
    """Parse a single InfoVER tag into a features dict.

    Tag format examples::

        ind:pre:1s   → {mood:indicative, tense:present, person:1, number:s}
        ind:imp:2    → {mood:indicative, tense:imperfect, person:2, number:s}
        ind:fut:1p   → {mood:indicative, tense:future, person:1, number:p}
        cnd:pre:3p   → {mood:conditional, tense:present, person:3, number:p}
        par:p        → {mood:participle, tense:past}
        inf          → {mood:infinitive}
        ind:pre:1s,imp:pre:1  → same form, two tags (comma-separated)
    """
    tag = tag.strip()
    if not tag:
        return None

    parts = tag.split(":")
    mood = _MOOD_MAP.get(parts[0])
    if mood is None:
        return None

    if mood == "infinitive":
        return {"mood": "infinitive"}

    if mood == "participle":
        tense = _TENSE_MAP.get(parts[1]) if len(parts) > 1 else "past"
        return {"mood": "participle", "tense": tense}

    if mood in ("indicative", "subjunctive", "imperative", "conditional"):
        if len(parts) >= 3:
            tense = _TENSE_MAP.get(parts[1], parts[1])
            person_str = parts[2]
            person = person_str[0] if person_str else ""
            number = person_str[1] if len(person_str) > 1 else "s"
            return {"mood": mood, "tense": tense, "person": person, "number": number}
        if len(parts) == 2:
            tense = _TENSE_MAP.get(parts[1], parts[1])
            return {"mood": mood, "tense": tense}

    return None


def verb_form_type_from_features(features: dict) -> str:
    """Determine the ``form_type`` for a feature set returned by ``parse_info_ver``."""
    mood = features.get("mood", "")
    if mood == "infinitive":
        return "infinitive"
    if mood == "participle":
        return "past_participle" if features.get("tense") == "past" else "conjugation"
    if mood in ("indicative", "subjunctive", "imperative", "conditional"):
        return "conjugation"
    return "conjugation"


# ── Lexique file reading ──────────────────────────────────────────────


def read_lexique_entries(path: str | Path) -> list[dict[str, Any]]:
    """Read every row of ``Lexique4.tsv`` and return a list of records.

    Each record contains the raw columns by name (``1_Mot``, ``4_Lemme``,
    ``5_Cgram``, ``9_InfoVER``, etc.) plus a pre-parsed ``conjugation_tags``
    field that is a list of feature dicts from ``parse_info_ver`` (empty list
    if not a verb or no tag data).
    """
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            surface = row.get("1_Mot", "").strip()
            lemma = row.get("4_Lemme", "").strip()
            if not surface or not lemma:
                continue
            cgram = row.get("5_Cgram", "").strip()
            info_ver = row.get("9_InfoVER", "").strip()

            row["1_Mot"] = surface
            row["4_Lemme"] = lemma
            row["5_Cgram"] = cgram
            row["9_InfoVER"] = info_ver

            # Pre-parse verb tags
            tags: list[dict] = []
            if cgram in ("VER", "AUX") and info_ver:
                for tag in info_ver.split(","):
                    parsed = parse_info_ver(tag)
                    if parsed is not None:
                        tags.append(parsed)
            row["conjugation_tags"] = tags
            rows.append(row)
    return rows


def load_lexique_forms(path: str | Path) -> dict[str, set[str]]:
    """Map observed French forms to their lemmas from Lexique4.tsv.

    This is a convenience wrapper around ``read_lexique_entries`` that returns
    the ``{normalised_surface: {lemma, ...}}`` dict used by
    ``sentence_word_matches``.
    """
    forms: dict[str, set[str]] = {}
    for row in read_lexique_entries(path):
        forms.setdefault(_normalise(row["1_Mot"]), set()).add(row["4_Lemme"])
    return forms


# ── Normalisation ─────────────────────────────────────────────────────


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    return value.replace("’", "'")


# ── Sentence word matching ────────────────────────────────────────────


def sentence_word_matches(
    sentence: str, forms: dict[str, set[str]]
) -> list[dict[str, Any]]:
    """Find known surface forms and return their spans and lemmas.

    This is deliberately conservative: it records exact token matches and
    Lexique lemmas, while leaving disambiguation and multi-word expressions for
    a later NLP step.
    """
    matches = []
    seen: set[tuple[int, int, str]] = set()
    for token in _TOKEN_RE.finditer(sentence):
        surface = token.group(0)
        for lemma in sorted(forms.get(_normalise(surface), ())):
            key = (token.start(), token.end(), lemma)
            if key not in seen:
                matches.append(
                    {
                        "surface": surface,
                        "lemma": lemma,
                        "start": token.start(),
                        "end": token.end(),
                    }
                )
                seen.add(key)
    return matches


# ── Sentence pair loading ─────────────────────────────────────────────


def load_sentence_pairs(
    path: str | Path, forms: dict[str, set[str]]
) -> list[dict[str, Any]]:
    """Load every French-English row and retain all translations.

    Each row remains a separate pair because different translations can add
    useful semantic information. Word matches are shared by all pairs with the
    same French sentence.
    """
    grouped: dict[str, dict[str, Any]] = {}
    pairs: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            if len(row) < 4:
                continue
            french = row[1].strip()
            english = row[3].strip()
            if not french or not english:
                continue
            if french not in grouped:
                grouped[french] = {
                    "sentence_id": row[0],
                    "text": french,
                    "words": sentence_word_matches(french, forms),
                    "translations": [],
                }
            sentence = grouped[french]
            if english not in sentence["translations"]:
                sentence["translations"].append(english)
                pairs.append(
                    {
                        "pair_id": f"{row[0]}:{len(sentence['translations'])}",
                        "sentence_id": row[0],
                        "text": french,
                        "translation": english,
                        "words": sentence["words"],
                    }
                )
    return pairs