"""Convert embedding partial indexes from non-unique to unique

Each (model_name, content_type, item_fk) combination should have at most
one embedding row. The unique partial indexes enforce this at the DB level.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "756993beee95"
down_revision: Union[str, None] = "a1237a92cec6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_INDEXES = [
    ("ix_embeddings_model_content_item", ["model_name", "content_type", "lexical_item_id"]),
    ("ix_embeddings_model_content_sense", ["model_name", "content_type", "sense_id"]),
    ("ix_embeddings_model_content_sentence", ["model_name", "content_type", "sentence_id"]),
    ("ix_embeddings_model_content_translation", ["model_name", "content_type", "sentence_translation_id"]),
]

_WHERE_CLAUSES = {
    "ix_embeddings_model_content_item": "lexical_item_id IS NOT NULL",
    "ix_embeddings_model_content_sense": "sense_id IS NOT NULL",
    "ix_embeddings_model_content_sentence": "sentence_id IS NOT NULL",
    "ix_embeddings_model_content_translation": "sentence_translation_id IS NOT NULL",
}


def upgrade() -> None:
    for name, columns in _INDEXES:
        op.drop_index(name, table_name="embeddings", postgresql_where=_WHERE_CLAUSES[name])
        op.create_index(
            name,
            "embeddings",
            columns,
            unique=True,
            postgresql_where=_WHERE_CLAUSES[name],
        )


def downgrade() -> None:
    for name, columns in reversed(_INDEXES):
        op.drop_index(name, table_name="embeddings", postgresql_where=_WHERE_CLAUSES[name])
        op.create_index(
            name,
            "embeddings",
            columns,
            unique=False,
            postgresql_where=_WHERE_CLAUSES[name],
        )