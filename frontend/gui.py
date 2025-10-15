import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QPushButton, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import QDate, Qt
from backend import crud, reports
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
        self.tabs.addTab(self.reports_tab(), "📊 Reports")

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

# ---------------- Reports  Tab ----------------
    def reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Report Type Selector
        self.report_type = QComboBox()
        self.report_type.addItems(["By Date", "By Category"])
        self.report_type.currentIndexChanged.connect(self.update_report_mode)

        layout.addWidget(QLabel("Select Report Type:"))
        layout.addWidget(self.report_type)

        # Date Range Widgets
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())  # ✅ start today

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())    # ✅ end today

        # Category Widgets
        self.main_box = QComboBox()
        self.main_box.addItems(CATEGORIES.keys())
        self.main_box.currentTextChanged.connect(self.update_mid_box)

        self.mid_box = QComboBox()
        self.mid_box.currentTextChanged.connect(self.update_sub_box)

        self.sub_box = QComboBox()

        self.update_mid_box(self.main_box.currentText())

        # Stack for dynamic inputs
        self.date_range_box = QWidget()
        date_layout = QFormLayout()
        date_layout.addRow("Start Date:", self.start_date)
        date_layout.addRow("End Date:", self.end_date)
        self.date_range_box.setLayout(date_layout)

        self.category_box = QWidget()
        cat_layout = QFormLayout()
        cat_layout.addRow("Main:", self.main_box)
        cat_layout.addRow("Mid:", self.mid_box)
        cat_layout.addRow("Sub:", self.sub_box)
        self.category_box.setLayout(cat_layout)

        layout.addWidget(self.date_range_box)
        layout.addWidget(self.category_box)

        # Generate Button
        gen_btn = QPushButton("📊 Generate Report")
        gen_btn.clicked.connect(self.generate_report)
        layout.addWidget(gen_btn)

        # Results Table
        self.report_table = QTableWidget()
        #self.report_table.setColumnCount(6)
        #self.report_table.setHorizontalHeaderLabels(["Main", "Mid", "Sub", "Date", "Value", "Notes"])
        #layout.addWidget(self.report_table)

        self.report_result_label = QLabel("")
        self.report_result_label.setAlignment(Qt.AlignCenter)
        self.report_result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        layout.addWidget(self.report_result_label)
        
        #comment this one for remove the table
        #layout.addWidget(self.report_table)    

        widget.setLayout(layout)
        self.update_report_mode()  # Initialize visibility
        return widget

    def update_report_mode(self):
        mode = self.report_type.currentText()
        self.date_range_box.setVisible(mode == "By Date")
        self.category_box.setVisible(mode == "By Category")

    def update_mid_box(self, main):
        self.mid_box.clear()
        self.sub_box.clear()
        mids = list(CATEGORIES[main].keys())
        self.mid_box.addItems(mids)
        if mids:
            self.update_sub_box(mids[0])

    def update_sub_box(self, mid):
        self.sub_box.clear()
        main = self.main_box.currentText()
        subs = CATEGORIES[main][mid]
        if subs:
            self.sub_box.addItems(subs)
        else:
            self.sub_box.addItem("")

    def generate_report(self):
        mode = self.report_type.currentText()

        if mode == "By Date":
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            total = reports.get_total_by_date_range(start, end)
            summary_text = f"💰 Total expenses from {start} to {end}: ${total:.2f}"
        else:
            main = self.main_box.currentText()
            mid = self.mid_box.currentText()
            sub = self.sub_box.currentText()
            if sub == "":
                sub = None
            total = reports.get_total_by_category(main, mid, sub)
            cat_text = " > ".join(filter(None, [main, mid, sub]))
            summary_text = f"💰 Total expenses for {cat_text}: ${total:.2f}"

        self.report_result_label.setText(summary_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())
