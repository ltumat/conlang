from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.lexicon.embedding_config import embedding_dimensions


class WordEmbedding(Base):
    """An embedding for one lexical item, retaining which model created it."""

    __tablename__ = "word_embeddings"
    __table_args__ = (
        UniqueConstraint("lexical_item_id", "model_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lexical_item_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_items.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(embedding_dimensions()), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    lexical_item = relationship("LexicalItem", back_populates="embeddings")
