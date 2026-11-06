from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"


def upgrade():
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "copy_id", sa.Integer, sa.ForeignKey("book_copies.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("reader_name", sa.String(200), nullable=False),
        sa.Column("loaned_at", sa.DateTime, nullable=False),
        sa.Column("returned_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_loans_reader_name", "loans", ["reader_name"])


def downgrade():
    op.drop_table("loans")
