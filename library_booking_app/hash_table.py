"""Custom hash table with separate chaining (linked-list buckets).

Hash function: sum of the digits of the ISBN, modulo the table size.
    101 -> 1+0+1 = 2 -> bucket 2
    111 -> 1+1+1 = 3 -> bucket 3
    110 -> 1+1+0 = 2 -> bucket 2  (collision with 101, chained in bucket 2)
Non-digit characters (e.g. '-' or 'X') are ignored. If an ISBN has no digits at
all, the sum of its character codes is used instead.
"""
from typing import Iterator, List, Optional, Tuple

from models import Book


class Node:
    """One link in a bucket's chain."""

    def __init__(self, book: Book):
        self.book = book
        self.next: Optional["Node"] = None


class LibraryHashTable:
    def __init__(self, size: int = 10):
        self.size = size
        self.buckets: List[Optional[Node]] = [None] * size
        self.count = 0

    # ---- hash function (the ONLY place bucket indices are computed) ----
    def hash_function(self, isbn: str) -> int:
        s = str(isbn).strip()
        digits = [int(c) for c in s if c.isdigit()]
        total = sum(digits) if digits else sum(ord(c) for c in s)
        return total % self.size

    # ---- core operations ----
    def insert(self, book: Book) -> bool:
        """Add a book at the END of its chain. False if the ISBN already exists."""
        book.isbn = book.isbn.strip()
        idx = self.hash_function(book.isbn)
        node, tail = self.buckets[idx], None
        while node:
            if node.book.isbn == book.isbn:
                return False
            tail, node = node, node.next
        new = Node(book)
        if tail is None:
            self.buckets[idx] = new
        else:
            tail.next = new
        self.count += 1
        return True

    def search_with_trace(self, isbn: str) -> Tuple[Optional[Book], int, int]:
        """Return (book or None, bucket index, number of chain nodes compared)."""
        isbn = str(isbn).strip()
        idx = self.hash_function(isbn)
        node, steps = self.buckets[idx], 0
        while node:
            steps += 1
            if node.book.isbn == isbn:
                return node.book, idx, steps
            node = node.next
        return None, idx, steps

    def search(self, isbn: str) -> Optional[Book]:
        return self.search_with_trace(isbn)[0]

    def update(self, isbn: str, updated_data: dict) -> bool:
        book = self.search(isbn)
        if book is None:
            return False
        for key, value in updated_data.items():
            if key != "isbn" and hasattr(book, key):
                setattr(book, key, value)
        return True

    def delete(self, isbn: str) -> bool:
        isbn = str(isbn).strip()
        idx = self.hash_function(isbn)
        prev, node = None, self.buckets[idx]
        while node:
            if node.book.isbn == isbn:
                if prev is None:
                    self.buckets[idx] = node.next
                else:
                    prev.next = node.next
                self.count -= 1
                return True
            prev, node = node, node.next
        return False

    # ---- helpers / reporting ----
    def all_books(self) -> Iterator[Book]:
        for head in self.buckets:
            node = head
            while node:
                yield node.book
                node = node.next

    def display_table(self) -> List[dict]:
        rows = []
        for i, head in enumerate(self.buckets):
            chain, node = [], head
            while node:
                chain.append(node.book)
                node = node.next
            rows.append({"index": i, "books": chain, "length": len(chain),
                         "empty": not chain, "collision": len(chain) > 1})
        return rows

    def get_statistics(self) -> dict:
        lengths = [r["length"] for r in self.display_table()]
        occupied = sum(1 for n in lengths if n > 0)
        return {
            "table_size": self.size,
            "records": self.count,
            "occupied_buckets": occupied,
            "empty_buckets": self.size - occupied,
            "collisions": sum(n - 1 for n in lengths if n > 1),
            "load_factor": self.count / self.size if self.size else 0.0,
            "chain_lengths": lengths,
            "max_chain": max(lengths) if lengths else 0,
        }
