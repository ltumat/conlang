"""Incremental scripts for adding individual words, senses, sentences, and
translations outside of the big-batch import pipeline.

Usage:
    python -m app.lexicon.add_item word --lang fra --word "bonjour" --pos "int" --sense "hello" --sense "good morning"
    python -m app.lexicon.add_item sense --word-id 42 --number 3 --translation "figuratively: a warm welcome"
    python -m app.lexicon.add_item translation --sense-id 7 --translation "cat (animal)" --position 2
    python -m app.lexicon.add_item form --word-id 42 --form "bonjours" --type "plural"
    python -m app.lexicon.add_item sentence --lang fra --text "Bonjour tout le monde !" --translation "Hello everyone!"
    python -m app.lexicon.add_item occurrence --sentence-id 15 --word-id 42 --surface "Bonjour" --start 0 --end 7

All commands commit immediately on success and rollback on failure.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    Language,
    LexicalForm,
    LexicalItem,
    LexicalSense,
    SenseTranslation,
    Sentence,
    SentenceTranslation,
    SentenceWordOccurrence,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_language(session: Any, code: str) -> Language:
    lang = session.scalar(select(Language).where(Language.code == code))
    if lang is None:
        print(f"Error: language code '{code}' not found. Create it first.", file=sys.stderr)
        sys.exit(1)
    return lang


def _get_lexical_item(session: Any, word: str, lang: Language,
                      pos: str | None = None, gender: str | None = None) -> LexicalItem | None:
    """Find a matching lexical item, or return None."""
    stmt = select(LexicalItem).where(
        LexicalItem.language_id == lang.id,
        LexicalItem.word == word,
    )
    if pos is not None:
        stmt = stmt.where(LexicalItem.part_of_speech_code == pos)
    if gender is not None:
        stmt = stmt.where(LexicalItem.gender == gender)
    return session.scalar(stmt)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_word(args: argparse.Namespace) -> None:
    """Add a new lexical item (word) with optional senses/translations."""
    with SessionLocal() as session:
        try:
            lang = _get_language(session, args.lang)
            existing = _get_lexical_item(session, args.word, lang, args.pos, args.gender)
            if existing is not None:
                print(f"Word '{args.word}' already exists (id={existing.id}). Use 'sense' or 'translation' subcommand to extend it.")
                return

            item = LexicalItem(
                word=args.word,
                pronunciation=args.pronunciation,
                part_of_speech_code=args.pos,
                gender=args.gender,
                language_id=lang.id,
            )
            session.add(item)
            session.flush()
            print(f"Created lexical item id={item.id}: '{args.word}'")

            # Add senses if provided
            for i, translation in enumerate(args.sense or [], start=1):
                sense = LexicalSense(lexical_item_id=item.id, sense_number=i)
                session.add(sense)
                session.flush()
                st = SenseTranslation(sense_id=sense.id, translation=translation, position=1)
                session.add(st)
                print(f"  sense #{i}: '{translation}'")

            session.commit()
            print(f"Committed word '{args.word}' (id={item.id}).")
        except Exception:
            session.rollback()
            raise


def cmd_sense(args: argparse.Namespace) -> None:
    """Add a new sense to an existing lexical item."""
    with SessionLocal() as session:
        try:
            item = session.get(LexicalItem, args.word_id)
            if item is None:
                print(f"Error: no lexical item with id={args.word_id}.", file=sys.stderr)
                sys.exit(1)

            # Determine next sense number
            max_num = max((s.sense_number for s in item.senses), default=0)
            sense_number = args.number if args.number is not None else max_num + 1
            sense = LexicalSense(lexical_item_id=item.id, sense_number=sense_number)
            session.add(sense)
            session.flush()

            for pos, trans in enumerate(args.translation or [], start=1):
                session.add(SenseTranslation(sense_id=sense.id, translation=trans, position=pos))
                print(f"  translation #{pos}: '{trans}'")
            session.commit()
            print(f"Added sense #{sense_number} to '{item.word}' (sense id={sense.id}).")
        except Exception:
            session.rollback()
            raise


def cmd_translation(args: argparse.Namespace) -> None:
    """Add a translation to an existing sense."""
    with SessionLocal() as session:
        try:
            sense = session.get(LexicalSense, args.sense_id)
            if sense is None:
                print(f"Error: no sense with id={args.sense_id}.", file=sys.stderr)
                sys.exit(1)
            st = SenseTranslation(
                sense_id=sense.id,
                translation=args.translation,
                position=args.position,
            )
            session.add(st)
            session.commit()
            print(f"Added translation '{args.translation}' to sense id={sense.id}.")
        except Exception:
            session.rollback()
            raise


def cmd_form(args: argparse.Namespace) -> None:
    """Add a lexical form (inflected variant) to an existing word."""
    import json as _json
    with SessionLocal() as session:
        try:
            item = session.get(LexicalItem, args.word_id)
            if item is None:
                print(f"Error: no lexical item with id={args.word_id}.", file=sys.stderr)
                sys.exit(1)
            features = {}
            if args.features:
                features = _json.loads(args.features)
            form = LexicalForm(
                lexical_item_id=item.id,
                form=args.form,
                form_type=args.type,
                features=features,
            )
            session.add(form)
            session.commit()
            print(f"Added form '{args.form}' ({args.type}) to '{item.word}'.")
        except Exception:
            session.rollback()
            raise


def cmd_sentence(args: argparse.Namespace) -> None:
    """Add a sentence with an optional translation."""
    with SessionLocal() as session:
        try:
            lang = _get_language(session, args.lang)

            # Check for duplicate
            existing = session.scalar(
                select(Sentence).where(
                    Sentence.language_id == lang.id,
                    Sentence.text == args.text,
                )
            )
            if existing is not None:
                print(f"Sentence already exists (id={existing.id}). Skipping.")
                return

            sentence = Sentence(
                text=args.text,
                language_id=lang.id,
                source_sentence_id=args.source_id,
            )
            session.add(sentence)
            session.flush()

            if args.translation:
                st = SentenceTranslation(
                    sentence_id=sentence.id,
                    translation=args.translation,
                )
                session.add(st)
                print(f"  translation: '{args.translation}'")

            session.commit()
            print(f"Added sentence id={sentence.id}.")
        except Exception:
            session.rollback()
            raise


def cmd_occurrence(args: argparse.Namespace) -> None:
    """Link a lexical item to a sentence occurrence."""
    with SessionLocal() as session:
        try:
            sentence = session.get(Sentence, args.sentence_id)
            if sentence is None:
                print(f"Error: no sentence with id={args.sentence_id}.", file=sys.stderr)
                sys.exit(1)
            item = session.get(LexicalItem, args.word_id)
            if item is None:
                print(f"Error: no lexical item with id={args.word_id}.", file=sys.stderr)
                sys.exit(1)
            occ = SentenceWordOccurrence(
                sentence_id=sentence.id,
                lexical_item_id=item.id,
                surface_form=args.surface,
                start_offset=args.start,
                end_offset=args.end,
                match_method=args.method or "manual",
                confidence=args.confidence,
            )
            session.add(occ)
            session.commit()
            print(f"Linked '{item.word}' → sentence id={sentence.id} (offset {args.start}:{args.end}).")
        except Exception:
            session.rollback()
            raise


# ---------------------------------------------------------------------------
# POS lookup (mirrors tei_loader)
# ---------------------------------------------------------------------------

_PART_OF_SPEECH = {
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add individual items to the conlang database.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # word
    p_word = sub.add_parser("word", help="Add a new lexical item (word)")
    p_word.add_argument("--lang", required=True, help="Language code (e.g. 'fra', 'eng')")
    p_word.add_argument("--word", required=True, help="The word / headword")
    p_word.add_argument("--pronunciation", help="Pronunciation string")
    p_word.add_argument("--pos", help="Part-of-speech code (n, v, adj, adv, ...)")
    p_word.add_argument("--gender", help="Gender (m, f, n)")
    p_word.add_argument("--sense", nargs="*", help="One or more sense translations", default=[])

    # sense
    p_sense = sub.add_parser("sense", help="Add a new sense to an existing word")
    p_sense.add_argument("--word-id", type=int, required=True, help="LexicalItem id")
    p_sense.add_argument("--number", type=int, help="Sense number (auto if omitted)")
    p_sense.add_argument("--translation", nargs="*", help="Translations for this sense", default=[])

    # translation
    p_trans = sub.add_parser("translation", help="Add a translation to an existing sense")
    p_trans.add_argument("--sense-id", type=int, required=True, help="LexicalSense id")
    p_trans.add_argument("--translation", required=True, help="Translation text")
    p_trans.add_argument("--position", type=int, default=1, help="Ordinal position")

    # form
    p_form = sub.add_parser("form", help="Add an inflected form to a word")
    p_form.add_argument("--word-id", type=int, required=True, help="LexicalItem id")
    p_form.add_argument("--form", required=True, help="Inflected form string")
    p_form.add_argument("--type", required=True, help="Form type (conjugation, observed, plural, ...)")
    p_form.add_argument("--features", help="JSON string of features (optional)")

    # sentence
    p_sent = sub.add_parser("sentence", help="Add a sentence")
    p_sent.add_argument("--lang", required=True, help="Language code")
    p_sent.add_argument("--text", required=True, help="Sentence text")
    p_sent.add_argument("--translation", help="Optional translation")
    p_sent.add_argument("--source-id", help="Source sentence id (e.g. Tatoeba id)")

    # occurrence
    p_occ = sub.add_parser("occurrence", help="Link a word occurrence in a sentence")
    p_occ.add_argument("--sentence-id", type=int, required=True, help="Sentence id")
    p_occ.add_argument("--word-id", type=int, required=True, help="LexicalItem id")
    p_occ.add_argument("--surface", required=True, help="Surface form in the sentence")
    p_occ.add_argument("--start", type=int, required=True, help="Start offset (char index)")
    p_occ.add_argument("--end", type=int, required=True, help="End offset (exclusive char index)")
    p_occ.add_argument("--method", default="manual", help="Match method")
    p_occ.add_argument("--confidence", type=float, help="Confidence score (0-1)")

    return parser


CMDS = {
    "word": cmd_word,
    "sense": cmd_sense,
    "translation": cmd_translation,
    "form": cmd_form,
    "sentence": cmd_sentence,
    "occurrence": cmd_occurrence,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    CMDS[args.command](args)


if __name__ == "__main__":
    main()