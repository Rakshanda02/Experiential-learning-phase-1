"""Library Booking System Using Hash Table - Streamlit interface (Python only)."""
import pandas as pd
import streamlit as st

from service import LibraryService

st.set_page_config(page_title="Library Booking System", page_icon="📚", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #24332d;
        --muted: #68776f;
        --paper: #f5f7f3;
        --line: #dfe6df;
        --forest: #183a31;
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(125deg, rgba(47, 110, 94, 0.055), transparent 38%), var(--paper);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1500px;
        padding: 2.25rem 3rem 3rem;
    }

    h1, h2, h3 {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 600;
    }

    h1 {
        font-size: 2.2rem;
        line-height: 1.2;
    }

    [data-testid="stSidebar"] {
        background: var(--forest);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #f0f4ef;
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.45rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #e5eee7;
        border-color: #e5eee7;
        color: var(--forest);
    }

    [data-testid="stSidebar"] .stButton > button p {
        color: var(--forest);
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        border-radius: 5px;
        padding: 0.18rem 0.35rem;
        transition: background-color 140ms ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.09);
    }

    [data-testid="stMetric"] {
        padding: 1rem 1.05rem;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid var(--line);
        border-radius: 6px;
    }

    [data-testid="stMetricLabel"] p {
        color: var(--muted);
        font-size: 0.82rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--forest);
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.65rem;
        border-radius: 5px;
        font-weight: 600;
        transition: transform 140ms ease, box-shadow 140ms ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(24, 58, 49, 0.12);
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div {
        border-radius: 4px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 5px;
        overflow: hidden;
    }

    [data-testid="stExpander"] {
        border-color: var(--line);
        border-radius: 5px;
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1.35rem 1rem 2rem;
        }

        h1 {
            font-size: 1.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_service() -> LibraryService:
    return LibraryService("library.db", size=10)


svc = get_service()


def show(result):
    """On success: remember the message and rerun so every table/list is fresh."""
    ok, msg = result
    if ok:
        st.session_state["flash"] = msg
        st.rerun()
    st.error(msg)
    return ok


def books_df(books):
    rows = [{"ISBN": b.isbn, "Title": b.title, "Author": b.author, "Category": b.category,
             "Publisher": b.publisher, "Year": b.year, "Total": b.total_copies,
             "Issued": b.issued_copies, "Available": b.available_copies,
             "Bucket": svc.table.hash_function(b.isbn)} for b in books]
    cols = ["ISBN", "Title", "Author", "Category", "Publisher", "Year", "Total", "Issued", "Available", "Bucket"]
    return pd.DataFrame(rows, columns=cols)


def empty_state():
    st.info("The library is empty. Add a book, or load the sample books.")
    if current_user.role == "librarian" and st.button("Load sample books", key=f"sample_{st.session_state.get('page')}"):
        show((True, f"Loaded {svc.load_samples()} sample books."))


def account_access():
    st.title("Library Booking")
    st.caption("Sign in to manage your library account.")
    if not svc.has_librarian():
        st.subheader("Set up the first librarian account")
        with st.form("first_librarian_form"):
            full_name = st.text_input("Full name")
            username = st.text_input("Username")
            email = st.text_input("Email (optional)")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create librarian account", type="primary")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, message = svc.create_first_librarian(username, password, full_name, email)
                if ok:
                    st.session_state["user"] = svc.authenticate(username, password)
                    st.rerun()
                st.error(message)

    sign_in, register = st.tabs(["Sign in", "Student registration"])
    with sign_in:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            user = svc.authenticate(username, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            st.error("Username or password is incorrect.")
    with register:
        with st.form("student_registration_form"):
            full_name = st.text_input("Full name", key="registration_name")
            username = st.text_input("Username", key="registration_username")
            email = st.text_input("Email (optional)", key="registration_email")
            password = st.text_input("Password", type="password", key="registration_password")
            confirm = st.text_input("Confirm password", type="password", key="registration_confirm")
            submitted = st.form_submit_button("Create student account", type="primary")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, message = svc.register_student(username, password, full_name, email)
                if ok:
                    st.session_state["user"] = svc.authenticate(username, password)
                    st.rerun()
                st.error(message)


if "user" not in st.session_state:
    account_access()
    st.stop()

current_user = st.session_state["user"]

# ------------------------------------------------------------------ sidebar
PAGES = ["📊 Dashboard", "➕ Add Book", "🔎 Search Books", "✏️ Update Book", "🗑️ Delete Book",
         "📚 Book Collection", "📤 Issue Book", "📥 Return Book", "🧮 Hash Table Explorer",
         "📈 Hash Table Statistics", "🧾 Transaction History", "⏳ Reservations",
         "👥 User Management", "📈 Popular Books"]
STUDENT_PAGES = [PAGES[0], PAGES[5], PAGES[2], "📖 Browse & Reserve", "👤 My Account"]
NAVIGATION = PAGES if current_user.role == "librarian" else STUDENT_PAGES
st.sidebar.title("📚 Library Booking")
st.sidebar.caption("Custom Hash Table • Separate Chaining")
st.sidebar.caption(f"{current_user.full_name} · {current_user.role.title()}")
page = st.sidebar.radio("Navigate", NAVIGATION, label_visibility="collapsed")
st.session_state["page"] = page
st.sidebar.divider()
if current_user.role == "librarian" and st.sidebar.button("Load sample books"):
    show((True, f"Loaded {svc.load_samples()} sample books."))
if st.sidebar.button("Sign out"):
    st.session_state.pop("user", None)
    st.rerun()
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

books = svc.all_books()

# ---------------------------------------------------------------- dashboard
if page == PAGES[0]:
    st.title("Dashboard")
    s = svc.dashboard_stats()
    if current_user.role == "librarian":
        c = st.columns(4)
        c[0].metric("Book records", s["records"])
        c[1].metric("Total copies", s["total_copies"])
        c[2].metric("Available", s["available"])
        c[3].metric("On loan", s["issued"])
        c = st.columns(3)
        c[0].metric("Occupied buckets", f"{s['occupied_buckets']} / {s['table_size']}")
        c[1].metric("Collisions", s["collisions"])
        c[2].metric("Load factor", f"{s['load_factor']:.2f}")
        left, right = st.columns([3, 2])
        with right:
            st.subheader("Library activity")
            st.metric("Active issues", s["active_txns"])
            st.metric("Overdue", s["overdue"])
            st.metric("Fines outstanding", f"{s['outstanding_fines']:.2f}")
            st.metric("Completed returns", s["returned_txns"])
    else:
        loans = svc.user_transactions(current_user.id)
        active_loans = [txn for txn in loans if not txn.return_date]
        holds = [hold for hold in svc.reservations(current_user.id)
                 if hold.status in ("Ready", "Waiting")]
        c = st.columns(4)
        c[0].metric("Books on loan", len(active_loans))
        c[1].metric("Borrowing limit", current_user.borrow_limit)
        c[2].metric("Active reservations", len(holds))
        c[3].metric("Fines due", f"{sum(svc.fine_amount(txn) for txn in loans if not txn.fine_paid):.2f}")
        left, right = st.columns([3, 2])
        with right:
            st.subheader("Next due dates")
            upcoming = sorted(active_loans, key=lambda txn: txn.due_date)[:5]
            if upcoming:
                st.dataframe(pd.DataFrame([{"Title": txn.title, "Due": txn.due_date}
                                           for txn in upcoming]), hide_index=True, use_container_width=True)
            else:
                st.info("No books currently on loan.")
    with left:
        st.subheader("Recently added books")
        if books:
            st.dataframe(books_df(svc.recent_books())[ ["ISBN", "Title", "Author", "Available", "Bucket"]],
                         hide_index=True, use_container_width=True)
        else:
            empty_state()

# ----------------------------------------------------------------- add book
elif page == PAGES[1]:
    st.title("Add Book")
    with st.form("add_form", clear_on_submit=False):
        a, b = st.columns(2)
        isbn = a.text_input("ISBN *")
        title = b.text_input("Title *")
        author = a.text_input("Author *")
        category = b.text_input("Category / Genre", value="General")
        publisher = a.text_input("Publisher")
        year = b.text_input("Publication year (optional)")
        copies = a.number_input("Number of copies *", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("Add book", type="primary")
    if submitted:
        show(svc.add_book(isbn, title, author, category, publisher, year, copies))

# -------------------------------------------------------------------- search
elif page == PAGES[2]:
    st.title("Search Books")
    a, b = st.columns([1, 3])
    field = a.selectbox("Search by", ["ISBN", "Title", "Author", "Category"])
    query = b.text_input("Search text")
    if query.strip():
        if field == "ISBN":
            book, idx, steps = svc.table.search_with_trace(query)
            st.caption(f"Hash table lookup: bucket {idx}, {steps} chain node(s) compared.")
        results = svc.search(field, query)
        if results:
            st.dataframe(books_df(results), hide_index=True, use_container_width=True)
        else:
            st.warning("No matching books found.")
    elif not books:
        empty_state()
    else:
        st.info("Enter text to search.")

# -------------------------------------------------------------------- update
elif page == PAGES[3]:
    st.title("Update Book")
    if not books:
        empty_state()
    else:
        isbn = st.selectbox("Select ISBN", sorted(b.isbn for b in books))
        bk = svc.table.search(isbn)
        k = f"_{isbn}"
        with st.form("update_form"):
            a, b = st.columns(2)
            title = a.text_input("Title *", bk.title, key="ut" + k)
            author = b.text_input("Author *", bk.author, key="ua" + k)
            category = a.text_input("Category", bk.category, key="uc" + k)
            publisher = b.text_input("Publisher", bk.publisher, key="up" + k)
            year = a.text_input("Publication year", "" if bk.year is None else str(bk.year), key="uy" + k)
            total = b.number_input("Total copies", min_value=1, value=bk.total_copies, step=1, key="un" + k)
            st.caption(f"Currently issued: {bk.issued_copies}")
            go = st.form_submit_button("Update book", type="primary")
        if go:
            show(svc.update_book(isbn, title, author, category, publisher, year, total))

# -------------------------------------------------------------------- delete
elif page == PAGES[4]:
    st.title("Delete Book")
    if not books:
        empty_state()
    else:
        isbn = st.selectbox("Select ISBN", sorted(b.isbn for b in books))
        bk = svc.table.search(isbn)
        st.write(f"**{bk.title}** by {bk.author} — issued copies: {bk.issued_copies}")
        confirm = st.checkbox("I confirm I want to permanently delete this book", key=f"del_{isbn}")
        if st.button("Delete book", type="primary", disabled=not confirm):
            show(svc.delete_book(isbn))

# ---------------------------------------------------------------- collection
elif page == PAGES[5]:
    st.title("Book Collection")
    if not books:
        empty_state()
    else:
        a, b, c = st.columns(3)
        text = a.text_input("Search table")
        cat = b.selectbox("Category", ["All"] + sorted({x.category for x in books}))
        avail = c.selectbox("Availability", ["All", "Available", "Unavailable"])
        view = books
        if cat != "All":
            view = [x for x in view if x.category == cat]
        if avail == "Available":
            view = [x for x in view if x.available_copies > 0]
        elif avail == "Unavailable":
            view = [x for x in view if x.available_copies == 0]
        if text.strip():
            t = text.lower()
            view = [x for x in view if t in f"{x.isbn} {x.title} {x.author} {x.category}".lower()]
        st.caption(f"{len(view)} of {len(books)} books. Click a column header to sort.")
        st.dataframe(books_df(view), hide_index=True, use_container_width=True)

# ----------------------------------------------------------- student services
elif page == "📖 Browse & Reserve":
    st.title("Browse & Reserve")
    if not books:
        st.info("No books are in the collection yet.")
    else:
        selected_isbn = st.selectbox("Choose a book", sorted(b.isbn for b in books),
                                     format_func=lambda isbn: f"{svc.table.search(isbn).title} · {isbn}")
        selected_book = svc.table.search(selected_isbn)
        ready_hold = next((hold for hold in svc.reservations(current_user.id)
                           if hold.isbn == selected_isbn and hold.status == "Ready"), None)
        st.write(f"**{selected_book.title}** by {selected_book.author}")
        st.caption(f"{selected_book.category} · {selected_book.available_copies} copies available")
        loan_count = len([txn for txn in svc.user_transactions(current_user.id) if not txn.return_date])
        st.caption(f"Your current loans: {loan_count} of {current_user.borrow_limit}")
        if ready_hold:
            st.success("A copy is ready for you.")
            if st.button("Borrow reserved copy", type="primary"):
                show(svc.issue_book(selected_isbn, "", user_id=current_user.id,
                                    reservation_id=ready_hold.id))
        elif selected_book.available_copies > 0:
            if st.button("Borrow now", type="primary", disabled=loan_count >= current_user.borrow_limit):
                show(svc.issue_book(selected_isbn, "", user_id=current_user.id))
        else:
            st.info("No copies are available. Join the waiting list for this title.")
        active_hold = next((hold for hold in svc.reservations(current_user.id)
                            if hold.isbn == selected_isbn and hold.status in ("Ready", "Waiting")), None)
        if active_hold:
            st.caption(f"Your reservation status: {active_hold.status}.")
            if st.button("Cancel reservation"):
                show(svc.cancel_reservation(active_hold.id, current_user.id))
        elif not ready_hold and st.button("Reserve this book"):
            show(svc.reserve_book(selected_isbn, current_user.id))

elif page == "👤 My Account":
    st.title("My Account")
    st.subheader("Profile")
    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=current_user.full_name)
        email = st.text_input("Email", value=current_user.email)
        if st.form_submit_button("Save profile", type="primary"):
            result = svc.update_profile(current_user.id, full_name, email)
            if result[0]:
                current_user.full_name = full_name.strip()
                current_user.email = email.strip()
            show(result)
    st.subheader("Loans and fines")
    my_loans = svc.user_transactions(current_user.id)
    if my_loans:
        st.dataframe(pd.DataFrame([{"Title": txn.title, "Issued": txn.issue_date, "Due": txn.due_date,
                                    "Returned": txn.return_date or "On loan",
                                    "Fine": f"{svc.fine_amount(txn):.2f}",
                                    "Fine status": "Paid" if txn.fine_paid else "Due"}
                                   for txn in my_loans]), hide_index=True, use_container_width=True)
        active_loans = [txn for txn in my_loans if not txn.return_date]
        if active_loans:
            labels = {f"#{txn.id} · {txn.title} · due {txn.due_date}": txn.id for txn in active_loans}
            selected_txn = st.selectbox("Return a book", list(labels))
            if st.button("Return selected book", type="primary"):
                show(svc.return_book(labels[selected_txn], current_user.id))
    else:
        st.info("No loan history yet.")
    st.subheader("Reservations")
    my_holds = svc.reservations(current_user.id)
    if my_holds:
        st.dataframe(pd.DataFrame([{"Title": hold.title, "Placed": hold.created_at,
                                    "Status": hold.status} for hold in my_holds]),
                     hide_index=True, use_container_width=True)
    else:
        st.info("No reservations yet.")

# --------------------------------------------------------------------- issue
elif page == PAGES[6]:
    st.title("Issue Book")
    isbn = st.text_input("ISBN")
    if isbn.strip():
        bk = svc.table.search(isbn)
        if bk:
            st.info(f"**{bk.title}** — {bk.available_copies} of {bk.total_copies} available")
        else:
            st.warning("No book with this ISBN.")
    students = [user for user in svc.users() if user.role == "student"]
    if not students:
        st.info("Create a student account in User Management before issuing a book.")
        student_id = None
    else:
        student_labels = {f"{user.full_name} (@{user.username})": user.id for user in students}
        student_label = st.selectbox("Student", list(student_labels))
        student_id = student_labels[student_label]
    days = st.number_input("Loan period (days)", min_value=1, max_value=90, value=14)
    if student_id and st.button("Issue book", type="primary"):
        show(svc.issue_book(isbn, "", days, user_id=student_id))

# -------------------------------------------------------------------- return
elif page == PAGES[7]:
    st.title("Return Book")
    isbn = st.text_input("Filter by ISBN (optional)")
    active = svc.active_transactions(isbn)
    if not active:
        st.info("No active issues found.")
    else:
        labels = {f"#{t.id} • {t.isbn} • {t.title} • {t.student} (due {t.due_date})": t.id for t in active}
        choice = st.selectbox("Select issued book", list(labels))
        if st.button("Return book", type="primary"):
            show(svc.return_book(labels[choice]))

# ------------------------------------------------------------------ explorer
elif page == PAGES[8]:
    st.title("Hash Table Explorer")
    st.caption("hash(ISBN) = (sum of ISBN digits) mod table size. Collisions are resolved by separate chaining.")
    with st.expander("Try the hash function", expanded=True):
        probe = st.text_input("ISBN to hash", value="101")
        if probe.strip():
            digits = [c for c in probe.strip() if c.isdigit()]
            st.write(f"Digits: {' + '.join(digits) or '(none)'} = {sum(int(d) for d in digits)} "
                     f"→ bucket **{svc.table.hash_function(probe)}**")
    if not books:
        empty_state()
    for row in svc.table.display_table():
        with st.container(border=True):
            a, b = st.columns([1, 6])
            a.markdown(f"### Bucket {row['index']}")
            if row["empty"]:
                a.caption("Empty")
                b.markdown("`None`")
            else:
                a.caption("⚠️ Collision" if row["collision"] else "✅ No collision")
                chain = " → ".join(f"`[{bk.isbn}] {bk.title}`" for bk in row["books"])
                b.markdown(chain + " → `None`")

# ---------------------------------------------------------------- statistics
elif page == PAGES[9]:
    st.title("Hash Table Statistics")
    s = svc.table.get_statistics()
    c = st.columns(4)
    c[0].metric("Table size", s["table_size"])
    c[1].metric("Unique records", s["records"])
    c[2].metric("Occupied buckets", s["occupied_buckets"])
    c[3].metric("Empty buckets", s["empty_buckets"])
    c = st.columns(3)
    c[0].metric("Collisions", s["collisions"])
    c[1].metric("Load factor", f"{s['load_factor']:.2f}")
    c[2].metric("Max chain length", s["max_chain"])
    st.caption("Collisions = records beyond the first in each occupied bucket. "
               "Load factor = stored records / table size.")
    df = pd.DataFrame({"Bucket": [str(i) for i in range(s["table_size"])],
                       "Chain length": s["chain_lengths"]}).set_index("Bucket")
    st.subheader("Books per bucket")
    st.bar_chart(df)
    st.dataframe(df.T, use_container_width=True)

# ------------------------------------------------------------------- history
elif page == PAGES[10]:
    st.title("Transaction History")
    flt = st.radio("Show", ["All", "Active issues", "Completed returns"], horizontal=True)
    txns = svc.transactions()
    if flt == "Active issues":
        txns = [t for t in txns if not t.return_date]
    elif flt == "Completed returns":
        txns = [t for t in txns if t.return_date]
    if not txns:
        st.info("No transactions to show.")
    else:
        st.dataframe(pd.DataFrame([{"Transaction ID": t.id, "ISBN": t.isbn, "Title": t.title,
                                    "Student": t.student, "Issue date": t.issue_date,
                                    "Due date": t.due_date, "Return date": t.return_date or "—",
                                    "Status": t.status,
                                    "Fine": f"{svc.fine_amount(t):.2f}",
                                    "Fine paid": "Yes" if t.fine_paid else "No"} for t in txns]),
                     hide_index=True, use_container_width=True)
        unpaid_fines = [txn for txn in txns if txn.return_date and txn.fine_amount > 0 and not txn.fine_paid]
        if unpaid_fines:
            fine_options = {f"#{txn.id} · {txn.student} · {txn.title} · {txn.fine_amount:.2f}": txn.id
                            for txn in unpaid_fines}
            fine_label = st.selectbox("Outstanding returned-book fine", list(fine_options))
            if st.button("Record fine as paid"):
                show(svc.pay_fine(fine_options[fine_label]))

elif page == PAGES[11]:
    st.title("Reservations & Waiting List")
    holds = [hold for hold in svc.reservations() if hold.status in ("Ready", "Waiting")]
    if not holds:
        st.info("There are no active reservations.")
    else:
        st.dataframe(pd.DataFrame([{"Position": index + 1, "Title": hold.title, "ISBN": hold.isbn,
                                    "Student": hold.username, "Placed": hold.created_at,
                                    "Status": hold.status}
                                   for index, hold in enumerate(holds)]),
                     hide_index=True, use_container_width=True)
        ready = [hold for hold in holds if hold.status == "Ready"]
        if ready:
            ready_labels = {f"{hold.title} · {hold.username} · #{hold.id}": hold.id for hold in ready}
            choice = st.selectbox("Ready for pickup", list(ready_labels))
            a, b = st.columns(2)
            if a.button("Issue reserved copy", type="primary"):
                hold = next(item for item in ready if item.id == ready_labels[choice])
                show(svc.issue_book(hold.isbn, hold.username, user_id=hold.user_id,
                                    reservation_id=hold.id))
            if b.button("Cancel selected reservation"):
                show(svc.cancel_reservation(ready_labels[choice]))

elif page == PAGES[12]:
    st.title("User Management")
    with st.expander("Create account", expanded=True):
        with st.form("create_user_form"):
            full_name = st.text_input("Full name", key="new_full_name")
            username = st.text_input("Username", key="new_username")
            email = st.text_input("Email", key="new_email")
            role = st.selectbox("Role", ["student", "librarian"])
            password = st.text_input("Temporary password", type="password", key="new_password")
            limit = st.number_input("Borrowing limit", min_value=1, max_value=20, value=5)
            if st.form_submit_button("Create account", type="primary"):
                show(svc.create_user(username, password, full_name, role, email, int(limit)))
    st.subheader("Registered users")
    users = svc.users()
    if users:
        st.dataframe(pd.DataFrame([{"Name": user.full_name, "Username": user.username,
                                    "Role": user.role.title(), "Email": user.email,
                                    "Borrowing limit": user.borrow_limit if user.role == "student" else "—"}
                                   for user in users]), hide_index=True, use_container_width=True)
        students = [user for user in users if user.role == "student"]
        if students:
            options = {f"{user.full_name} (@{user.username})": user for user in students}
            choice = st.selectbox("Adjust student borrowing limit", list(options))
            selected = options[choice]
            new_limit = st.number_input("New limit", min_value=1, max_value=20,
                                        value=selected.borrow_limit, key=f"limit_{selected.id}")
            if st.button("Save borrowing limit"):
                show(svc.update_borrow_limit(selected.id, int(new_limit)))
    else:
        st.info("No registered users.")

elif page == PAGES[13]:
    st.title("Popular Books")
    popular = svc.popular_books()
    if not popular:
        st.info("Borrowing analytics will appear after books have been issued.")
    else:
        total_borrowings = sum(row["Borrowings"] for row in popular)
        st.metric("Titles borrowed", len(popular))
        st.metric("Total recorded loans", total_borrowings)
        st.subheader("Most frequently borrowed")
        st.bar_chart(pd.DataFrame(popular).set_index("Title")["Borrowings"])
        st.dataframe(pd.DataFrame(popular), hide_index=True, use_container_width=True)
