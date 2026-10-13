"""Business logic: validates input, keeps SQLite and the hash table in sync."""
import hashlib
import hmac
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

import storage
from hash_table import LibraryHashTable
from models import Book, LibraryUser, Reservation, Transaction

Result = Tuple[bool, str]
PASSWORD_ITERATIONS = 240_000
FINE_PER_DAY = 1.0

SAMPLE_BOOKS = [
    ("101", "Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", "MIT Press", 2009, 3),
    ("110", "Data Structures Using C", "Reema Thareja", "Computer Science", "Oxford", 2014, 2),
    ("111", "Python Crash Course", "Eric Matthes", "Programming", "No Starch Press", 2019, 4),
    ("120", "Clean Code", "Robert C. Martin", "Programming", "Prentice Hall", 2008, 2),
    ("205", "The Discovery of India", "Jawaharlal Nehru", "History", "Penguin", 2004, 2),
    ("330", "Wings of Fire", "A. P. J. Abdul Kalam", "Biography", "Universities Press", 1999, 5),
    ("417", "Concrete Mathematics", "Ronald Graham", "Mathematics", "Addison-Wesley", 1994, 1),
    ("502", "Database System Concepts", "Abraham Silberschatz", "Computer Science", "McGraw-Hill", 2019, 3),
]


