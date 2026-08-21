from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.lexicon.embedding_config import load_config
from app.lexicon.sentence_loader import load_lexique_forms, load_sentence_pairs
from app.lexicon.tei_loader import load_tei_entries
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

BATCH_SIZE = 2_000


def get_language(session: Session, name: str, code: str) -> Language:
    language = session.scalar(select(Language).where(Language.code == code))
    if language is None:
        language = Language(name=name, code=code)
        session.add(language)
        session.flush()
    return language


def import_lexicon(
    session: Session, entries: list[dict], language: Language
) -> dict[str, list[LexicalItem]]:
    """Import TEI entries using preloaded lookups instead of per-row queries."""
    items = session.scalars(
        select(LexicalItem).where(LexicalItem.language_id == language.id)
    ).all()
    item_by_key = {
        (item.word, item.part_of_speech_code, item.gender): item for item in items
    }
    senses = session.scalars(
        select(LexicalSense).join(LexicalItem).where(
            LexicalItem.language_id == language.id
        )
    ).all()
    sense_by_key = {
        (sense.lexical_item_id, sense.sense_number): sense for sense in senses
    }
    translations = session.scalars(select(SenseTranslation)).all()
    translation_keys = {
        (translation.sense_id, translation.position) for translation in translations
    }
    new_items: list[LexicalItem] = []
    new_senses: list[LexicalSense] = []
    items_by_word: dict[str, list[LexicalItem]] = {}

    for entry in entries:
        word = entry.get("word")
        if not word:
            continue
        key = (word, entry.get("part_of_speech_code"), entry.get("gender"))
        item = item_by_key.get(key)
        if item is None:
            item = LexicalItem(
                word=word,
                pronunciation=entry.get("pronunciation"),
                part_of_speech_code=entry.get("part_of_speech_code"),
                part_of_speech=entry.get("part_of_speech"),
                gender=entry.get("gender"),
                source_entry_id=entry.get("id"),
                language_id=language.id,
            )
            session.add(item)
            new_items.append(item)
            item_by_key[key] = item
        items_by_word.setdefault(word.casefold(), []).append(item)

    session.flush()
    for entry in entries:
        word = entry.get("word")
        if not word:
            continue
        item = item_by_key[
            (word, entry.get("part_of_speech_code"), entry.get("gender"))
        ]
        for index, sense_data in enumerate(entry.get("senses", []), start=1):
            number = sense_data.get("number", index)
            sense = sense_by_key.get((item.id, number))
            if sense is None:
                sense = LexicalSense(lexical_item_id=item.id, sense_number=number)
                session.add(sense)
                new_senses.append(sense)
                session.flush()
                sense_by_key[(item.id, number)] = sense
            for position, translation in enumerate(
                sense_data.get("translations", []), start=1
            ):
                if (sense.id, position) not in translation_keys:
                    session.add(
                        SenseTranslation(
                            sense_id=sense.id,
                            translation=translation,
                            position=position,
                        )
                    )
                    translation_keys.add((sense.id, position))
    session.flush()
    print(f"Lexicon: {len(new_items)} new items, {len(new_senses)} new senses")
    return items_by_word


def import_lexique_forms(
    session: Session,
    lexique_path: str | Path,
    items_by_word: dict[str, list[LexicalItem]],
) -> int:
    """Import observed forms using one query and one bulk insert batch."""
    forms = load_lexique_forms(lexique_path)
    item_ids = {item.id for items in items_by_word.values() for item in items}
    existing = session.scalars(
        select(LexicalForm).where(LexicalForm.lexical_item_id.in_(item_ids))
    ).all()
    existing_keys = {(form.lexical_item_id, form.form) for form in existing}
    new_forms: list[LexicalForm] = []
    for surface, lemmas in forms.items():
        for lemma in lemmas:
            for item in items_by_word.get(lemma.casefold(), []):
                key = (item.id, surface)
                if key not in existing_keys:
                    new_forms.append(
                        LexicalForm(
                            lexical_item_id=item.id,
                            form=surface,
                            form_type="observed",
                            features={},
                        )
                    )
                    existing_keys.add(key)
    session.add_all(new_forms)
    session.flush()
    print(f"Lexical forms: {len(new_forms)} new forms")
    return len(new_forms)


