"""empty message

Revision ID: 5d220ea146e6
Revises: 79e1c3bb83e6
Create Date: 2021-12-14 17:27:02.286871

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5d220ea146e6'
down_revision = '79e1c3bb83e6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Configuration')
    op.add_column('ABInstance', sa.Column('model_idx', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ABInstance', 'model_idx')
    op.create_table('Configuration',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Configuration_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('is_default', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('session_sz', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('live_transcribe', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('visualize_mic', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('auto_trim', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('analyze_sound', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('auto_gain_control', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('noise_suppression', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('channel_count', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sample_rate', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sample_size', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blob_slice', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('audio_codec', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('video_w', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('video_h', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('video_codec', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('has_video', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('trim_threshold', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('too_low_threshold', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('too_high_threshold', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('too_high_frames', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Configuration_pkey')
    )
    # ### end Alembic commands ###
