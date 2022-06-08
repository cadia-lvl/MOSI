"""empty message

Revision ID: da2902e237da
Revises: 2f145aed69cf
Create Date: 2022-03-09 14:53:46.681200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da2902e237da'
down_revision = '2f145aed69cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_abtest_admin',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('abtest_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['abtest_id'], ['ABtest.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_abtest_admin')
    # ### end Alembic commands ###