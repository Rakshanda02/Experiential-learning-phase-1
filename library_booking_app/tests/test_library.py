import os, sys, tempfile, unittest
import sqlite3
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hash_table import LibraryHashTable
from models import Book
from service import LibraryService
import storage


class HashTableTests(unittest.TestCase):
    def setUp(self):
        self.t = LibraryHashTable(10)

    def test_hash_examples(self):
        self.assertEqual(self.t.hash_function("101"), 2)
        self.assertEqual(self.t.hash_function("111"), 3)
        self.assertEqual(self.t.hash_function("110"), 2)

    def test_insert_search_duplicate(self):
        self.assertTrue(self.t.insert(Book("101", "A", "X")))
        self.assertFalse(self.t.insert(Book("101", "B", "Y")))
        self.assertEqual(self.t.search("101").title, "A")
        self.assertIsNone(self.t.search("999"))

    def test_collision_chaining(self):
        self.t.insert(Book("101", "A", "X"))
        self.t.insert(Book("110", "B", "Y"))
        self.t.insert(Book("111", "C", "Z"))
        rows = self.t.display_table()
        self.assertEqual([b.isbn for b in rows[2]["books"]], ["101", "110"])
        self.assertTrue(rows[2]["collision"])
        st = self.t.get_statistics()
        self.assertEqual((st["records"], st["occupied_buckets"], st["collisions"], st["max_chain"]), (3, 2, 1, 2))
        self.assertAlmostEqual(st["load_factor"], 0.3)

    def test_update_delete(self):
        for i in ("101", "110"):
            self.t.insert(Book(i, "T" + i, "A"))
        self.assertTrue(self.t.update("110", {"title": "New"}))
        self.assertEqual(self.t.search("110").title, "New")
        self.assertTrue(self.t.delete("101"))   # head of chain
        self.assertEqual(self.t.search("110").title, "New")
        self.assertFalse(self.t.delete("101"))
        self.assertEqual(self.t.count, 1)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db"); os.close(fd)
        self.s = LibraryService(self.path)

    def tearDown(self):
        os.remove(self.path)

    def test_add_validation(self):
        self.assertTrue(self.s.add_book("101", "T", "A", copies=2)[0])
        self.assertFalse(self.s.add_book("101", "T", "A")[0])
        self.assertFalse(self.s.add_book("", "T", "A")[0])
        self.assertFalse(self.s.add_book("5", "", "A")[0])
        self.assertFalse(self.s.add_book("5", "T", "A", copies=0)[0])
        self.assertFalse(self.s.add_book("5", "T", "A", year="3000")[0])

    def test_issue_return_flow(self):
        self.s.add_book("101", "T", "A", copies=1)
        self.assertTrue(self.s.issue_book("101", "S1")[0])
        self.assertFalse(self.s.issue_book("101", "S2")[0])       # none available
        self.assertFalse(self.s.delete_book("101")[0])            # issued
        txn = self.s.active_transactions("101")[0]
        self.assertTrue(self.s.return_book(txn.id)[0])
        self.assertFalse(self.s.return_book(txn.id)[0])           # double return
        self.assertTrue(self.s.delete_book("101")[0])

    def test_update_not_below_issued(self):
        self.s.add_book("101", "T", "A", copies=3)
        self.s.issue_book("101", "S1"); self.s.issue_book("101", "S2")
        self.assertFalse(self.s.update_book("101", "T", "A", "G", "", "", 1)[0])
        self.assertTrue(self.s.update_book("101", "T2", "A", "G", "", "2020", 2)[0])

    def test_persistence_and_collision_demo(self):
        self.s.add_book("101", "A", "X"); self.s.add_book("110", "B", "Y")
        s2 = LibraryService(self.path)                            # simulated restart
        self.assertEqual(s2.table.hash_function("101"), s2.table.hash_function("110"))
        self.assertEqual(s2.dashboard_stats()["collisions"], 1)
        self.assertEqual(LibraryService(tempfile.mktemp()).dashboard_stats()["records"], 0)

    def test_authentication_and_borrowing_limit(self):
        self.assertTrue(self.s.create_first_librarian("librarian", "secure-pass", "Library Admin")[0])
        self.assertIsNone(self.s.authenticate("librarian", "wrong-pass"))
        self.assertEqual(self.s.authenticate("librarian", "secure-pass").role, "librarian")
        self.assertTrue(self.s.register_student("reader", "student-pass", "Riley Reader")[0])
        student = self.s.authenticate("reader", "student-pass")
        self.assertTrue(self.s.update_borrow_limit(student.id, 1)[0])
        self.s.add_book("111", "One", "Author", copies=2)
        self.assertTrue(self.s.issue_book("111", "", user_id=student.id)[0])
        self.assertFalse(self.s.issue_book("111", "", user_id=student.id)[0])

    def test_late_return_calculates_fine_and_analytics(self):
        self.s.add_book("121", "Late Book", "Author", copies=1)
        book = self.s.table.search("121")
        book.issued_copies = 1
        due = date.today() - timedelta(days=3)
        txn_id = storage.save_issue(self.path, book, "Reader", due.isoformat(), due.isoformat())
        self.assertTrue(self.s.return_book(txn_id)[0])
        txn = storage.get_transaction(self.path, txn_id)
        self.assertEqual(txn.fine_amount, 3.0)
        self.assertEqual(self.s.popular_books()[0]["Borrowings"], 1)

    def test_waitlist_promotes_in_order_and_reservation_is_required(self):
        self.s.add_book("131", "Held Book", "Author", copies=1)
        self.assertTrue(self.s.issue_book("131", "Walk-in")[0])
        self.s.register_student("first", "first-pass", "First Reader")
        self.s.register_student("second", "second-pass", "Second Reader")
        first = self.s.authenticate("first", "first-pass")
        second = self.s.authenticate("second", "second-pass")
        self.s.reserve_book("131", first.id)
        self.s.reserve_book("131", second.id)
        self.assertTrue(self.s.return_book(self.s.active_transactions("131")[0].id)[0])
        holds = {hold.user_id: hold for hold in self.s.reservations() if hold.isbn == "131"}
        self.assertEqual(holds[first.id].status, "Ready")
        self.assertEqual(holds[second.id].status, "Waiting")
        self.assertFalse(self.s.issue_book("131", "", user_id=second.id)[0])
        self.assertTrue(self.s.issue_book("131", "", user_id=first.id,
                                          reservation_id=holds[first.id].id)[0])

    def test_legacy_database_migrates_without_losing_transactions(self):
        fd, legacy_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = sqlite3.connect(legacy_path)
            try:
                conn.execute("CREATE TABLE books(isbn TEXT PRIMARY KEY,title TEXT NOT NULL,author TEXT NOT NULL,"
                             "category TEXT,publisher TEXT,year INTEGER,total_copies INTEGER NOT NULL,"
                             "issued_copies INTEGER NOT NULL DEFAULT 0,added_at TEXT NOT NULL)")
                conn.execute("CREATE TABLE transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,isbn TEXT NOT NULL,"
                             "title TEXT NOT NULL,student TEXT NOT NULL,issue_date TEXT NOT NULL,"
                             "due_date TEXT NOT NULL,return_date TEXT)")
                conn.execute("INSERT INTO transactions(isbn,title,student,issue_date,due_date) "
                             "VALUES('141','Legacy','Reader','2025-01-01','2025-01-15')")
                conn.commit()
            finally:
                conn.close()
            migrated = LibraryService(legacy_path)
            transaction = storage.get_transaction(legacy_path, 1)
            self.assertEqual(transaction.title, "Legacy")
            self.assertEqual(transaction.fine_amount, 0.0)
            self.assertFalse(migrated.has_librarian())
        finally:
            os.remove(legacy_path)


if __name__ == "__main__":
    unittest.main()
