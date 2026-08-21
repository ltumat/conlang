"""create normalized vocabulary and embedding schema"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

# The selected embedding dimension is public schema configuration.
EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "user_languages",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column(
            "language_id", sa.Integer(), sa.ForeignKey("languages.id"), primary_key=True
        ),
    )
    op.create_table(
        "lexical_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("pronunciation", sa.String()),
        sa.Column("part_of_speech_code", sa.String(10)),
        sa.Column("part_of_speech", sa.String()),
        sa.Column("gender", sa.String(10)),
        sa.Column("source_entry_id", sa.Integer()),
        sa.Column(
            "language_id", sa.Integer(), sa.ForeignKey("languages.id"), nullable=False
        ),
        sa.UniqueConstraint("language_id", "word", "part_of_speech_code", "gender"),
    )
    op.create_table(
        "lexical_senses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lexical_item_id",
            sa.Integer(),
            sa.ForeignKey("lexical_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sense_number", sa.Integer(), nullable=False),
    )
    op.create_table(
        "sense_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "sense_id",
            sa.Integer(),
            sa.ForeignKey("lexical_senses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("translation", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_table(
        "lexical_forms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lexical_item_id",
            sa.Integer(),
            sa.ForeignKey("lexical_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("form", sa.String(), nullable=False),
        sa.Column("form_type", sa.String(30), nullable=False),
        sa.Column(
            "features", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
        ),
    )
    op.create_table(
        "sentences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("source_sentence_id", sa.String()),
        sa.Column(
            "language_id", sa.Integer(), sa.ForeignKey("languages.id"), nullable=False
        ),
        sa.UniqueConstraint("language_id", "text"),
    )
    op.create_table(
        "sentence_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "sentence_id",
            sa.Integer(),
            sa.ForeignKey("sentences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("translation", sa.String(), nullable=False),
        sa.Column("source_translation_id", sa.String()),
    )
    op.create_table(
        "sentence_word_occurrences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "sentence_id",
            sa.Integer(),
            sa.ForeignKey("sentences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lexical_item_id",
            sa.Integer(),
            sa.ForeignKey("lexical_items.id"),
            nullable=False,
        ),
        sa.Column("surface_form", sa.String(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("match_method", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float()),
    )
    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("lexical_item_id", sa.Integer(), sa.ForeignKey("lexical_items.id")),
        sa.Column("sense_id", sa.Integer(), sa.ForeignKey("lexical_senses.id")),
        sa.Column("sentence_id", sa.Integer(), sa.ForeignKey("sentences.id")),
        sa.Column(
            "sentence_translation_id",
            sa.Integer(),
            sa.ForeignKey("sentence_translations.id"),
        ),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "content_type IN ('word', 'sense', 'sentence', 'sentence_pair')",
            name="ck_embedding_content_type",
        ),
    )


def downgrade() -> None:
    for table in (
        "embeddings",
        "sentence_word_occurrences",
        "sentence_translations",
        "sentences",
        "lexical_forms",
        "sense_translations",
        "lexical_senses",
        "lexical_items",
        "user_languages",
        "users",
        "languages",
    ):
        op.drop_table(table)
