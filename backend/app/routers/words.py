from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models import Language, LexicalForm, LexicalItem, LexicalSense, SenseTranslation

router = APIRouter(prefix="/words", tags=["words"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _word_to_dict(item: LexicalItem) -> dict:
    senses = []
    for sense in sorted(item.senses, key=lambda s: s.sense_number):
        senses.append(
            {
                "number": sense.sense_number,
                "translations": [t.translation for t in sense.translations],
            }
        )

    # Group verb forms into conjugations by form_type
    conjugations: dict[str, dict[str, str] | str] = {}
    for form in item.forms:
        if form.form_type == "conjugation":
            tense = form.features.get("tense", "present")
            person = form.features.get("person", "")
            if tense not in conjugations:
                conjugations[tense] = {}
            if isinstance(conjugations[tense], dict):
                conjugations[tense][person] = form.form
        elif form.form_type == "past_participle":
            conjugations["past_participle"] = form.form

    result: dict = {
        "word": item.word,
        "pronunciation": item.pronunciation,
        "part_of_speech": item.part_of_speech or item.part_of_speech_code,
        "gender": item.gender,
        "senses": senses,
    }
    if conjugations:
        result["conjugations"] = conjugations
    return result


@router.get("/")
async def list_words(language: str = "French", db: Session = Depends(get_db)):
    lang = db.scalar(select(Language).where(Language.name == language))
    if lang is None:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not found")

    items = (
        db.execute(
            select(LexicalItem)
            .where(LexicalItem.language_id == lang.id)
            .options(
                joinedload(LexicalItem.senses).joinedload(LexicalSense.translations),
                joinedload(LexicalItem.forms),
            )
            .order_by(LexicalItem.word)
        )
        .unique()
        .scalars()
        .all()
    )
    return {"words": [_word_to_dict(item) for item in items]}


@router.get("/{word}")
async def get_word(word: str, language: str = "French", db: Session = Depends(get_db)):
    lang = db.scalar(select(Language).where(Language.name == language))
    if lang is None:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not found")

    item = db.scalar(
        select(LexicalItem).where(
            LexicalItem.language_id == lang.id, LexicalItem.word == word
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Word not found")

    # Load relationships
    db.execute(
        select(LexicalItem)
        .where(LexicalItem.id == item.id)
        .options(
            joinedload(LexicalItem.senses).joinedload(LexicalSense.translations),
            joinedload(LexicalItem.forms),
        )
    )

    return {"word": _word_to_dict(item)}