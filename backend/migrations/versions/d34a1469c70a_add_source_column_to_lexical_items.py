"""add source column to lexical_items"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd34a1469c70a'
down_revision: Union[str, None] = '905aa7befc78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'lexical_items',
        sa.Column('source', sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('lexical_items', 'source')