"""Add unique constraint on sentence_translations(sentence_id, translation)"""

from typing import Sequence, Union

from alembic import op

revision: str = "c4e021ccdbff"
down_revision: Union[str, None] = "5db3699a55c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_sentence_translations_sentence_translation",
        "sentence_translations",
        ["sentence_id", "translation"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_sentence_translations_sentence_translation",
        "sentence_translations",
        type_="unique",
    )