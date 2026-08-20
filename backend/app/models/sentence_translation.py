from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SentenceTranslation(Base):
    __tablename__ = "sentence_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False
    )
    translation: Mapped[str] = mapped_column(String, nullable=False)
    source_translation_id: Mapped[str | None] = mapped_column(String)

    sentence = relationship("Sentence", back_populates="translations")
    embeddings = relationship(
        "Embedding", back_populates="sentence_translation", cascade="all, delete-orphan"
    )
