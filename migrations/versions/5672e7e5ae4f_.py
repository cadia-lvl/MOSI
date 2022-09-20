"""empty message

Revision ID: 5672e7e5ae4f
Revises: e161b722a4e6
Create Date: 2022-09-20 14:11:31.227323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5672e7e5ae4f'
down_revision = 'e161b722a4e6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('MosInstance', sa.Column('additional_id', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('MosInstance', 'additional_id')
    # ### end Alembic commands ###
