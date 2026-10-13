"""Data models for books and borrowing transactions."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    category: str = "General"
    publisher: str = ""
    year: Optional[int] = None
    total_copies: int = 1
    issued_copies: int = 0
    added_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="microseconds"))

    @property
    def available_copies(self) -> int:
        return self.total_copies - self.issued_copies


@dataclass
class Transaction:
    id: int
    isbn: str
    title: str
    student: str
    issue_date: str
    due_date: str
    return_date: Optional[str] = None
    user_id: Optional[int] = None
    fine_amount: float = 0.0
    fine_paid: bool = False

    @property
    def status(self) -> str:
        return "Returned" if self.return_date else "Active"


@dataclass
class LibraryUser:
    id: int
    username: str
    full_name: str
    role: str
    email: str = ""
    borrow_limit: int = 5


@dataclass
class Reservation:
    id: int
    isbn: str
    title: str
    user_id: int
    username: str
    created_at: str
    status: str
