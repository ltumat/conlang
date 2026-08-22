from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SenseTranslation(Base):
    __tablename__ = "sense_translations"
    __table_args__ = (UniqueConstraint("sense_id", "position", name="uq_sense_translations_sense_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sense_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_senses.id", ondelete="CASCADE"), nullable=False
    )
    translation: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    sense = relationship("LexicalSense", back_populates="translations")
