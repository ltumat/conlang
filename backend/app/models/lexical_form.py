from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LexicalForm(Base):
    __tablename__ = "lexical_forms"
    __table_args__ = (
        UniqueConstraint(
            "lexical_item_id",
            "form_type",
            "form",
            name="uq_lexical_forms_item_type_form",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lexical_item_id: Mapped[int] = mapped_column(
        ForeignKey("lexical_items.id", ondelete="CASCADE"), nullable=False
    )
    form: Mapped[str] = mapped_column(String, nullable=False)
    form_type: Mapped[str] = mapped_column(String(30), nullable=False)
    features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    lexical_item = relationship("LexicalItem", back_populates="forms")
