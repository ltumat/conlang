from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class LexicalItem(Base):
    __tablename__ = "lexical_items"
    __table_args__ = (
        UniqueConstraint(
            "language_id",
            "word",
            "part_of_speech_code",
            "gender",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    pronunciation = Column(String)
    part_of_speech_code = Column(String(10))
    part_of_speech = Column(String)
    gender = Column(String(10))
    source_entry_id = Column(Integer)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)

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
