from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SenseTranslation(Base):
    __tablename__ = "sense_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sense_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_senses.id", ondelete="CASCADE"), nullable=False
    )
    translation: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    sense = relationship("LexicalSense", back_populates="translations")
