from alembic import op  # type: ignore
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'evaluations',
        sa.Column('evaluation_id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False, index=True),
        sa.Column('question_id', sa.String(), nullable=False, index=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('feedback', sa.JSON(), nullable=False),
        sa.Column('misconceptions_detected', sa.JSON(), default=[]),
        sa.Column('learning_progress', sa.JSON(), nullable=False),
        sa.Column('agent_metadata', sa.JSON(), nullable=False),
        sa.Column('key_concepts_understood', sa.JSON(), default=[]),
        sa.Column('next_recommended_topics', sa.JSON(), default=[]),
        sa.Column('estimated_time_to_mastery', sa.Integer(), default=60),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('evaluations') 