"""SQLite persistence. The hash table (not SQLite) is used for ISBN lookups."""
import sqlite3
from contextlib import contextmanager
from typing import List, Optional

from models import Book, LibraryUser, Reservation, Transaction


@contextmanager
def _conn(path):
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str) -> None:
    with _conn(path) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS books(
            isbn TEXT PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL,
            category TEXT, publisher TEXT, year INTEGER,
            total_copies INTEGER NOT NULL, issued_copies INTEGER NOT NULL DEFAULT 0,
            added_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT NOT NULL, title TEXT NOT NULL,
            student TEXT NOT NULL, issue_date TEXT NOT NULL, due_date TEXT NOT NULL,
            return_date TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL, salt TEXT NOT NULL, full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'librarian')),
            email TEXT NOT NULL DEFAULT '', borrow_limit INTEGER NOT NULL DEFAULT 5)""")
        c.execute("""CREATE TABLE IF NOT EXISTS reservations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT NOT NULL, user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Waiting',
            FOREIGN KEY(user_id) REFERENCES users(id))""")
        transaction_columns = {row[1] for row in c.execute("PRAGMA table_info(transactions)")}
        if "user_id" not in transaction_columns:
            c.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
        if "fine_amount" not in transaction_columns:
            c.execute("ALTER TABLE transactions ADD COLUMN fine_amount REAL NOT NULL DEFAULT 0")
        if "fine_paid" not in transaction_columns:
            c.execute("ALTER TABLE transactions ADD COLUMN fine_paid INTEGER NOT NULL DEFAULT 0")


def load_books(path: str) -> List[Book]:
    with _conn(path) as c:
        rows = c.execute("SELECT isbn,title,author,category,publisher,year,total_copies,"
                         "issued_copies,added_at FROM books ORDER BY added_at").fetchall()
    return [Book(*r) for r in rows]


def insert_book(path: str, b: Book) -> None:
    with _conn(path) as c:
        c.execute("INSERT INTO books VALUES(?,?,?,?,?,?,?,?,?)",
                  (b.isbn, b.title, b.author, b.category, b.publisher, b.year,
                   b.total_copies, b.issued_copies, b.added_at))


def update_book(path: str, b: Book) -> None:
    with _conn(path) as c:
        c.execute("UPDATE books SET title=?,author=?,category=?,publisher=?,year=?,"
                  "total_copies=?,issued_copies=? WHERE isbn=?",
                  (b.title, b.author, b.category, b.publisher, b.year,
                   b.total_copies, b.issued_copies, b.isbn))


def delete_book(path: str, isbn: str) -> None:
    with _conn(path) as c:
        c.execute("DELETE FROM books WHERE isbn=?", (isbn,))


def save_issue(path: str, b: Book, student: str, issue: str, due: str,
               user_id: Optional[int] = None) -> int:
    with _conn(path) as c:
        c.execute("UPDATE books SET issued_copies=? WHERE isbn=?", (b.issued_copies, b.isbn))
        cur = c.execute("INSERT INTO transactions(isbn,title,student,issue_date,due_date,user_id) "
                "VALUES(?,?,?,?,?,?)", (b.isbn, b.title, student, issue, due, user_id))
        return cur.lastrowid


def save_return(path: str, b: Book, txn_id: int, return_date: str, fine_amount: float = 0.0) -> None:
    with _conn(path) as c:
        c.execute("UPDATE books SET issued_copies=? WHERE isbn=?", (b.issued_copies, b.isbn))
        c.execute("UPDATE transactions SET return_date=?,fine_amount=? WHERE id=?",
              (return_date, fine_amount, txn_id))


def _txn(r) -> Transaction:
    return Transaction(*r)


def _user(row) -> Optional[LibraryUser]:
    return LibraryUser(*row) if row else None


def get_transaction(path: str, txn_id: int) -> Optional[Transaction]:
    with _conn(path) as c:
        r = c.execute("SELECT id,isbn,title,student,issue_date,due_date,return_date,"
                  "user_id,fine_amount,fine_paid "
                      "FROM transactions WHERE id=?", (txn_id,)).fetchone()
    return _txn(r) if r else None


def list_transactions(path: str) -> List[Transaction]:
    with _conn(path) as c:
        rows = c.execute("SELECT id,isbn,title,student,issue_date,due_date,return_date,"
                         "user_id,fine_amount,fine_paid "
                         "FROM transactions ORDER BY id DESC").fetchall()
    return [_txn(r) for r in rows]


def create_user(path: str, username: str, password_hash: str, salt: str,
                full_name: str, role: str, email: str = "", borrow_limit: int = 5) -> int:
    with _conn(path) as c:
        cur = c.execute("INSERT INTO users(username,password_hash,salt,full_name,role,email,borrow_limit) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (username, password_hash, salt, full_name, role, email, borrow_limit))
        return cur.lastrowid


def get_user(path: str, user_id: int) -> Optional[LibraryUser]:
    with _conn(path) as c:
        row = c.execute("SELECT id,username,full_name,role,email,borrow_limit FROM users WHERE id=?",
                        (user_id,)).fetchone()
    return _user(row)


def get_user_by_username(path: str, username: str):
    with _conn(path) as c:
        row = c.execute("SELECT id,username,password_hash,salt,full_name,role,email,borrow_limit "
                         "FROM users WHERE username=?", (username,)).fetchone()
    return row


def has_librarian(path: str) -> bool:
    with _conn(path) as c:
        return c.execute("SELECT 1 FROM users WHERE role='librarian' LIMIT 1").fetchone() is not None


def list_users(path: str) -> List[LibraryUser]:
    with _conn(path) as c:
        rows = c.execute("SELECT id,username,full_name,role,email,borrow_limit FROM users "
                         "ORDER BY full_name COLLATE NOCASE").fetchall()
    return [LibraryUser(*row) for row in rows]


def update_profile(path: str, user_id: int, full_name: str, email: str) -> None:
    with _conn(path) as c:
        c.execute("UPDATE users SET full_name=?,email=? WHERE id=?", (full_name, email, user_id))


def update_borrow_limit(path: str, user_id: int, borrow_limit: int) -> None:
    with _conn(path) as c:
        c.execute("UPDATE users SET borrow_limit=? WHERE id=?", (borrow_limit, user_id))


def save_reservation(path: str, isbn: str, user_id: int, created_at: str) -> int:
    with _conn(path) as c:
        cur = c.execute("INSERT INTO reservations(isbn,user_id,created_at) VALUES(?,?,?)",
                        (isbn, user_id, created_at))
        return cur.lastrowid


def list_reservations(path: str, user_id: Optional[int] = None) -> List[Reservation]:
    query = ("SELECT r.id,r.isbn,b.title,r.user_id,u.username,r.created_at,r.status "
             "FROM reservations r JOIN users u ON u.id=r.user_id "
             "JOIN books b ON b.isbn=r.isbn")
    params = ()
    if user_id is not None:
        query += " WHERE r.user_id=?"
        params = (user_id,)
    query += " ORDER BY CASE r.status WHEN 'Ready' THEN 0 WHEN 'Waiting' THEN 1 ELSE 2 END, r.created_at, r.id"
    with _conn(path) as c:
        rows = c.execute(query, params).fetchall()
    return [Reservation(*row) for row in rows]


def get_reservation(path: str, reservation_id: int) -> Optional[Reservation]:
    with _conn(path) as c:
        row = c.execute("SELECT r.id,r.isbn,b.title,r.user_id,u.username,r.created_at,r.status "
                         "FROM reservations r JOIN users u ON u.id=r.user_id "
                         "JOIN books b ON b.isbn=r.isbn WHERE r.id=?", (reservation_id,)).fetchone()
    return Reservation(*row) if row else None


def count_reservations(path: str, isbn: str, status: str) -> int:
    with _conn(path) as c:
        row = c.execute("SELECT COUNT(*) FROM reservations WHERE isbn=? AND status=?", (isbn, status)).fetchone()
    return row[0]


def set_reservation_status(path: str, reservation_id: int, status: str) -> None:
    with _conn(path) as c:
        c.execute("UPDATE reservations SET status=? WHERE id=?", (status, reservation_id))


def mark_fine_paid(path: str, txn_id: int) -> None:
    with _conn(path) as c:
        c.execute("UPDATE transactions SET fine_paid=1 WHERE id=?", (txn_id,))
