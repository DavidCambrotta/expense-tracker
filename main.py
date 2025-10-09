from backend.database import init_db
from frontend.cli import menu
from frontend.gui import ExpenseTracker
from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    init_db()

    # Ask user which mode to run
    mode = input("Choose mode: (1) CLI  (2) GUI → ").strip()

    if mode == "1":
        menu()
    elif mode == "2":
        app = QApplication(sys.argv)
        window = ExpenseTracker()
        window.show()
        sys.exit(app.exec())
    else:
        print("Invalid option. Exiting.")