class LibraryService:
    def __init__(self, db_path: str = "library.db", size: int = 10):
        self.db_path = db_path
        self.table = LibraryHashTable(size)
        storage.init_db(db_path)
        self.sync()

    def sync(self) -> None:
        """Rebuild the in-memory hash table from SQLite."""
        self.table = LibraryHashTable(self.table.size)
        for b in storage.load_books(self.db_path):
            self.table.insert(b)

    # ---------- accounts and profiles ----------
    @staticmethod
    def _password_digest(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS).hex()

    def has_librarian(self) -> bool:
        return storage.has_librarian(self.db_path)

    def _create_account(self, username, password, full_name, role, email="", borrow_limit=5) -> Result:
        username = (username or "").strip()
        full_name = (full_name or "").strip()
        email = (email or "").strip()
        if len(username) < 3:
            return False, "Username must contain at least 3 characters."
        if len(password or "") < 8:
            return False, "Password must contain at least 8 characters."
        if not full_name:
            return False, "Full name is required."
        if role not in ("student", "librarian"):
            return False, "Choose a valid account role."
        if not 1 <= int(borrow_limit) <= 20:
            return False, "Borrowing limit must be between 1 and 20."
        salt = secrets.token_hex(16)
        try:
            storage.create_user(self.db_path, username, self._password_digest(password, salt),
                                salt, full_name, role, email, int(borrow_limit))
        except sqlite3.IntegrityError:
            return False, "That username is already in use."
        return True, f"Created {role} account for {full_name}."

    def create_first_librarian(self, username, password, full_name, email="") -> Result:
        if self.has_librarian():
            return False, "A librarian account is already set up."
        return self._create_account(username, password, full_name, "librarian", email, 20)

    def register_student(self, username, password, full_name, email="") -> Result:
        return self._create_account(username, password, full_name, "student")

    def create_user(self, username, password, full_name, role="student", email="", borrow_limit=5) -> Result:
        return self._create_account(username, password, full_name, role, email, borrow_limit)

    def authenticate(self, username: str, password: str) -> Optional[LibraryUser]:
        row = storage.get_user_by_username(self.db_path, (username or "").strip())
        if not row:
            return None
        user_id, login, password_hash, salt, full_name, role, email, borrow_limit = row
        if not hmac.compare_digest(password_hash, self._password_digest(password or "", salt)):
            return None
        return LibraryUser(user_id, login, full_name, role, email, borrow_limit)

    def users(self) -> List[LibraryUser]:
        return storage.list_users(self.db_path)

    def update_profile(self, user_id: int, full_name: str, email: str) -> Result:
        full_name, email = (full_name or "").strip(), (email or "").strip()
        if not full_name:
            return False, "Full name is required."
        storage.update_profile(self.db_path, user_id, full_name, email)
        return True, "Profile updated."

    def update_borrow_limit(self, user_id: int, borrow_limit: int) -> Result:
        try:
            limit = int(borrow_limit)
        except (TypeError, ValueError):
            return False, "Borrowing limit must be a whole number."
        user = storage.get_user(self.db_path, user_id)
        if not user or user.role != "student":
            return False, "Student account not found."
        if not 1 <= limit <= 20:
            return False, "Borrowing limit must be between 1 and 20."
        storage.update_borrow_limit(self.db_path, user_id, limit)
        return True, "Borrowing limit updated."

    # ---------- validation helpers ----------
    @staticmethod
    def _parse_year(year) -> Tuple[Optional[int], Optional[str]]:
        if year is None or str(year).strip() == "":
            return None, None
        try:
            y = int(str(year).strip())
        except ValueError:
            return None, "Publication year must be a number."
        if not 1000 <= y <= date.today().year:
            return None, f"Publication year must be between 1000 and {date.today().year}."
        return y, None

    @staticmethod
    def _parse_copies(copies) -> Tuple[Optional[int], Optional[str]]:
        try:
            n = int(copies)
        except (TypeError, ValueError):
            return None, "Number of copies must be a whole number."
        if n <= 0:
            return None, "Number of copies must be a positive integer."
        return n, None

    # ---------- book operations ----------
    def add_book(self, isbn, title, author, category="General", publisher="", year=None, copies=1) -> Result:
        isbn, title, author = (isbn or "").strip(), (title or "").strip(), (author or "").strip()
        if not isbn:
            return False, "ISBN is required."
        if not title or not author:
            return False, "Title and author are required."
        y, err = self._parse_year(year)
        if err:
            return False, err
        n, err = self._parse_copies(copies)
        if err:
            return False, err
        if self.table.search(isbn):
            return False, f"A book with ISBN {isbn} already exists."
        book = Book(isbn, title, author, (category or "General").strip() or "General",
                    (publisher or "").strip(), y, n)
        storage.insert_book(self.db_path, book)
        self.table.insert(book)
        return True, f"Added '{title}' to bucket {self.table.hash_function(isbn)}."

    def update_book(self, isbn, title, author, category, publisher, year, total_copies) -> Result:
        book = self.table.search(isbn)
        if not book:
            return False, "Book not found."
        title, author = (title or "").strip(), (author or "").strip()
        if not title or not author:
            return False, "Title and author are required."
        y, err = self._parse_year(year)
        if err:
            return False, err
        n, err = self._parse_copies(total_copies)
        if err:
            return False, err
        if n < book.issued_copies:
            return False, f"Total copies cannot be less than the {book.issued_copies} currently issued."
        self.table.update(isbn, {"title": title, "author": author,
                                 "category": (category or "General").strip() or "General",
                                 "publisher": (publisher or "").strip(), "year": y, "total_copies": n})
        storage.update_book(self.db_path, book)
        return True, "Book updated."

    def delete_book(self, isbn) -> Result:
        book = self.table.search(isbn)
        if not book:
            return False, "Book not found."
        if book.issued_copies > 0:
            return False, f"Cannot delete: {book.issued_copies} copy/copies are currently issued."
        storage.delete_book(self.db_path, book.isbn)
        self.table.delete(isbn)
        return True, f"Deleted '{book.title}'."

    def all_books(self) -> List[Book]:
        return list(self.table.all_books())

    def search(self, field: str, query: str) -> List[Book]:
        query = (query or "").strip()
        if not query:
            return self.all_books()
        if field == "ISBN":
            book = self.table.search(query)  # custom hash table lookup
            return [book] if book else []
        attr = {"Title": "title", "Author": "author", "Category": "category"}[field]
        q = query.lower()
        return [b for b in self.all_books() if q in getattr(b, attr).lower()]

    # ---------- issue / return ----------
    def issue_book(self, isbn, student, days: int = 14, user_id: Optional[int] = None,
                   reservation_id: Optional[int] = None) -> Result:
        book = self.table.search(isbn)
        if not book:
            return False, "Book not found."
        user = storage.get_user(self.db_path, user_id) if user_id is not None else None
        if user_id is not None and not user:
            return False, "Student account not found."
        if user:
            if user.role != "student":
                return False, "Only student accounts can borrow books."
            active_loans = sum(1 for txn in self.active_transactions() if txn.user_id == user.id)
            if active_loans >= user.borrow_limit:
                return False, f"Borrowing limit reached ({user.borrow_limit} active books)."
            student = user.full_name
        student = (student or "").strip()
        if not student:
            return False, "Student name or ID is required."
        reservation = storage.get_reservation(self.db_path, reservation_id) if reservation_id else None
        if reservation_id and (not reservation or reservation.status != "Ready"):
            return False, "This reservation is not ready to be issued."
        if reservation and (reservation.isbn != isbn or (user_id is not None and reservation.user_id != user_id)):
            return False, "This reservation belongs to another student or book."
        if reservation:
            reserved_user = storage.get_user(self.db_path, reservation.user_id)
            if not reserved_user:
                return False, "Student account not found."
            student, user_id = reserved_user.full_name, reserved_user.id
            active_loans = sum(1 for txn in self.active_transactions() if txn.user_id == user_id)
            if active_loans >= reserved_user.borrow_limit:
                return False, f"{student} has reached their borrowing limit."
        if book.available_copies < 1:
            return False, "No copies available to issue."
        ready_holds = storage.count_reservations(self.db_path, isbn, "Ready")
        if not reservation and book.available_copies <= ready_holds:
            return False, "Available copies are held for students in the reservation queue."
        book.issued_copies += 1
        today = date.today()
        txn_id = storage.save_issue(self.db_path, book, student, today.isoformat(),
                                    (today + timedelta(days=int(days))).isoformat(), user_id)
        if reservation:
            storage.set_reservation_status(self.db_path, reservation.id, "Fulfilled")
            self._promote_waitlist(isbn)
        return True, f"Issued '{book.title}' to {student} (transaction #{txn_id}). Due {today + timedelta(days=int(days))}."

    def return_book(self, txn_id: int, user_id: Optional[int] = None) -> Result:
        txn = storage.get_transaction(self.db_path, txn_id)
        if not txn:
            return False, "Transaction not found."
        if user_id is not None and txn.user_id != user_id:
            return False, "You can only return books issued to your account."
        if txn.return_date:
            return False, "This book has already been returned."
        book = self.table.search(txn.isbn)
        if not book or book.issued_copies < 1:
            return False, "No issued copy of this book to return."
        book.issued_copies -= 1
        returned = date.today()
        overdue_days = max((returned - date.fromisoformat(txn.due_date)).days, 0)
        fine_amount = round(overdue_days * FINE_PER_DAY, 2)
        storage.save_return(self.db_path, book, txn_id, returned.isoformat(), fine_amount)
        self._promote_waitlist(txn.isbn)
        suffix = f" Fine due: {fine_amount:.2f}." if fine_amount else " No fine due."
        return True, f"'{txn.title}' returned by {txn.student}.{suffix}"

    def fine_amount(self, txn: Transaction, as_of: Optional[date] = None) -> float:
        if txn.return_date:
            return txn.fine_amount
        current = as_of or date.today()
        overdue_days = max((current - date.fromisoformat(txn.due_date)).days, 0)
        return round(overdue_days * FINE_PER_DAY, 2)

    def pay_fine(self, txn_id: int) -> Result:
        txn = storage.get_transaction(self.db_path, txn_id)
        if not txn or not txn.return_date:
            return False, "Only returned loans can have a fine recorded as paid."
        if txn.fine_amount <= 0:
            return False, "There is no fine due for this loan."
        if txn.fine_paid:
            return False, "This fine has already been recorded as paid."
        storage.mark_fine_paid(self.db_path, txn_id)
        return True, f"Fine of {txn.fine_amount:.2f} recorded as paid."

    # ---------- reservations ----------
    def reservations(self, user_id: Optional[int] = None) -> List[Reservation]:
        return storage.list_reservations(self.db_path, user_id)

    def reserve_book(self, isbn: str, user_id: int) -> Result:
        book = self.table.search(isbn)
        user = storage.get_user(self.db_path, user_id)
        if not book:
            return False, "Book not found."
        if not user or user.role != "student":
            return False, "Student account not found."
        active_loan = any(txn.user_id == user_id and txn.isbn == isbn for txn in self.active_transactions())
        if active_loan:
            return False, "You already have this book on loan."
        current = [hold for hold in self.reservations(user_id)
                   if hold.isbn == isbn and hold.status in ("Waiting", "Ready")]
        if current:
            return False, "You already have an active reservation for this book."
        hold_id = storage.save_reservation(self.db_path, isbn, user_id, datetime.now().isoformat(timespec="seconds"))
        self._promote_waitlist(isbn)
        hold = storage.get_reservation(self.db_path, hold_id)
        if hold and hold.status == "Ready":
            return True, f"'{book.title}' is available and held for you."
        position = 1 + sum(1 for item in self.reservations()
                           if item.isbn == isbn and item.status == "Waiting"
                           and (item.created_at, item.id) < (hold.created_at, hold.id))
        return True, f"Added to the waiting list for '{book.title}' (position {position})."

    def cancel_reservation(self, reservation_id: int, user_id: Optional[int] = None) -> Result:
        hold = storage.get_reservation(self.db_path, reservation_id)
        if not hold or hold.status not in ("Waiting", "Ready"):
            return False, "Active reservation not found."
        if user_id is not None and hold.user_id != user_id:
            return False, "You can only cancel your own reservation."
        storage.set_reservation_status(self.db_path, reservation_id, "Cancelled")
        self._promote_waitlist(hold.isbn)
        return True, "Reservation cancelled."

    def _promote_waitlist(self, isbn: str) -> None:
        book = self.table.search(isbn)
        if not book:
            return
        open_slots = max(0, book.available_copies - storage.count_reservations(self.db_path, isbn, "Ready"))
        if open_slots == 0:
            return
        waiting = [hold for hold in self.reservations() if hold.isbn == isbn and hold.status == "Waiting"]
        for hold in waiting[:open_slots]:
            storage.set_reservation_status(self.db_path, hold.id, "Ready")

    def user_transactions(self, user_id: int) -> List[Transaction]:
        return [txn for txn in self.transactions() if txn.user_id == user_id]

    def popular_books(self, limit: int = 10) -> List[dict]:
        counts = {}
        for txn in self.transactions():
            entry = counts.setdefault(txn.isbn, {"ISBN": txn.isbn, "Title": txn.title, "Borrowings": 0})
            entry["Borrowings"] += 1
        return sorted(counts.values(), key=lambda item: (-item["Borrowings"], item["Title"].casefold()))[:limit]

    def transactions(self) -> List[Transaction]:
        return storage.list_transactions(self.db_path)

    def active_transactions(self, isbn: str = "") -> List[Transaction]:
        isbn = (isbn or "").strip()
        return [t for t in self.transactions() if not t.return_date and (not isbn or t.isbn == isbn)]

    # ---------- statistics ----------
    def dashboard_stats(self) -> dict:
        s = self.table.get_statistics()
        books = self.all_books()
        total = sum(b.total_copies for b in books)
        issued = sum(b.issued_copies for b in books)
        txns = self.transactions()
        today = date.today().isoformat()
        s.update(total_copies=total, issued=issued, available=total - issued,
                 active_txns=sum(1 for t in txns if not t.return_date),
                 returned_txns=sum(1 for t in txns if t.return_date),
                 overdue=sum(1 for t in txns if not t.return_date and t.due_date < today),
                 outstanding_fines=round(sum(self.fine_amount(t) for t in txns if not t.fine_paid), 2))
        return s

    def recent_books(self, n: int = 5) -> List[Book]:
        return sorted(self.all_books(), key=lambda b: b.added_at, reverse=True)[:n]

    def load_samples(self) -> int:
        added = 0
        for row in SAMPLE_BOOKS:
            ok, _ = self.add_book(*row)
            added += ok
        return added
