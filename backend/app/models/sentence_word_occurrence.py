from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SentenceWordOccurrence(Base):
    __tablename__ = "sentence_word_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "sentence_id",
            "lexical_item_id",
            "start_offset",
            "end_offset",
            name="uq_sentence_word_occurrences_span",
        ),
        Index(
            "ix_sentence_word_occurrences_item",
            "lexical_item_id",
            "sentence_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False
    )
    lexical_item_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_items.id"), nullable=False
    )
    surface_form: Mapped[str] = mapped_column(String, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    match_method: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)

    sentence = relationship("Sentence", back_populates="occurrences")
    lexical_item = relationship("LexicalItem", back_populates="sentence_occurrences")
