"""Add unique constraint and index on sentence_word_occurrences

- UNIQUE(sentence_id, lexical_item_id, start_offset, end_offset) prevents
  duplicate occurrence records for the same token span.
- INDEX(lexical_item_id, sentence_id) enables fast word-to-sentence queries
  ("find all sentences containing this lexical item").
"""

from typing import Sequence, Union

from alembic import op

revision: str = "a1237a92cec6"
down_revision: Union[str, None] = "c4e021ccdbff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_sentence_word_occurrences_span",
        "sentence_word_occurrences",
        ["sentence_id", "lexical_item_id", "start_offset", "end_offset"],
    )
    op.create_index(
        "ix_sentence_word_occurrences_item",
        "sentence_word_occurrences",
        ["lexical_item_id", "sentence_id"],
        unique=False,
        postgresql_where=None,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sentence_word_occurrences_item",
        table_name="sentence_word_occurrences",
    )
    op.drop_constraint(
        "uq_sentence_word_occurrences_span",
        "sentence_word_occurrences",
        type_="unique",
    )