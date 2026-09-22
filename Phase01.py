# ---------------------------------------------------------
# Library Book Indexing System Using Hash Tables
# ---------------------------------------------------------
# A Python dictionary is used as a hash table.
# ISBN is used as the unique key.
# Book title and author are stored as the value.
# ---------------------------------------------------------


# Create an empty dictionary to store books
library = {}


# Run the program continuously until the user chooses Exit
while True:

    # Display the menu
    print("\n===== LIBRARY BOOK INDEXING SYSTEM =====")
    print("1. Insert Book")
    print("2. Search Book")
    print("3. Delete Book")
    print("4. Display Books")
    print("5. Exit")

    # Take the user's choice
    choice = input("Enter your choice: ")


    # -----------------------------------------------------
    # 1. INSERT BOOK
    # -----------------------------------------------------
    if choice == "1":

        # Take book details from the user
        isbn = input("Enter ISBN: ")
        title = input("Enter Book Title: ")
        author = input("Enter Author: ")

        # Store the book in the hash table
        # ISBN is the key
        # Title and Author are the values
        library[isbn] = [title, author]

        print("Book added successfully!")


    # -----------------------------------------------------
    # 2. SEARCH BOOK
    # -----------------------------------------------------
    elif choice == "2":

        # Ask the user for the ISBN to search
        isbn = input("Enter ISBN: ")

        # Check if the ISBN exists in the hash table
        if isbn in library:

            print("Book Found!")

            # Display the book details
            print("Title:", library[isbn][0])
            print("Author:", library[isbn][1])

        else:
            # ISBN does not exist
            print("Book Not Found!")


    # -----------------------------------------------------
    # 3. DELETE BOOK
    # -----------------------------------------------------
    elif choice == "3":

        # Ask the user for the ISBN to delete
        isbn = input("Enter ISBN: ")

        # Check if the book exists
        if isbn in library:

            # Delete the book using its ISBN
            del library[isbn]

            print("Book deleted successfully!")

        else:
            print("Book Not Found!")


    # -----------------------------------------------------
    # 4. DISPLAY ALL BOOKS
    # -----------------------------------------------------
    elif choice == "4":

        # Check whether the library is empty
        if not library:
            print("Library is empty!")

        else:
            print("\n===== LIBRARY BOOKS =====")

            # Go through each book in the hash table
            for isbn, details in library.items():

                # Display ISBN, title and author
                print("ISBN:", isbn)
                print("Title:", details[0])
                print("Author:", details[1])
                print("------------------------")


    # -----------------------------------------------------
    # 5. EXIT
    # -----------------------------------------------------
    elif choice == "5":

        # End the program
        print("Thank you for using the Library System!")
        break


    # -----------------------------------------------------
    # INVALID CHOICE
    # -----------------------------------------------------
    else:

        # Display message for an invalid menu choice
        print("Invalid choice! Please try again.")