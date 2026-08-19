from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.associations import sentence_lexical_items


class LexicalItem(Base):
    __tablename__ = "lexical_items"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False)
    translation = Column(String)
    category = Column(String)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)

    language = relationship("Language", back_populates="lexical_items")
    sentences = relationship(
        "Sentence",
        secondary=sentence_lexical_items,
        back_populates="lexical_items",
    )
    embeddings = relationship(
        "WordEmbedding", back_populates="lexical_item", cascade="all, delete-orphan"
    )