def import_sentences(
    session: Session,
    sentence_pairs: list[dict],
    items_by_word: dict[str, list[LexicalItem]],
    language: Language,
) -> tuple[int, int, int]:
    """Import sentences with in-memory indexes and periodic progress output."""
    sentences = session.scalars(
        select(Sentence).where(Sentence.language_id == language.id)
    ).all()
    sentence_by_text = {sentence.text: sentence for sentence in sentences}
    sentence_translations = session.scalars(select(SentenceTranslation)).all()
    translation_keys = {
        (translation.sentence_id, translation.translation)
        for translation in sentence_translations
    }
    occurrences = session.scalars(select(SentenceWordOccurrence)).all()
    occurrence_keys = {
        (
            occurrence.sentence_id,
            occurrence.lexical_item_id,
            occurrence.start_offset,
            occurrence.end_offset,
        )
        for occurrence in occurrences
    }
    new_sentences: list[Sentence] = []
    new_translations: list[SentenceTranslation] = []
    new_occurrences: list[SentenceWordOccurrence] = []
    sentence_count = translation_count = occurrence_count = 0

    for index, pair in enumerate(sentence_pairs, start=1):
        sentence = sentence_by_text.get(pair["text"])
        if sentence is None:
            sentence = Sentence(
                text=pair["text"],
                source_sentence_id=pair.get("sentence_id"),
                language_id=language.id,
            )
            session.add(sentence)
            session.flush()
            sentence_by_text[sentence.text] = sentence
            new_sentences.append(sentence)
            sentence_count += 1
        translation_key = (sentence.id, pair["translation"])
        if translation_key not in translation_keys:
            new_translations.append(
                SentenceTranslation(
                    sentence_id=sentence.id,
                    translation=pair["translation"],
                    source_translation_id=pair.get("pair_id"),
                )
            )
            translation_keys.add(translation_key)
            translation_count += 1
        for match in pair.get("words", []):
            for item in items_by_word.get(match["lemma"].casefold(), []):
                occurrence_key = (
                    sentence.id,
                    item.id,
                    match["start"],
                    match["end"],
                )
                if occurrence_key not in occurrence_keys:
                    new_occurrences.append(
                        SentenceWordOccurrence(
                            sentence_id=sentence.id,
                            lexical_item_id=item.id,
                            surface_form=match["surface"],
                            start_offset=match["start"],
                            end_offset=match["end"],
                            match_method="lexique_exact_form",
                        )
                    )
                    occurrence_keys.add(occurrence_key)
                    occurrence_count += 1
        if len(new_translations) >= BATCH_SIZE:
            session.add_all(new_translations)
            session.add_all(new_occurrences)
            session.flush()
            new_translations.clear()
            new_occurrences.clear()
        if index % 10_000 == 0:
            print(f"Sentences: processed {index:,}/{len(sentence_pairs):,}")

    session.add_all(new_translations)
    session.add_all(new_occurrences)
    session.flush()
    print(
        f"Sentences: {sentence_count} new, {translation_count} translations, "
        f"{occurrence_count} occurrences"
    )
    return sentence_count, translation_count, occurrence_count


def populate_database(
    tei_file: str | Path,
    sentences_file: str | Path,
    lexique_file: str | Path,
    language_name: str = "French",
    language_code: str = "fra",
) -> dict[str, int]:
    print("Loading source files...")
    entries = load_tei_entries(tei_file)
    forms = load_lexique_forms(lexique_file)
    sentence_pairs = load_sentence_pairs(sentences_file, forms)
    print(
        f"Loaded {len(entries):,} entries and "
        f"{len(sentence_pairs):,} sentence pairs"
    )
    with SessionLocal() as session:
        try:
            language = get_language(session, language_name, language_code)
            items_by_word = import_lexicon(session, entries, language)
            lexical_forms = import_lexique_forms(
                session, lexique_file, items_by_word
            )
            sentence_counts = import_sentences(
                session, sentence_pairs, items_by_word, language
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
    return {
        "entries": len(entries),
        "lexical_items": sum(len(items) for items in items_by_word.values()),
        "lexical_forms": lexical_forms,
        "sentences": sentence_counts[0],
        "sentence_translations": sentence_counts[1],
        "word_occurrences": sentence_counts[2],
    }


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description="Populate the French database")
    parser.add_argument("--tei-file", type=Path, default=config.tei_file)
    parser.add_argument("--sentences-file", type=Path, default=config.sentences_file)
    parser.add_argument("--lexique-file", type=Path, default=config.lexique_file)
    args = parser.parse_args()
    print(populate_database(**vars(args)))


if __name__ == "__main__":
    main()
