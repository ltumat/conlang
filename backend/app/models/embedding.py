from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.lexicon.embedding_config import EMBEDDING_DIMENSIONS


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('word', 'sense', 'sentence', 'sentence_pair')",
            name="ck_embedding_content_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    lexical_item_id: Mapped[int | None] = mapped_column(ForeignKey("lexical_items.id"))
    sense_id: Mapped[int | None] = mapped_column(ForeignKey("lexical_senses.id"))
    sentence_id: Mapped[int | None] = mapped_column(ForeignKey("sentences.id"))
    sentence_translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("sentence_translations.id")
    )
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    lexical_item = relationship("LexicalItem", back_populates="embeddings")
    sense = relationship("LexicalSense", back_populates="embeddings")
    sentence = relationship("Sentence", back_populates="embeddings")
    sentence_translation = relationship(
        "SentenceTranslation", back_populates="embeddings"
    )
