from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CopyStatus(str, Enum):
    available = "available"
    loaned = "loaned"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    books: Mapped[list[Book]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="RESTRICT"))
    author: Mapped[Author] = relationship(back_populates="books")
    copies: Mapped[list[BookCopy]] = relationship(back_populates="book")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    address: Mapped[str] = mapped_column(String(300))
    copies: Mapped[list[BookCopy]] = relationship(back_populates="branch")


class BookCopy(Base):
    __tablename__ = "book_copies"
    __table_args__ = (UniqueConstraint("inventory_number", name="uq_copy_inventory_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_number: Mapped[str] = mapped_column(String(50), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="RESTRICT"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    book: Mapped[Book] = relationship(back_populates="copies")
    branch: Mapped[Branch] = relationship(back_populates="copies")
    loans: Mapped[list[Loan]] = relationship(back_populates="copy")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id", ondelete="RESTRICT"))
    reader_name: Mapped[str] = mapped_column(String(200), index=True)
    loaned_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    returned_at: Mapped[datetime | None] = mapped_column(nullable=True)
    copy: Mapped[BookCopy] = relationship(back_populates="loans")
