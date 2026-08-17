"""Load a TEI dictionary without losing entry or sense information.

The returned objects contain plain Python values and are therefore suitable for
serialising as JSON, inserting into Postgres, or turning into embedding
records.  TEI namespaces are handled explicitly because the source uses the
TEI default namespace.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

PART_OF_SPEECH = {
    "adj": "adjective",
    "adv": "adverb",
    "art": "article",
    "conj": "conjunction",
    "int": "interjection",
    "n": "noun",
    "num": "numeral",
    "prep": "preposition",
    "pron": "pronoun",
    "v": "verb",
    "vi": "intransitive verb",
    "vt": "transitive verb",
}

_TEI = "{http://www.tei-c.org/ns/1.0}"


def _text(element: ET.Element | None) -> str | None:
    """Return normalised text, or None for a missing/empty element."""
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _attr(element: ET.Element, name: str) -> str | None:
    value = element.attrib.get(name)
    return value.strip() if value and value.strip() else None


def _element(entry: ET.Element, name: str) -> ET.Element | None:
    # ``find`` is intentionally scoped to direct children: a sense's form or
    # grammatical information must not accidentally be used for the entry.
    return entry.find(f"{_TEI}{name}")


def _parse_entry(entry: ET.Element, index: int) -> dict[str, Any]:
    form = _element(entry, "form")
    gramgrp = _element(entry, "gramGrp") or _element(entry, "gramgrp")

    pos_code = _text(_element(gramgrp, "pos")) if gramgrp is not None else None
    senses: list[dict[str, Any]] = []
    for sense_index, sense in enumerate(entry.findall(f"{_TEI}sense"), start=1):
        translations = [
            quote
            for cit in sense.findall(f"{_TEI}cit")
            if _attr(cit, "type") == "trans"
            and (quote := _text(_element(cit, "quote"))) is not None
        ]
        sense_number = _attr(sense, "n")
        senses.append(
            {
                "number": (
                    int(sense_number)
                    if sense_number and sense_number.isdigit()
                    else sense_index
                ),
                "translations": translations,
            }
        )

    return {
        "id": index,
        "word": _text(_element(form, "orth")) if form is not None else None,
        "pronunciation": _text(_element(form, "pron")) if form is not None else None,
        "part_of_speech_code": pos_code,
        "part_of_speech": PART_OF_SPEECH.get(pos_code) if pos_code else None,
        "gender": _text(_element(gramgrp, "gen")) if gramgrp is not None else None,
        "senses": senses,
        "meaning_count": len(senses),
    }


def load_tei_entries(path: str | Path) -> list[dict[str, Any]]:
    """Return one record per TEI ``entry`` in *path*.

    Missing form, pronunciation, grammatical group, sense, and quote elements
    become ``None`` or empty lists.  This keeps the shape stable for database
    consumers while retaining the distinction between missing and present data.
    """
    root = ET.parse(path).getroot()
    return [_parse_entry(entry, index) for index, entry in enumerate(
        root.iter(f"{_TEI}entry"), start=1
    )]


def load_tei_dictionary(path: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Group records by source word; repeated spellings remain separate entries."""
    dictionary: dict[str, list[dict[str, Any]]] = {}
    for entry in load_tei_entries(path):
        key = entry["word"] or ""
        dictionary.setdefault(key, []).append(entry)
    return dictionary


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a TEI dictionary to JSON")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    data = load_tei_dictionary(args.input)
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
