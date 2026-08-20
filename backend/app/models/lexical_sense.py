from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LexicalSense(Base):
    __tablename__ = "lexical_senses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lexical_item_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_items.id", ondelete="CASCADE"), nullable=False
    )
    sense_number: Mapped[int] = mapped_column(Integer, nullable=False)

    lexical_item = relationship("LexicalItem", back_populates="senses")
    translations = relationship(
        "SenseTranslation", back_populates="sense", cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "Embedding", back_populates="sense", cascade="all, delete-orphan"
    )
