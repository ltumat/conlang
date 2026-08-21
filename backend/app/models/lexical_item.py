from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LexicalItem(Base):
    __tablename__ = "lexical_items"
    __table_args__ = (
        UniqueConstraint(
            "language_id", "word", "part_of_speech_code", "gender"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    word: Mapped[str] = mapped_column(String, nullable=False)
    pronunciation: Mapped[str | None] = mapped_column(String)
    part_of_speech_code: Mapped[str | None] = mapped_column(String(10))
    part_of_speech: Mapped[str | None] = mapped_column(String)
    gender: Mapped[str | None] = mapped_column(String(10))
    source_entry_id: Mapped[int | None] = mapped_column(Integer)
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id"), nullable=False
    )

    language = relationship("Language", back_populates="lexical_items")
    senses = relationship(
        "LexicalSense", back_populates="lexical_item", cascade="all, delete-orphan"
    )
    forms = relationship(
        "LexicalForm", back_populates="lexical_item", cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "Embedding", back_populates="lexical_item", cascade="all, delete-orphan"
    )
    sentence_occurrences = relationship(
        "SentenceWordOccurrence", back_populates="lexical_item"
    )
