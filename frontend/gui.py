import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QPushButton, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox
)
from PySide6.QtCore import QDate
from backend import crud, validation
from backend.validation import CATEGORIES


class ExpenseTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Tracker")
        self.setGeometry(200, 200, 800, 600)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add tabs
        self.tabs.addTab(self.add_expense_tab(), "➕ Add Expense")
        self.tabs.addTab(self.list_expenses_tab(), "📋 List Expenses")

    # ---------------- Add Expense Tab ----------------
    def add_expense_tab(self):
        widget = QWidget()
        layout = QFormLayout()

        # Main category
        self.main_cat_box = QComboBox()
        self.main_cat_box.addItems(CATEGORIES.keys())
        self.main_cat_box.currentTextChanged.connect(self.update_mid_cat)

        # Mid category
        self.mid_cat_box = QComboBox()
        self.mid_cat_box.currentTextChanged.connect(self.update_sub_cat)

        # Sub category
        self.sub_cat_box = QComboBox()

        # Initialize mid & sub options
        self.update_mid_cat(self.main_cat_box.currentText())

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        # Value
        self.value_input = QLineEdit()

        # Notes
        self.notes_input = QTextEdit()

        # Button
        submit_btn = QPushButton("Add Expense")
        submit_btn.clicked.connect(self.add_expense)

        # Layout
        layout.addRow("Main Category:", self.main_cat_box)
        layout.addRow("Mid Category:", self.mid_cat_box)
        layout.addRow("Sub Category:", self.sub_cat_box)
        layout.addRow("Date:", self.date_edit)
        layout.addRow("Value:", self.value_input)
        layout.addRow("Notes:", self.notes_input)
        layout.addRow(submit_btn)

        widget.setLayout(layout)
        return widget

    def update_mid_cat(self, main_cat):
        self.mid_cat_box.clear()
        self.sub_cat_box.clear()
        for mid in CATEGORIES[main_cat].keys():
            self.mid_cat_box.addItem(mid)
        if self.mid_cat_box.count() > 0:
            self.update_sub_cat(self.mid_cat_box.currentText())

    def update_sub_cat(self, mid_cat):
        self.sub_cat_box.clear()
        main_cat = self.main_cat_box.currentText()
        subs = CATEGORIES[main_cat][mid_cat]
        if subs is None:
            self.sub_cat_box.addItem("")
        else:
            self.sub_cat_box.addItems(subs)

    def add_expense(self):
        try:
            main_cat = self.main_cat_box.currentText()
            mid_cat = self.mid_cat_box.currentText()
            sub_cat = self.sub_cat_box.currentText() or None
            date = self.date_edit.date().toString("yyyy-MM-dd")
            value = float(self.value_input.text().replace(",", "."))
            notes = self.notes_input.toPlainText()

            exp_id = crud.add_expense(main_cat, mid_cat, sub_cat, date, value, notes)
            QMessageBox.information(self, "Success", f"Expense added (ID {exp_id}).")
            self.value_input.clear()
            self.notes_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ---------------- List Expenses Tab ----------------
    def list_expenses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Main", "Mid", "Sub", "Date", "Value", "Notes"])
        layout.addWidget(self.table)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_expenses)
        layout.addWidget(refresh_btn)

        widget.setLayout(layout)
        self.load_expenses()
        return widget

    def load_expenses(self):
        expenses = crud.get_expenses()
        self.table.setRowCount(len(expenses))
        for row, exp in enumerate(expenses):
            for col, val in enumerate(exp):
                self.table.setItem(row, col, QTableWidgetItem(str(val)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())
