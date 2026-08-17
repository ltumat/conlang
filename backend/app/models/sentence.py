from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.associations import sentence_lexical_items


class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    translation = Column(String)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)

    language = relationship("Language", back_populates="sentences")
    lexical_items = relationship(
        "LexicalItem",
        secondary=sentence_lexical_items,
        back_populates="sentences",
    )
