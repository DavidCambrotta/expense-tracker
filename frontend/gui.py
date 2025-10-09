import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QPushButton, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import QDate
from backend import crud
from backend.validation import CATEGORIES


class ExpenseTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Tracker")
        self.setGeometry(200, 200, 900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.add_expense_tab(), "➕ Add Expense")
        self.tabs.addTab(self.list_expenses_tab(), "📋 List Expenses")

    # ---------------- Add Expense Tab ----------------
    def add_expense_tab(self):
        widget = QWidget()
        layout = QFormLayout()

        self.main_cat_box = QComboBox()
        self.main_cat_box.addItems(CATEGORIES.keys())
        self.main_cat_box.currentTextChanged.connect(self.update_mid_cat)

        self.mid_cat_box = QComboBox()
        self.mid_cat_box.currentTextChanged.connect(self.update_sub_cat)

        self.sub_cat_box = QComboBox()
        self.update_mid_cat(self.main_cat_box.currentText())

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.value_input = QLineEdit()
        self.notes_input = QTextEdit()

        submit_btn = QPushButton("Add Expense")
        submit_btn.clicked.connect(self.add_expense)

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
            self.load_expenses()  # refresh list
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


    # ---------------- List Expenses Tab ----------------
    def list_expenses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # --- Filter Controls ---
        filter_layout = QHBoxLayout()
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "By Year", "By Year and Month"])
        self.filter_type.currentIndexChanged.connect(self.update_filter_options)

        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{i:02d}" for i in range(1, 13)])

        apply_btn = QPushButton("✅ Apply Filter")
        apply_btn.clicked.connect(self.load_expenses)

        clear_btn = QPushButton("🧹 Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)

        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_type)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(apply_btn)
        filter_layout.addWidget(clear_btn)

        layout.addLayout(filter_layout)

        self.current_filter_label = QLabel("Showing: All expenses")
        layout.addWidget(self.current_filter_label)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Main", "Mid", "Sub", "Date", "Value", "Notes"])
        self.table.hideColumn(0)  # hide ID column
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()

        delete_btn = QPushButton("🗑 Delete")
        delete_btn.clicked.connect(self.delete_expense)
        btn_layout.addWidget(delete_btn)

        update_btn = QPushButton("✏️ Update")
        update_btn.clicked.connect(self.update_expense)
        btn_layout.addWidget(update_btn)

        layout.addLayout(btn_layout)

        widget.setLayout(layout)

        # --- Initial setup ---
        self.load_years()
        self.update_filter_options()
        self.load_expenses()

        return widget

    def update_filter_options(self):
        """Show/hide year/month selectors depending on filter type."""
        mode = self.filter_type.currentText()
        if mode == "All":
            self.year_combo.setVisible(False)
            self.month_combo.setVisible(False)
        elif mode == "By Year":
            self.year_combo.setVisible(True)
            self.month_combo.setVisible(False)
        elif mode == "By Year and Month":
            self.year_combo.setVisible(True)
            self.month_combo.setVisible(True)

    def clear_filters(self):
        """Reset filter combo boxes to default."""
        self.filter_type.setCurrentText("All")
        self.update_filter_options()
        self.load_expenses()

    def load_expenses(self):
        """Load and display expenses with active filters."""
        filter_mode = self.filter_type.currentText()
        expenses = []

        try:
            if filter_mode == "All":
                expenses = crud.get_expenses()
                self.current_filter_label.setText("Showing: All expenses")
            elif filter_mode == "By Year":
                year = int(self.year_combo.currentText())
                expenses = crud.get_expenses(year=year)
                self.current_filter_label.setText(f"Showing: Expenses from {year}")
                
            elif filter_mode == "By Year and Month":
                year = int(self.year_combo.currentText())
                month = int(self.month_combo.currentText())
                expenses = crud.get_expenses(year=year, month=month)
                self.current_filter_label.setText(f"Showing: Expenses from {year}-{month}")

        except Exception:
            expenses = crud.get_expenses()  # fallback if any error

        # Sort by date ASC
        expenses = sorted(
            [e for e in expenses if e[4] is not None],
            key=lambda e: e[4],
            reverse=True
        )
        # Display in table
        self.table.setRowCount(len(expenses))
        for row, exp in enumerate(expenses):
            for col, val in enumerate(exp):
                display_val = "" if val is None else str(val)
                self.table.setItem(row, col, QTableWidgetItem(display_val))

        self.table.resizeColumnsToContents()

    def load_years(self):
        """Load available years dynamically (fallback if unavailable)."""
        years = crud.get_available_years() if hasattr(crud, "get_available_years") else []
        self.year_combo.clear()
        if years:
            self.year_combo.addItems([str(y) for y in years])
        else:
            current_year = QDate.currentDate().year()
            self.year_combo.addItems([str(y) for y in range(current_year - 10, current_year + 1)])

    def load_years(self):
        """Load available years into year filter combo."""
        years = crud.get_available_years() if hasattr(crud, "get_available_years") else []
        self.year_combo.clear()
        if years:
            self.year_combo.addItems([str(y) for y in years])
        else:
            # fallback if no function implemented
            self.year_combo.addItems([str(y) for y in range(2015, QDate.currentDate().year() + 1)])


    def get_selected_expense_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def load_years(self):
        years = crud.get_available_years()  # we’ll add this next
        self.year_combo.clear()
        self.year_combo.addItems([str(y) for y in years])

    def delete_expense(self):
        exp_id = self.get_selected_expense_id()
        if not exp_id:
            QMessageBox.warning(self, "Warning", "Select an expense first.")
            return
        try:
            crud.delete_expense(exp_id)
            QMessageBox.information(self, "Deleted", f"Expense {exp_id} deleted.")
            self.load_expenses()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_expense(self):
        exp_id = self.get_selected_expense_id()
        if not exp_id:
            QMessageBox.warning(self, "Warning", "Select an expense first.")
            return

        row = self.table.currentRow()
        try:
            main_cat = self.table.item(row, 1).text()
            mid_cat = self.table.item(row, 2).text()
            sub_cat = self.table.item(row, 3).text() or None
            date = self.table.item(row, 4).text()
            value = float(self.table.item(row, 5).text())
            notes = self.table.item(row, 6).text()

            crud.update_expense(exp_id, main_cat, mid_cat, sub_cat, date, value, notes)
            QMessageBox.information(self, "Updated", f"Expense {exp_id} updated.")
            self.load_expenses()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())
