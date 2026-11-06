from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"


def upgrade():
    op.add_column("books", sa.Column("publication_year", sa.Integer, nullable=True))


def downgrade():
    op.drop_column("books", "publication_year")
