from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Language, LexicalItem

router = APIRouter(prefix="/languages", tags=["languages"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def list_languages(db: Session = Depends(get_db)):
    result = db.execute(
        select(
            Language.name,
            func.count(LexicalItem.id).label("word_count"),
        )
        .outerjoin(LexicalItem, LexicalItem.language_id == Language.id)
        .group_by(Language.name)
        .order_by(Language.name)
    ).all()

    languages = [
        {
            "name": name,
            "word_count": word_count,
            "video_count": 0,  # placeholder, no video data yet
        }
        for name, word_count in result
    ]
    return {"languages": languages}