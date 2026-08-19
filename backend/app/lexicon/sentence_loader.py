from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿŒœÆæ]+(?:['’][\wÀ-ÖØ-öø-ÿŒœÆæ]+)?", re.UNICODE)


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    return value.replace("’", "'")


def load_lexique_forms(path: str | Path) -> dict[str, set[str]]:
    """Map observed French forms to their lemmas from Lexique4.tsv."""
    forms: dict[str, set[str]] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            form = row.get("1_Mot", "").strip()
            lemma = row.get("4_Lemme", "").strip()
            if form and lemma:
                forms.setdefault(_normalise(form), set()).add(lemma)
    return forms


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
