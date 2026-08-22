"""Remove redundant part_of_speech column from lexical_items

The full name (e.g. 'noun') is redundant with part_of_speech_code ('n').
Also add the missing index on lexical_items.id to match the model definition.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9a35bad4e480"
down_revision: Union[str, None] = "f4a02696b951"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_lexical_items_id"), "lexical_items", ["id"], unique=False)
    op.drop_column("lexical_items", "part_of_speech")


def downgrade() -> None:
    op.add_column(
        "lexical_items",
        sa.Column("part_of_speech", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_index(op.f("ix_lexical_items_id"), table_name="lexical_items")