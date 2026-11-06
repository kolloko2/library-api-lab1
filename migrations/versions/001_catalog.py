from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None


def upgrade():
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
    )
    op.create_index("ix_authors_name", "authors", ["name"])
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("address", sa.String(300), nullable=False),
    )
    op.create_table(
        "books",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("isbn", sa.String(20), nullable=False, unique=True),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("authors.id", ondelete="RESTRICT"), nullable=False),
    )
    op.create_index("ix_books_title", "books", ["title"])
    op.create_index("ix_books_isbn", "books", ["isbn"])


def downgrade():
    op.drop_table("books")
    op.drop_table("branches")
    op.drop_table("authors")
