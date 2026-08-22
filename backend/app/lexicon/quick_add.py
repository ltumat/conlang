"""Quick-add script that reads a simple CSV/TSV line and inserts the item.

This is meant for very fast manual addition of single items discovered
outside the big-batch pipeline. It uses a simple positional format:

  Word:
    fra, bonjour, int, hello|good morning
    fra, merci, n, thank you|thanks

  Sentence:
    fra, Bonjour tout le monde !, Hello everyone!

  Occurrence:
    15, 42, Bonjour, 0, 7


Usage:
    echo "fra,bonjour,int,\"hello|good morning\"" | python -m app.lexicon.quick_add word
    echo "fra,\"Bonjour tout le monde !\",\"Hello everyone!\"" | python -m app.lexicon.quick_add sentence
    echo "15,42,Bonjour,0,7" | python -m app.lexicon.quick_add occurrence

Fields:
    word:       lang_code, word, [pos], [sense1|sense2|...]
    sentence:   lang_code, text, [translation]
    occurrence: sentence_id, lexical_item_id, surface, start, end
"""

from __future__ import annotations

import argparse
import csv
import sys

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

_PART_OF_SPEECH = {
    "adj": "adjective", "adv": "adverb", "art": "article",
    "conj": "conjunction", "int": "interjection", "n": "noun",
    "num": "numeral", "prep": "preposition", "pron": "pronoun",
    "v": "verb", "vi": "intransitive verb", "vt": "transitive verb",
}


def add_word(row: list[str]) -> None:
    """CSV: lang_code, word, [pos], [senses_pipe_separated]"""
    lang_code = row[0].strip()
    word = row[1].strip()
    pos = row[2].strip() if len(row) > 2 and row[2].strip() else None
    senses_raw = row[3].strip() if len(row) > 3 and row[3].strip() else ""

    with SessionLocal() as session:
        lang = session.scalar(
            Language.__table__.select().where(Language.code == lang_code)
        )
        if lang is None:
            print(f"⛔ Language '{lang_code}' not found.", file=sys.stderr)
            return

        filters = [
            LexicalItem.language_id == lang.id,
            LexicalItem.word == word,
        ]
        if pos:
            filters.append(LexicalItem.part_of_speech_code == pos)
        existing = session.scalar(
            LexicalItem.__table__.select().where(*filters)
        )
        if existing is not None:
            print(f"⏭️  Word '{word}' already exists (id={existing.id}).")
            return

        item = LexicalItem(
            word=word,
            part_of_speech_code=pos,
            language_id=lang.id,
        )
        session.add(item)
        session.flush()

        if senses_raw:
            for i, trans in enumerate(senses_raw.split("|"), start=1):
                sense = LexicalSense(lexical_item_id=item.id, sense_number=i)
                session.add(sense)
                session.flush()
                session.add(SenseTranslation(sense_id=sense.id, translation=trans.strip(), position=1))

        session.commit()
        print(f"✅ Word '{word}' (id={item.id}) added to {lang.name}.")


def add_sentence(row: list[str]) -> None:
    """CSV: lang_code, text, [translation]"""
    lang_code = row[0].strip()
    text = row[1].strip()
    translation = row[2].strip() if len(row) > 2 and row[2].strip() else None

    with SessionLocal() as session:
        lang = session.scalar(
            Language.__table__.select().where(Language.code == lang_code)
        )
        if lang is None:
            print(f"⛔ Language '{lang_code}' not found.", file=sys.stderr)
            return

        existing = session.scalar(
            Sentence.__table__.select().where(
                Sentence.language_id == lang.id, Sentence.text == text
            )
        )
        if existing is not None:
            print(f"⏭️  Sentence already exists (id={existing.id}).")
            return

        sent = Sentence(text=text, language_id=lang.id)
        session.add(sent)
        session.flush()

        if translation:
            session.add(SentenceTranslation(sentence_id=sent.id, translation=translation))

        session.commit()
        print(f"✅ Sentence (id={sent.id}) added.")


def add_occurrence(row: list[str]) -> None:
    """CSV: sentence_id, lexical_item_id, surface, start, end"""
    sentence_id = int(row[0])
    lexical_item_id = int(row[1])
    surface = row[2].strip()
    start_offset = int(row[3])
    end_offset = int(row[4])

    with SessionLocal() as session:
        sent = session.get(Sentence, sentence_id)
        if sent is None:
            print(f"⛔ Sentence id={sentence_id} not found.", file=sys.stderr)
            return
        item = session.get(LexicalItem, lexical_item_id)
        if item is None:
            print(f"⛔ LexicalItem id={lexical_item_id} not found.", file=sys.stderr)
            return

        occ = SentenceWordOccurrence(
            sentence_id=sentence_id,
            lexical_item_id=lexical_item_id,
            surface_form=surface,
            start_offset=start_offset,
            end_offset=end_offset,
            match_method="manual",
        )
        session.add(occ)
        session.commit()
        print(f"✅ Occurrence '{surface}' → '{item.word}' in sentence id={sentence_id}.")


CMDS = {
    "word": add_word,
    "sentence": add_sentence,
    "occurrence": add_occurrence,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick-add items from piped CSV lines.")
    parser.add_argument("command", choices=list(CMDS), help="Type of item to add")
    parser.add_argument("--delimiter", default=",")
    args = parser.parse_args()

    reader = csv.reader(sys.stdin, delimiter=args.delimiter)
    for row in reader:
        if not row or row[0].startswith("#"):
            continue
        CMDS[args.command](row)


if __name__ == "__main__":
    main()