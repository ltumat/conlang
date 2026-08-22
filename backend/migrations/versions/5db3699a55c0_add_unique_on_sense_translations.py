"""Add unique constraint on sense_translations(sense_id, position)"""

from typing import Sequence, Union

from alembic import op

revision: str = "5db3699a55c0"
down_revision: Union[str, None] = "9a35bad4e480"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_sense_translations_sense_position",
        "sense_translations",
        ["sense_id", "position"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_sense_translations_sense_position",
        "sense_translations",
        type_="unique",
    )