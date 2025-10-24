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
from datetime import date, timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import defaultdict
import matplotlib as mpl
import numpy as np

class PieChartCanvas(FigureCanvas):
    COLOR_MAP = {}  # stores persistent colors for labels
    PALETTE = list(mpl.colormaps["tab20"].colors)  # 20 distinct colors

    def __init__(self, title, on_slice_click=None):
        self.fig = Figure(figsize=(3, 3))
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.title = title
        self.on_slice_click = on_slice_click  # callback from parent
        self.draw_empty()

        # enable picking (click detection)
        self.mpl_connect("pick_event", self.on_pick)

    def draw_empty(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No Data", ha="center", va="center", fontsize=12, color="gray")
        self.ax.set_title(self.title)
        self.ax.axis("off")
        self.draw()

    def plot_pie(self, data_dict):
        self.ax.clear()

        if not data_dict or sum(data_dict.values()) == 0:
            self.draw_empty()
            return

        labels = list(data_dict.keys())
        sizes = list(data_dict.values())
        total = sum(sizes)


        # assign colors deterministically
        for label in labels:
            if label not in PieChartCanvas.COLOR_MAP:
                idx = len(PieChartCanvas.COLOR_MAP) % len(PieChartCanvas.PALETTE)
                PieChartCanvas.COLOR_MAP[label] = PieChartCanvas.PALETTE[idx]

        colors = [PieChartCanvas.COLOR_MAP[label] for label in labels]

        #Plot pie just with percentage 
        #self.ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, colors=colors)
        #or percentage + total
        #self.ax.pie(sizes, labels=labels, autopct=lambda p: f"{p:.1f}%\n(${p * total / 100:.2f})", startangle=140, colors=colors)
        #self.ax.set_title(self.title)
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            colors=colors,
            startangle=140,
            autopct="%1.1f%%",
            textprops={'color': 'white', 'fontsize': 9},
            wedgeprops={'picker': True}  # enable clicking wedges
)
        # --- Legend on the right ---
        #normal legend
        #legend_labels = [f"{lbl}: ${val:.2f}" for lbl, val in zip(labels, sizes)]
        # --- Truncate long labels for legend display ---
        def shorten_label(label, max_length=15):
            return label if len(label) <= max_length else label[:max_length - 3] + "..."
        legend_labels = [f"{shorten_label(lbl)}: ${val:.2f}" for lbl, val in zip(labels, sizes)]
        self.ax.legend(wedges,legend_labels,loc="center left",bbox_to_anchor=(1.05, 0.5),fontsize=8,frameon=False)

        # --- Title and total below ---
        self.ax.set_title(self.title, fontsize=12, fontweight="bold", pad=20)
        self.ax.text(0.5, -0.2,f"Total: ${total:.2f}",ha="center",fontsize=10,color="#333",fontweight="bold",transform=self.ax.transAxes)

        self.ax.axis("equal")
        self.fig.tight_layout()
        self.draw()

        self._wedges = wedges
        self._labels = labels

    def on_pick(self, event):
        if not hasattr(event, "artist"):
            return

        wedge = event.artist
        label = wedge.get_label() if hasattr(wedge, "get_label") else None

        # fallback: find which wedge was clicked based on its index
        if not label and hasattr(self, "_labels"):
            for i, w in enumerate(self._wedges):
                if wedge == w:
                    label = self._labels[i]
                    break

        if label and self.on_slice_click:
            self.on_slice_click(self.title, label)


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

    def get_selected_expense_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

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
        layout.addWidget(QLabel("📊 Expense Report"))

        # --- Date Range Widgets ---
        today = QDate.currentDate()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(today.year(), today.month(), 1))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(today)

        # Connect to live chart updates
        self.start_date.dateChanged.connect(self.update_pie_charts)
        self.end_date.dateChanged.connect(self.update_pie_charts)

        # --- Date + Category Filters ---
        date_layout = QFormLayout()
        date_layout.addRow("Start Date:", self.start_date)
        date_layout.addRow("End Date:", self.end_date)
        layout.addLayout(date_layout)

        # Quick buttons
        btn_layout = QHBoxLayout()
        current_month_btn = QPushButton("📅 Current Month")
        current_month_btn.clicked.connect(self.set_current_month)
        current_year_btn = QPushButton("🗓 Current Year")
        current_year_btn.clicked.connect(self.set_current_year)
        btn_layout.addWidget(current_month_btn)
        btn_layout.addWidget(current_year_btn)
        layout.addLayout(btn_layout)

        # --- Category Filters ---
        self.main_box = QComboBox()
        self.main_box.addItems(CATEGORIES.keys())
        self.main_box.currentTextChanged.connect(self.update_mid_box)

        self.mid_box = QComboBox()
        self.mid_box.currentTextChanged.connect(self.update_sub_box)

        self.sub_box = QComboBox()
        self.update_mid_box(self.main_box.currentText())

        cat_layout = QFormLayout()
        cat_layout.addRow("Main:", self.main_box)
        cat_layout.addRow("Mid:", self.mid_box)
        cat_layout.addRow("Sub:", self.sub_box)
        layout.addWidget(QLabel("Filter by Date and/or Category:"))
        layout.addLayout(cat_layout)

        # --- Generate Report Button ---
        gen_btn = QPushButton("📊 Generate Report")
        gen_btn.clicked.connect(self.generate_report)
        layout.addWidget(gen_btn)

        # --- Report Summary ---
        self.report_result_label = QLabel("")
        self.report_result_label.setAlignment(Qt.AlignCenter)
        self.report_result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        layout.addWidget(self.report_result_label)

        # --- Pie Charts ---
        self.pie_main = PieChartCanvas("Main Categories")
        self.pie_daily = PieChartCanvas("Daily Expenses")
        self.pie_month = PieChartCanvas("Month Expenses")
        self.pie_daily = PieChartCanvas("Daily Mid Categories", self.handle_pie_click)
        self.pie_month = PieChartCanvas("Month Mid Categories", self.handle_pie_click)

        pie_layout = QHBoxLayout()
        pie_layout.addWidget(self.pie_main)
        pie_layout.addWidget(self.pie_daily)
        pie_layout.addWidget(self.pie_month)

        #layout.addWidget(QLabel("Category Breakdown (Global)"))
        layout.addLayout(pie_layout)

        # --- Totals Labels (below each pie) ---
        '''totals_layout = QHBoxLayout()
        self.label_main_total = QLabel("Total: $0.00")
        self.label_daily_total = QLabel("Total: $0.00")
        self.label_month_total = QLabel("Total: $0.00")

        for lbl in [self.label_main_total, self.label_daily_total, self.label_month_total]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #444;")

        totals_layout.addWidget(self.label_main_total)
        totals_layout.addWidget(self.label_daily_total)
        totals_layout.addWidget(self.label_month_total)

        layout.addLayout(totals_layout)'''

        self.btn_reset_pies = QPushButton("🔙 Back to Main View")
        self.btn_reset_pies.clicked.connect(self.reset_pies)
        layout.addWidget(self.btn_reset_pies)

        widget.setLayout(layout)

        # Initialize pie charts
        self.update_pie_charts()

        return widget

    def generate_report(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        main = self.main_box.currentText()
        mid = self.mid_box.currentText()
        sub = self.sub_box.currentText()
        if sub == "":
            sub = None

        # --- logic ---
        total = reports.get_total_filtered(main, mid, sub, start, end)

        filters = []
        if main:
            filters.append(main)
        if mid:
            filters.append(mid)
        if sub:
            filters.append(sub)

        filter_text = " > ".join(filters) if filters else "All Categories"
        summary_text = f"💰 Total from {start} to {end} for {filter_text}: ${total:.2f}"

        # --- Generate Pie Chart Data ---
        from collections import defaultdict

        expenses = reports.expenses = reports.get_expenses_filtered(
            main=main or None,
            mid=mid or None,
            sub=sub or None,
            start=start or None,
            end=end or None
        )

        main_totals = defaultdict(float)
        mid_totals = defaultdict(float)
        sub_totals = defaultdict(float)

        for exp in expenses:
            try:
                value = float(exp[4])  # Convert safely
            except (ValueError, TypeError):
                value = 0.0

            main_totals[exp[1]] += value
            mid_totals[exp[2]] += value
            sub_totals[exp[3]] += value

        # --- Update Pie Charts ---
        self.pie_main.plot_pie(main_totals)
        self.pie_mid.plot_pie(mid_totals)
        self.pie_sub.plot_pie(sub_totals)

        self.report_result_label.setText(summary_text)

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

    def set_current_month(self):
        today = date.today()
        start = date(today.year, today.month, 1)
        # Compute last day of month safely
        if today.month == 12:
            end = date(today.year, 12, 31)
        else:
            next_month = date(today.year, today.month + 1, 1)
            end = next_month.replace(day=1) - timedelta(days=1)
        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))

        self.update_pie_charts()

    def set_current_year(self):
        today = date.today()
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))

        self.update_pie_charts()

    def update_pie_charts(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        expenses = reports.get_expenses_by_date_range(start, end)
        if not expenses:
            self.pie_main.draw_empty()
            self.pie_daily.draw_empty()
            self.pie_month.draw_empty()
            return

        from collections import defaultdict
        main_totals = defaultdict(float)
        daily_mid_totals = defaultdict(float)
        month_mid_totals = defaultdict(float)

        for exp in expenses:
            main, mid, value = exp[1], exp[2], float(exp[5])
            main_totals[main] += value

            if main == "Daily Expenses":
                daily_mid_totals[mid] += value
            elif main == "Month Expenses":
                month_mid_totals[mid] += value

        # Draw the pies
        self.pie_main.plot_pie(main_totals)
        self.pie_daily.plot_pie(daily_mid_totals)
        self.pie_month.plot_pie(month_mid_totals)

        # Draw labels
        #self.label_main_total.setText(f"Total: ${sum(main_totals.values()):.2f}")
        #self.label_daily_total.setText(f"Total: ${sum(daily_mid_totals.values()):.2f}")
        #self.label_month_total.setText(f"Total: ${sum(month_mid_totals.values()):.2f}")

    def handle_pie_click(self, chart_title, category_clicked):
        print(f"[DEBUG] Clicked on {category_clicked} in {chart_title}")

        if chart_title == "Daily Mid Categories":
            subs = self.get_sub_totals("Daily Expenses", category_clicked)
            self.pie_daily.plot_pie(subs)
            self.current_daily_mid = category_clicked  # track state

        elif chart_title == "Month Mid Categories":
            subs = self.get_sub_totals("Month Expenses", category_clicked)
            self.pie_month.plot_pie(subs)
            self.current_month_mid = category_clicked

    def get_sub_totals(self, main_category, mid_category):
        from collections import defaultdict
        subs = defaultdict(float)

        expenses = reports.get_expenses_by_date_range(
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )

        for exp in expenses:
            if exp[1] == main_category and exp[2] == mid_category:
                subs[exp[3]] += float(exp[5])

        return dict(subs)

    def reset_pies(self):
        self.update_pie_charts()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())
