"""Add unique constraint on lexical_forms(lexical_item_id, form_type, form)"""

from typing import Sequence, Union

from alembic import op

revision: str = "905aa7befc78"
down_revision: Union[str, None] = "756993beee95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_lexical_forms_item_type_form",
        "lexical_forms",
        ["lexical_item_id", "form_type", "form"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_lexical_forms_item_type_form",
        "lexical_forms",
        type_="unique",
    )