from sqlalchemy import Table, Column, Integer, ForeignKey

from app.database import Base

user_languages = Table(
    "user_languages",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("language_id", Integer, ForeignKey("languages.id"), primary_key=True),
)

sentence_lexical_items = Table(
    "sentence_lexical_items",
    Base.metadata,
    Column("sentence_id", Integer, ForeignKey("sentences.id"), primary_key=True),
    Column("lexical_item_id", Integer, ForeignKey("lexical_items.id"), primary_key=True),
    Column("position", Integer),
)
