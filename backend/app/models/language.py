from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.associations import user_languages


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)

    users = relationship("User", secondary=user_languages, back_populates="languages")
    lexical_items = relationship("LexicalItem", back_populates="language")
    sentences = relationship("Sentence", back_populates="language")