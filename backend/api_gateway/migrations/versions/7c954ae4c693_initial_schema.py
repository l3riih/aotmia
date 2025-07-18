"""initial schema

Revision ID: 7c954ae4c693
Revises: 
Create Date: 2025-06-23 13:23:21.140798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7c954ae4c693'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('learning_atoms',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('difficulty_level', sa.Enum('EASY', 'MEDIUM', 'HARD', name='difficulty_level'), nullable=False),
    sa.Column('prerequisites', postgresql.ARRAY(sa.UUID()), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('learning_atoms')
    # ### end Alembic commands ###
