"""Generate a TEI dictionary for French words that are missing from the
existing FreeDict dictionaries but appear frequently in sentence data.

Uses an LLM (OpenAI-compatible API) to produce English translations.

Usage::

    python -m app.lexicon.generate_missing_words --api-key sk-... [--num-words 500]
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

import httpx

from app.database import SessionLocal
from app.lexicon.embedding_config import load_config
from app.lexicon.sentence_loader import load_lexique_forms, load_sentence_pairs
from app.lexicon.tei_loader import load_tei_entries
from app.models import LexicalItem
from sqlalchemy import select

TEI_NS = "http://www.tei-c.org/ns/1.0"


def _tag(name: str) -> str:
    return f"{{{TEI_NS}}}{name}"


def _make_entry(word: str, pos: str | None, senses: dict[str, list[str]]) -> Element:
    """Create a TEI ``<entry>`` from a word, optional POS, and numbered sense groups.

    *senses* is a dict like ``{"1": ["buy", "purchase"], "2": ["meaning2"]}``.
    """
    entry = Element(_tag("entry"))
    form = SubElement(entry, _tag("form"))
    SubElement(form, _tag("orth")).text = word
    if pos:
        gramgrp = SubElement(entry, _tag("gramGrp"))
        SubElement(gramgrp, _tag("pos")).text = pos
    for num_str, translations in senses.items():
        sense = SubElement(entry, _tag("sense"))
        if num_str not in ("", "1"):
            sense.set("n", num_str)
        for translation in translations:
            cit = SubElement(sense, _tag("cit"), type="trans")
            SubElement(cit, _tag("quote")).text = translation
    return entry


def _build_tei(entries: list[Element]) -> Element:
    tei = Element(_tag("TEI"), xmlns=TEI_NS)
    header = SubElement(tei, _tag("teiHeader"))
    fd = SubElement(header, _tag("fileDesc"))
    ts = SubElement(fd, _tag("titleStmt"))
    SubElement(ts, _tag("title")).text = "Auto-generated French-English Dictionary (LLM)"
    SubElement(fd, _tag("extent")).text = f"{len(entries)} headwords"
    SubElement(SubElement(fd, _tag("publicationStmt")), _tag("publisher")).text = "LLM-generated"
    SubElement(SubElement(fd, _tag("sourceDesc")), _tag("p")).text = "Lexique4 + Tatoeba + LLM"
    text = SubElement(tei, _tag("text"))
    body = SubElement(text, _tag("body"))
    for e in entries:
        body.append(e)
    return tei


def get_missing_words(cfg: Any, num_words: int) -> list[dict[str, Any]]:
    """Return the most frequent French lemmas missing from the database, up to *num_words*.

    Each entry includes the word and part-of-speech from Lexique if available.
    """
    with SessionLocal() as session:
        known = set(r[0].casefold() for r in session.execute(select(LexicalItem.word)).all())

    tei_dir = Path(cfg.tei_file).parent
    for fname in ("fra-eng.tei", "eng-fra.tei"):
        p = tei_dir / fname
        if p.exists():
            for e in load_tei_entries(str(p)):
                if e.get("word"):
                    known.add(e["word"].casefold())

    from app.lexicon.sentence_loader import read_lexique_entries
    lexique_rows = read_lexique_entries(cfg.lexique_file)
    pos_by_lemma: dict[str, str] = {}
    for r in lexique_rows:
        lemma = r["4_Lemme"].casefold()
        if lemma not in pos_by_lemma:
            cgram = r.get("5_Cgram", "")
            # Map Lexique codes to TEI-style POS codes
            pos_code = {
                "NOM": "n", "VER": "v", "ADJ": "adj", "ADV": "adv",
                "AUX": "v", "ONO": "int",
            }.get(cgram, cgram.lower() if cgram else "")
            pos_by_lemma[lemma] = pos_code

    forms = load_lexique_forms(cfg.lexique_file)
    pairs = load_sentence_pairs(cfg.sentences_file, forms)

    counts: Counter = Counter()
    for pair in pairs:
        seen = set()
        for w in pair.get("words", []):
            l = w["lemma"].casefold()
            if l not in seen:
                counts[l] += 1
                seen.add(l)

    missing: list[tuple[str, int]] = []
    for lemma, cnt in counts.most_common():
        if lemma in known:
            continue
        if len(lemma) <= 1:
            continue
        if cnt < 5:
            continue
        missing.append((lemma, cnt))

    result: list[dict[str, Any]] = []
    for lemma, _ in missing[:num_words]:
        result.append({"word": lemma, "pos": pos_by_lemma.get(lemma, "")})
    return result


def translate(words: list[dict[str, Any]], api_key: str, model: str = "gpt-4o-mini") -> dict[str, Any]:
    """Translate a batch of French words using an LLM.

    *words* is a list of dicts with keys ``word`` (str) and ``pos`` (str | "").
    Returns dict mapping lowercase lemma -> {"word": ..., "pos": ..., "senses": {1: [...], 2: [...]}}.
    """
    results: dict[str, Any] = {}
    batch_size = 80

    for i in range(0, len(words), batch_size):
        batch = words[i : i + batch_size]
        lines = []
        for w in batch:
            line = f"- {w['word']}"
            if w.get("pos"):
                line += f" ({w['pos']})"
            lines.append(line)
        prompt = (
            "You are a French-English dictionary. Translate each French word into English.\n"
            "For each word, provide its part of speech and numbered sense groups.\n"
            "Output exactly one JSON object per line:\n"
            '{"word": "...", "pos": "n|v|adj|adv|...", "senses": {"1": ["trans1a", "trans1b"], "2": ["trans2"]}}\n\n'
            + "\n".join(lines)
        )

        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 3000,
            },
            timeout=90,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                w = d.get("word", "").casefold()
                senses = d.get("senses", {})
                if w and senses:
                    results[w] = d
            except (json.JSONDecodeError, KeyError):
                continue

        ok = sum(1 for w in batch if w["word"].casefold() in results)
        print(f"  batch {i // batch_size + 1}: {ok}/{len(batch)} ok")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TEI for missing French words via LLM")
    parser.add_argument("--output", type=Path, default=Path("app/language_data/french/auto-generated.tei"))
    parser.add_argument("--num-words", type=int, default=500, help="Number of most-frequent missing words to translate")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--api-key")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: --api-key or OPENAI_API_KEY required")
        return

    cfg = load_config()
    print("Finding missing words...")
    word_list = get_missing_words(cfg, args.num_words)
    print(f"Translating {len(word_list)} missing words with {args.model}...")
    translations = translate(word_list, api_key, args.model)

    entries: list[Element] = []
    for item in word_list:
        w = item["word"]
        if w not in translations:
            continue
        d = translations[w]
        senses = d.get("senses", {})
        if not senses:
            continue
        entries.append(_make_entry(w, d.get("pos", item.get("pos", "")), senses))
    tei = _build_tei(entries)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(tei, encoding="unicode")
    args.output.write_text(xml, encoding="utf-8")

    print(f"\nWrote {len(entries)} entries to {args.output}")
    for item in word_list[:10]:
        w = item["word"]
        if w in translations:
            d = translations[w]
            print(f"  {w} ({d.get('pos', '?')}): {d['senses']}")


if __name__ == "__main__":
    main()