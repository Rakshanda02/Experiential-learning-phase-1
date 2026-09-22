# ============================================================
# LIBRARY BOOKING SYSTEM USING HASH TABLE
# PHASE-II
# ============================================================

class LibraryHashTable:

    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]

    # --------------------------------------------------------
    # Hash Function
    # --------------------------------------------------------
    def hash_function(self, isbn):
        digits = ""

        for ch in isbn:
            if ch.isdigit():
                digits += ch

        if digits == "":
            return 0

        return int(digits) % self.size

    # --------------------------------------------------------
    # Find Book
    # --------------------------------------------------------
    def find_book(self, isbn):
        index = self.hash_function(isbn)

        for book in self.table[index]:
            if book["isbn"] == isbn:
                return book

        return None

    # --------------------------------------------------------
    # 1. Insert Book
    # --------------------------------------------------------
    def insert_book(self, isbn, title, author):

        if self.find_book(isbn) is not None:
            print("\nBook with this ISBN already exists!")
            return

        index = self.hash_function(isbn)

        book = {
            "isbn": isbn,
            "title": title,
            "author": author,
            "available": True
        }

        # Collision handled using chaining
        if len(self.table[index]) > 0:
            print("Collision occurred at index", index)
            print("Using chaining...")

        self.table[index].append(book)

        print("\nBook inserted successfully!")
        print("Hash Index:", index)

    # --------------------------------------------------------
    # 2. Search Book
    # --------------------------------------------------------
    def search_book(self, isbn):

        book = self.find_book(isbn)

        if book is None:
            print("\nBook not found!")
        else:
            print("\nBook Found")
            print("ISBN       :", book["isbn"])
            print("Title      :", book["title"])
            print("Author     :", book["author"])

            if book["available"]:
                print("Status     : Available")
            else:
                print("Status     : Issued")

    # --------------------------------------------------------
    # 3. Delete Book
    # --------------------------------------------------------
    def delete_book(self, isbn):

        index = self.hash_function(isbn)

        for i in range(len(self.table[index])):

            if self.table[index][i]["isbn"] == isbn:

                self.table[index].pop(i)

                print("\nBook deleted successfully!")
                return

        print("\nBook not found!")

    # --------------------------------------------------------
    # 4. Display All Books
    # --------------------------------------------------------
    def display_books(self):

        found = False

        print("\n========== ALL BOOKS ==========")

        for bucket in self.table:

            for book in bucket:

                found = True

                print("----------------------------")
                print("ISBN   :", book["isbn"])
                print("Title  :", book["title"])
                print("Author :", book["author"])

                if book["available"]:
                    print("Status : Available")
                else:
                    print("Status : Issued")

        if not found:
            print("No books in library.")

    # --------------------------------------------------------
    # 5. Update Book
    # --------------------------------------------------------
    def update_book(self, isbn):

        book = self.find_book(isbn)

        if book is None:
            print("\nBook not found!")
            return

        print("\nCurrent Book Details")
        print("Title :", book["title"])
        print("Author:", book["author"])

        new_title = input("Enter new title: ")
        new_author = input("Enter new author: ")

        if new_title != "":
            book["title"] = new_title

        if new_author != "":
            book["author"] = new_author

        print("\nBook updated successfully!")

    # --------------------------------------------------------
    # 6. Issue / Book a Book
    # --------------------------------------------------------
    def issue_book(self, isbn):

        book = self.find_book(isbn)

        if book is None:
            print("\nBook not found!")
            return

        if not book["available"]:
            print("\nBook is already issued!")
            return

        book["available"] = False

        print("\nBook issued successfully!")

    # --------------------------------------------------------
    # 7. Return Book
    # --------------------------------------------------------
    def return_book(self, isbn):

        book = self.find_book(isbn)

        if book is None:
            print("\nBook not found!")
            return

        if book["available"]:
            print("\nBook is already available!")
            return

        book["available"] = True

        print("\nBook returned successfully!")

    # --------------------------------------------------------
    # 8. Search By Title
    # --------------------------------------------------------
    def search_by_title(self, title):

        found = False

        print("\n========== SEARCH RESULT ==========")

        for bucket in self.table:

            for book in bucket:

                if title.lower() in book["title"].lower():

                    found = True

                    print("----------------------------")
                    print("ISBN   :", book["isbn"])
                    print("Title  :", book["title"])
                    print("Author :", book["author"])

                    if book["available"]:
                        print("Status : Available")
                    else:
                        print("Status : Issued")

        if not found:
            print("No book found with this title.")

    # --------------------------------------------------------
    # 9. Display Hash Table
    # --------------------------------------------------------
    def display_hash_table(self):

        print("\n========== HASH TABLE ==========")

        for i in range(self.size):

            print("Index", i, ":", end=" ")

            if len(self.table[i]) == 0:
                print("Empty")

            else:

                for book in self.table[i]:
                    print(book["isbn"], end=" -> ")

                print("None")

    # --------------------------------------------------------
    # 10. Statistics
    # --------------------------------------------------------
    def statistics(self):

        total_books = 0
        available_books = 0
        issued_books = 0
        collision_count = 0

        for bucket in self.table:

            # Every extra book in same bucket is a collision
            if len(bucket) > 1:
                collision_count += len(bucket) - 1

            for book in bucket:

                total_books += 1

                if book["available"]:
                    available_books += 1
                else:
                    issued_books += 1

        print("\n========== LIBRARY STATISTICS ==========")
        print("Total Books     :", total_books)
        print("Available Books :", available_books)
        print("Issued Books    :", issued_books)
        print("Collisions      :", collision_count)
        print("Hash Table Size :", self.size)


