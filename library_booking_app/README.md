# Library Booking System Using Hash Table (Python + Streamlit)

A browser-based library dashboard written **entirely in Python**. Books are stored in a
**custom hash table with separate chaining**; SQLite (built-in `sqlite3`) only provides persistence.

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit interface and navigation |
| `hash_table.py` | `LibraryHashTable` (linked-list chaining) |
| `models.py` | `Book` and `Transaction` models |
| `storage.py` | SQLite persistence |
| `service.py` | Validation + keeps SQLite and hash table in sync |
| `tests/test_library.py` | Unit tests |

## Run locally
1. Install Python 3.9+
2. `pip install -r requirements.txt`
3. `streamlit run app.py`
4. Open the URL shown (usually http://localhost:8501)

Click **Load sample books** in the sidebar to get demo data.

## Accounts and library workflows
On the first run, create the librarian account from the sign-in screen. Students can then register
their own accounts. Librarians can also create accounts, issue and return books, manage borrowing
limits, and review reservations and fines. Students can browse, borrow, reserve, and view their own
loans and profile.

Late returns accrue a fine of **1.00 per overdue day**. Librarians can record payment for returned
loans with an outstanding fine. Reservation requests are queued in order; a returned copy is marked
ready for the first student in line.

The app stores account password hashes and salts in SQLite. The local `library.db` file contains
the app's accounts and library data; protect it accordingly.

## Run tests
`python -m unittest discover -s tests -v`

## Deploy (Streamlit Community Cloud)
Push the project to GitHub, sign in at share.streamlit.io, choose the repo and `app.py` as the main file.
Note: free hosting may reset the filesystem on restart, so `library.db` is not guaranteed to persist there
(use a persistent database for production). Basic online Python compilers do **not** support Streamlit.

## How the hash table works
- **Hash function:** sum of ISBN digits mod 10 (non-digits ignored).
- **Table:** 10 buckets, each the head of a linked list of books.
- **Insert:** hash → walk the chain (reject duplicates) → append at tail.
- **Search:** hash → walk only that chain.
- **Delete:** hash → unlink the node from its chain.
- **Collisions** = records beyond the first in each occupied bucket. **Load factor** = records / 10.

## Collision demo
1. Add ISBN `101` → bucket 2 (1+0+1).
2. Add ISBN `111` → bucket 3.
3. Add ISBN `110` → bucket 2 (1+1+0): collision, chained after `101`.
4. Open **Hash Table Explorer**: bucket 2 shows `[101] … → [110] … → None`; Statistics shows collisions = 1.
