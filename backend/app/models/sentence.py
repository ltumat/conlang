from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sentence(Base):
    __tablename__ = "sentences"
    __table_args__ = (UniqueConstraint("language_id", "text"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    source_sentence_id: Mapped[str | None] = mapped_column(String)
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id"), nullable=False
    )

    language = relationship("Language", back_populates="sentences")
    translations = relationship(
        "SentenceTranslation", back_populates="sentence", cascade="all, delete-orphan"
    )
    occurrences = relationship(
        "SentenceWordOccurrence",
        back_populates="sentence",
        cascade="all, delete-orphan",
    )
    embeddings = relationship(
        "Embedding", back_populates="sentence", cascade="all, delete-orphan"
    )