# ============================================================
# MAIN PROGRAM
# ============================================================

library = LibraryHashTable(10)

while True:

    print("\n====================================")
    print("       LIBRARY BOOKING SYSTEM")
    print("====================================")

    print("1. Insert Book")
    print("2. Search Book")
    print("3. Delete Book")
    print("4. Display All Books")
    print("5. Update Book")
    print("6. Issue / Book Book")
    print("7. Return Book")
    print("8. Search Book By Title")
    print("9. Display Hash Table")
    print("10. Library Statistics")
    print("11. Exit")

    choice = input("\nEnter your choice: ")

    # --------------------------------------------------------
    # OPTION 1
    # --------------------------------------------------------
    if choice == "1":

        isbn = input("Enter ISBN: ")
        title = input("Enter Book Title: ")
        author = input("Enter Author Name: ")

        library.insert_book(isbn, title, author)

    # --------------------------------------------------------
    # OPTION 2
    # --------------------------------------------------------
    elif choice == "2":

        isbn = input("Enter ISBN to search: ")

        library.search_book(isbn)

    # --------------------------------------------------------
    # OPTION 3
    # --------------------------------------------------------
    elif choice == "3":

        isbn = input("Enter ISBN to delete: ")

        library.delete_book(isbn)

    # --------------------------------------------------------
    # OPTION 4
    # --------------------------------------------------------
    elif choice == "4":

        library.display_books()

    # --------------------------------------------------------
    # OPTION 5
    # --------------------------------------------------------
    elif choice == "5":

        isbn = input("Enter ISBN to update: ")

        library.update_book(isbn)

    # --------------------------------------------------------
    # OPTION 6
    # --------------------------------------------------------
    elif choice == "6":

        isbn = input("Enter ISBN to issue/book: ")

        library.issue_book(isbn)

    # --------------------------------------------------------
    # OPTION 7
    # --------------------------------------------------------
    elif choice == "7":

        isbn = input("Enter ISBN to return: ")

        library.return_book(isbn)

    # --------------------------------------------------------
    # OPTION 8
    # --------------------------------------------------------
    elif choice == "8":

        title = input("Enter title to search: ")

        library.search_by_title(title)

    # --------------------------------------------------------
    # OPTION 9
    # --------------------------------------------------------
    elif choice == "9":

        library.display_hash_table()

    # --------------------------------------------------------
    # OPTION 10
    # --------------------------------------------------------
    elif choice == "10":

        library.statistics()

    # --------------------------------------------------------
    # OPTION 11
    # --------------------------------------------------------
    elif choice == "11":

        print("\nThank you for using Library Booking System!")
        break

    # --------------------------------------------------------
    # INVALID CHOICE
    # --------------------------------------------------------
    else:

        print("\nInvalid choice! Please enter 1 to 11.")