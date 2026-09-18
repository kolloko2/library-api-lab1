from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Author, Book, BookCopy, Branch, Loan
from app.schemas import (
    AuthorCreate,
    AuthorRead,
    BookCreate,
    BookRead,
    BranchCreate,
    BranchRead,
    CopyCreate,
    CopyRead,
    LoanCreate,
    LoanRead,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)


def commit_or_conflict(db: Session, detail: str):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok", "environment": get_settings().app_env}


@app.post("/authors", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
def create_author(payload: AuthorCreate, db: Session = Depends(get_db)):
    author = Author(name=payload.name)
    db.add(author)
    commit_or_conflict(db, "Автор с таким именем уже существует")
    db.refresh(author)
    return author


@app.get("/authors", response_model=list[AuthorRead])
def list_authors(db: Session = Depends(get_db)):
    return db.scalars(select(Author).order_by(Author.name)).all()


@app.post("/books", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    if db.get(Author, payload.author_id) is None:
        raise HTTPException(status_code=404, detail="Автор не найден")
    book = Book(**payload.model_dump())
    db.add(book)
    commit_or_conflict(db, "Книга с таким ISBN уже существует")
    db.refresh(book)
    return book


@app.get("/books", response_model=list[BookRead])
def list_books(
    title: str | None = Query(default=None, min_length=1),
    author_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = select(Book).order_by(Book.title)
    if title:
        query = query.where(Book.title.ilike(f"%{title}%"))
    if author_id:
        query = query.where(Book.author_id == author_id)
    return db.scalars(query).all()


@app.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db)):
    branch = Branch(**payload.model_dump())
    db.add(branch)
    commit_or_conflict(db, "Филиал с таким именем уже существует")
    db.refresh(branch)
    return branch


@app.get("/branches", response_model=list[BranchRead])
def list_branches(db: Session = Depends(get_db)):
    return db.scalars(select(Branch).order_by(Branch.name)).all()


@app.post("/copies", response_model=CopyRead, status_code=status.HTTP_201_CREATED)
def create_copy(payload: CopyCreate, db: Session = Depends(get_db)):
    if db.get(Book, payload.book_id) is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if db.get(Branch, payload.branch_id) is None:
        raise HTTPException(status_code=404, detail="Филиал не найден")
    copy = BookCopy(**payload.model_dump())
    db.add(copy)
    commit_or_conflict(db, "Экземпляр с таким инвентарным номером уже существует")
    db.refresh(copy)
    return copy


@app.get("/copies", response_model=list[CopyRead])
def list_copies(
    branch_id: int | None = Query(default=None, gt=0),
    available: bool | None = None,
    db: Session = Depends(get_db),
):
    query = select(BookCopy).order_by(BookCopy.inventory_number)
    if branch_id:
        query = query.where(BookCopy.branch_id == branch_id)
    if available is not None:
        query = query.where(BookCopy.is_available == available)
    return db.scalars(query).all()


@app.post("/loans", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)):
    copy = db.get(BookCopy, payload.copy_id)
    if copy is None:
        raise HTTPException(status_code=404, detail="Экземпляр не найден")
    if not copy.is_available:
        raise HTTPException(status_code=409, detail="Экземпляр уже выдан")

    active_count = db.scalar(
        select(func.count(Loan.id)).where(
            Loan.reader_name == payload.reader_name,
            Loan.returned_at.is_(None),
        )
    )
    if active_count >= get_settings().max_active_loans:
        raise HTTPException(
            status_code=409,
            detail="Читатель достиг лимита активных выдач",
        )

    loan = Loan(copy_id=copy.id, reader_name=payload.reader_name)
    copy.is_available = False
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@app.get("/loans", response_model=list[LoanRead])
def list_loans(active_only: bool = False, db: Session = Depends(get_db)):
    query = select(Loan).order_by(Loan.loaned_at.desc())
    if active_only:
        query = query.where(Loan.returned_at.is_(None))
    return db.scalars(query).all()


@app.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Выдача не найдена")
    if loan.returned_at is not None:
        raise HTTPException(status_code=409, detail="Выдача уже возвращена")

    loan.returned_at = datetime.now(timezone.utc)
    loan.copy.is_available = True
    db.commit()
    db.refresh(loan)
    return loan
