from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"


def upgrade():
    op.create_table(
        "book_copies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("inventory_number", sa.String(50), nullable=False),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("books.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_available", sa.Boolean, nullable=False),
        sa.UniqueConstraint("inventory_number", name="uq_copy_inventory_number"),
    )
    op.create_index("ix_book_copies_inventory_number", "book_copies", ["inventory_number"])


def downgrade():
    op.drop_table("book_copies")
