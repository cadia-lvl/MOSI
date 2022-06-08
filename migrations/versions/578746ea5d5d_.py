"""empty message

Revision ID: 578746ea5d5d
Revises: da2902e237da
Create Date: 2022-03-14 13:40:46.102755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '578746ea5d5d'
down_revision = 'da2902e237da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_mos_test_admin',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('mos_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['mos_id'], ['Mos.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_sus_test_admin',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('sus_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['sus_id'], ['Sus.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_sus_test_admin')
    op.drop_table('user_mos_test_admin')
    # ### end Alembic commands ###