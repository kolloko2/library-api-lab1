from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class AuthorRead(AuthorCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    isbn: str = Field(pattern=r"^(?:\d{10}|\d{13})$")
    author_id: int = Field(gt=0)


class BookRead(BookCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    address: str = Field(min_length=5, max_length=300)


class BranchRead(BranchCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CopyCreate(BaseModel):
    inventory_number: str = Field(min_length=2, max_length=50)
    book_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)


class CopyRead(CopyCreate):
    id: int
    is_available: bool
    model_config = ConfigDict(from_attributes=True)


class LoanCreate(BaseModel):
    copy_id: int = Field(gt=0)
    reader_name: str = Field(min_length=2, max_length=200)


class LoanRead(LoanCreate):
    id: int
    loaned_at: datetime
    returned_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
