"""Add indexes for embedding import performance

These indexes dramatically speed up the import_embeddings script by avoiding
sequential scans on the sentences and embeddings tables.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f4a02696b951"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index for looking up sentences by text (import_embeddings does this 437k times)
    op.create_index(
        "ix_sentences_text",
        "sentences",
        ["text"],
        unique=False,
        if_not_exists=True,
    )

    # Partial indexes for embedding lookups by content type
    # Each index covers one of the four target types (word/sense/sentence/sentence_pair)
    op.create_index(
        "ix_embeddings_model_content_item",
        "embeddings",
        ["model_name", "content_type", "lexical_item_id"],
        unique=False,
        postgresql_where="lexical_item_id IS NOT NULL",
        if_not_exists=True,
    )
    op.create_index(
        "ix_embeddings_model_content_sense",
        "embeddings",
        ["model_name", "content_type", "sense_id"],
        unique=False,
        postgresql_where="sense_id IS NOT NULL",
        if_not_exists=True,
    )
    op.create_index(
        "ix_embeddings_model_content_sentence",
        "embeddings",
        ["model_name", "content_type", "sentence_id"],
        unique=False,
        postgresql_where="sentence_id IS NOT NULL",
        if_not_exists=True,
    )
    op.create_index(
        "ix_embeddings_model_content_translation",
        "embeddings",
        ["model_name", "content_type", "sentence_translation_id"],
        unique=False,
        postgresql_where="sentence_translation_id IS NOT NULL",
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_embeddings_model_content_translation", table_name="embeddings")
    op.drop_index("ix_embeddings_model_content_sentence", table_name="embeddings")
    op.drop_index("ix_embeddings_model_content_sense", table_name="embeddings")
    op.drop_index("ix_embeddings_model_content_item", table_name="embeddings")
    op.drop_index("ix_sentences_text", table_name="sentences")
