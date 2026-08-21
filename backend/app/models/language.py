from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.lexical_item import LexicalItem
    from app.models.sentence import Sentence
    from app.models.user import User
from app.models.associations import user_languages


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(
        "User", secondary=user_languages, back_populates="languages"
    )
    lexical_items: Mapped[list[LexicalItem]] = relationship(
        "LexicalItem", back_populates="language"
    )
    sentences: Mapped[list[Sentence]] = relationship(
        "Sentence", back_populates="language"
    )
