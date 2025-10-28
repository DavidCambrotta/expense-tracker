import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QPushButton, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHBoxLayout, QSpinBox, QHeaderView
)
from PySide6.QtCore import QDate, Qt
from backend import crud, reports
from backend.validation import CATEGORIES
from datetime import date, datetime, timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from collections import defaultdict
import matplotlib as mpl
import numpy as np
import calendar

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

        wedges, texts, autotexts = self.ax.pie(
            sizes,
            colors=colors,
            startangle=140,
            autopct="%1.1f%%", #autopct=lambda p: f"{p:.1f}%\n(${p * total / 100:.2f})"  -> for % + $
            textprops={'color': 'white', 'fontsize': 9},
            wedgeprops={'picker': True})  # enable clicking wedges

        # --- Legend on the right ---
        #normal legend
        #legend_labels = [f"{lbl}: ${val:.2f}" for lbl, val in zip(labels, sizes)]
        # --- Truncate long labels for legend display ---
        def shorten_label(label, max_length=15):
            if not label:
                return "Unknown"
            label = str(label)
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
        self._current_data = data_dict

    def animate_transition(self, new_data_dict):
        """Animate a smooth transition from current pie to new pie."""
        old_data = getattr(self, "_current_data", {})
        old_labels = list(old_data.keys())
        old_sizes = list(old_data.values())

        new_labels = list(new_data_dict.keys())
        new_sizes = list(new_data_dict.values())

        if not new_labels or sum(new_sizes) == 0:
            self.draw_empty()
            return

        # If old pie doesn't exist, just draw new one
        if not old_labels or len(old_sizes) != len(new_sizes):
            self.plot_pie(new_data_dict)
            return

        # Normalize data lengths by zero-padding shorter one
        max_len = max(len(old_sizes), len(new_sizes))
        while len(old_sizes) < max_len:
            old_sizes.append(0)
        while len(new_sizes) < max_len:
            new_sizes.append(0)

        # Generate interpolated frames between old and new
        frames = 20
        def interpolate(i):
            alpha = i / frames
            interpolated = [
                old_sizes[j] * (1 - alpha) + new_sizes[j] * alpha
                for j in range(max_len)
            ]
            data_dict = {
                (new_labels[j] if j < len(new_labels) else old_labels[j]): interpolated[j]
                for j in range(max_len)
            }
            self.plot_pie(data_dict)

        FuncAnimation(self.fig, interpolate, frames=frames, interval=50, repeat=False)
        self._current_data = new_data_dict

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
        self.tabs.addTab(self.monthly_planner_tab(), "📊 Monthly Planner")
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
        if hasattr(self, "pie_daily"):
            main_data = self.get_mid_totals("Daily Expenses")
            self.pie_daily.animate_transition(main_data)

        if hasattr(self, "pie_month"):
            month_data = self.get_mid_totals("Month Expenses")
            self.pie_month.animate_transition(month_data)

    def get_mid_totals(self, main_category):
        from collections import defaultdict
        mids = defaultdict(float)
        expenses = reports.get_expenses_by_date_range(
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )

        for exp in expenses:
            if exp[1] == main_category:
                mids[exp[2]] += float(exp[5])
        return dict(mids)

    # ---------------- Monthly Planner  Tab ----------------

    def monthly_planner_tab(self):
        """Create the Monthly Planner tab widget."""
        widget = QWidget()
        outer = QVBoxLayout(widget)

        # --- Top controls row (left spacer, right controls) ---
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel(""), 1)  # spacer on left (keeps left area free)

        controls = QHBoxLayout()
        # Year combo (last 10 years)
        self.year_combo_planner = QComboBox()
        current_year = date.today().year
        years = [str(y) for y in range(current_year, current_year - 10, -1)]
        self.year_combo_planner.addItems(years)

        # Month combo
        self.month_combo_planner = QComboBox()
        self.month_combo_planner.addItems([f"{i:02d}" for i in range(1, 13)])

        controls.addWidget(QLabel("Year:"))
        controls.addWidget(self.year_combo_planner)
        controls.addSpacing(8)
        controls.addWidget(QLabel("Month:"))
        controls.addWidget(self.month_combo_planner)
        controls.addSpacing(16)

        # Vacation controls
        self.vacation_combo = QComboBox()
        self.vacation_combo.addItems(["No", "Yes"])
        controls.addWidget(QLabel("Vacation:"))
        controls.addWidget(self.vacation_combo)

        self.vac_start = QDateEdit()
        self.vac_start.setCalendarPopup(True)
        self.vac_end = QDateEdit()
        self.vac_end.setCalendarPopup(True)
        self.vac_sub_combo = QComboBox()
        # populate with vacation subcategories from CATEGORIES if present:
        vac_subs = []
        if "Vacation" in CATEGORIES.get("Month Expenses", {}):
            subs = CATEGORIES["Month Expenses"]["Vacation"]
            if subs:
                vac_subs = subs
        self.vac_sub_combo.addItems(vac_subs or ["Others"])
        self.vac_ok_btn = QPushButton("OK")
        controls.addWidget(self.vac_start)
        controls.addWidget(self.vac_end)
        controls.addWidget(QLabel("Vac Sub:"))
        controls.addWidget(self.vac_sub_combo)
        controls.addWidget(self.vac_ok_btn)

        # Buttons (Update/Delete/Save)
        controls.addSpacing(12)
        self.update_cell_btn = QPushButton("Update")
        self.delete_cell_btn = QPushButton("Delete")
        self.save_all_btn = QPushButton("Save")
        controls.addWidget(self.update_cell_btn)
        controls.addWidget(self.delete_cell_btn)
        controls.addWidget(self.save_all_btn)

        # pack top row
        top_row.addLayout(controls)
        outer.addLayout(top_row)

        # --- Main area: split horizontal (left daily grid, right month table) ---
        main_h = QHBoxLayout()

        # --- Left: Daily grid table ---
        self.daily_table = QTableWidget()
        self.daily_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.daily_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.daily_table.setSelectionMode(QTableWidget.SingleSelection)
        # we'll set row/column counts in load_month_grid()

        # --- Right: Month expenses small table ---
        self.month_table = QTableWidget()
        self.month_table.setColumnCount(3)
        self.month_table.setHorizontalHeaderLabels(["Category", "Value", "Notes"])
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.month_table.setSelectionMode(QTableWidget.SingleSelection)

        main_h.addWidget(self.daily_table, 3)
        main_h.addWidget(self.month_table, 1)
        outer.addLayout(main_h)

        # --- Bottom status label ---
        self.planner_status_label = QLabel("")
        outer.addWidget(self.planner_status_label)

        # --- Signals ---
        self.year_combo_planner.currentIndexChanged.connect(self.load_month_grid)
        self.month_combo_planner.currentIndexChanged.connect(self.load_month_grid)
        self.vacation_combo.currentTextChanged.connect(self.on_vacation_toggle)
        self.vac_ok_btn.clicked.connect(self.apply_vacation_selection)

        self.update_cell_btn.clicked.connect(self.update_selected_cell)
        self.delete_cell_btn.clicked.connect(self.delete_selected_cell)
        self.save_all_btn.clicked.connect(self.save_planner)

        # initialize
        self.vac_start.hide(); self.vac_end.hide(); self.vac_sub_combo.hide(); self.vac_ok_btn.hide()
        # set defaults to current month/year
        self.year_combo_planner.setCurrentText(str(current_year))
        self.month_combo_planner.setCurrentIndex(date.today().month - 1)

        # build columns from CATEGORIES["Daily Expenses"]
        self._planner_daily_columns = self._build_daily_columns()  # list of (mid, sub)
        # maps for tracking expense ids on grid: (row, col) -> expense_id
        self._planner_daily_id_map = {}
        self._planner_month_id_map = {}  # row -> expense_id

        # Fill month
        self.load_month_grid()

        return widget

    # ---------------- helper methods ----------------

    def _build_daily_columns(self):
        """Return list of (mid, sub) tuples for all Daily Expenses columns."""
        cols = []
        daily = CATEGORIES.get("Daily Expenses", {})
        for mid, subs in daily.items():
            if subs is None:
                cols.append((mid, ""))  # no sub
            else:
                for sub in subs:
                    cols.append((mid, sub))
        return cols

    def load_month_grid(self):
        """Adjust table size for selected month/year, highlight weekends, load DB data."""
        year = int(self.year_combo_planner.currentText())
        month = int(self.month_combo_planner.currentText())
        num_days = calendar.monthrange(year, month)[1]

        # Columns: first column is "Day" label, then one column per (mid,sub)
        cols = self._planner_daily_columns
        col_count = 1 + len(cols)
        row_count = 2 + num_days  # row0 mid headers, row1 sub headers, rows 2.. -> days 1..n

        self.daily_table.clear()
        self.daily_table.setColumnCount(col_count)
        self.daily_table.setRowCount(row_count)
        # set headers for columns (col 0 blank)
        header_labels = ["Day"] + [f"{mid}\n{sub}" if sub else f"{mid}" for mid, sub in cols]
        self.daily_table.setHorizontalHeaderLabels(header_labels)
        self.daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # fill top two rows: mid and sub as visual header rows (non-editable)
        for c, (mid, sub) in enumerate(cols, start=1):
            mid_item = QTableWidgetItem(mid)
            mid_item.setFlags(mid_item.flags() & ~Qt.ItemIsEditable)
            sub_item = QTableWidgetItem(sub or "")
            sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsEditable)
            self.daily_table.setItem(0, c, mid_item)
            self.daily_table.setItem(1, c, sub_item)

        # fill day column and empty editable cells
        year_val, month_val = year, month
        for i in range(num_days):
            day = i + 1
            row = 2 + i
            # Day label in column 0
            day_item = QTableWidgetItem(str(day))
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)
            self.daily_table.setItem(row, 0, day_item)

            # weekdays for coloring
            dt = datetime(year_val, month_val, day)
            is_weekend = dt.weekday() >= 5  # 5=Sat,6=Sun
            for c in range(1, col_count):
                item = QTableWidgetItem("")  # empty cell for value
                # allow editing
                self.daily_table.setItem(row, c, item)
                if is_weekend:
                    item.setBackground(Qt.lightGray)  # light blue-ish substitute (Qt has limited colors)
                # ensure numeric input will be validated on Save

        # clear id map and then load existing DB entries for the month
        self._planner_daily_id_map.clear()
        start = f"{year_val:04d}-{month_val:02d}-01"
        end = f"{year_val:04d}-{month_val:02d}-{num_days:02d}"
        try:
            expenses = reports.get_expenses_by_date_range(start, end)
        except Exception:
            # fallback: use crud.get_expenses(year=..., month=...) if available
            try:
                expenses = crud.get_expenses(year=year_val, month=month_val)
            except Exception:
                expenses = []
        # expenses expected as tuples: (id, main, mid, sub, date, value, notes)
        for exp in expenses:
            try:
                exp_id = exp[0]
                main = exp[1]
                mid = exp[2]
                sub = exp[3]
                date_str = exp[4]
                val = exp[5]
                # only daily expenses here
                if main != "Daily Expenses":
                    continue
                exp_date = datetime.strptime(date_str, "%Y-%m-%d")
                if exp_date.year != year_val or exp_date.month != month_val:
                    continue
                day = exp_date.day
                # find column index for (mid,sub)
                try:
                    col_index = 1 + cols.index((mid, sub if sub else ""))
                except ValueError:
                    # maybe stored with sub empty string vs None
                    try:
                        col_index = 1 + cols.index((mid, sub or ""))
                    except ValueError:
                        continue
                row = 2 + (day - 1)
                # set value string
                self.daily_table.item(row, col_index).setText(str(val))
                self._planner_daily_id_map[(row, col_index)] = exp_id
            except Exception:
                continue

        # load month expenses table on right
        self.load_month_table(year_val, month_val)

    def on_vacation_toggle(self, text):
        if text == "Yes":
            self.vac_start.show(); self.vac_end.show(); self.vac_sub_combo.show(); self.vac_ok_btn.show()
            # default vac dates to current month span
            y = int(self.year_combo_planner.currentText())
            m = int(self.month_combo_planner.currentText())
            self.vac_start.setDate(QDate(y, m, 1))
            self.vac_end.setDate(QDate(y, m, calendar.monthrange(y, m)[1]))
        else:
            self.vac_start.hide(); self.vac_end.hide(); self.vac_sub_combo.hide(); self.vac_ok_btn.hide()
            # remove any vacation highlighting
            self.load_month_grid()

    def apply_vacation_selection(self):
        # read dates and highlight cells in yellow
        start_q = self.vac_start.date()
        end_q = self.vac_end.date()
        start_dt = date(start_q.year(), start_q.month(), start_q.day())
        end_dt = date(end_q.year(), end_q.month(), end_q.day())
        if start_dt > end_dt:
            QMessageBox.warning(self, "Vacation", "Start date must be before end date.")
            return
        # ensure within current month
        y = int(self.year_combo_planner.currentText())
        m = int(self.month_combo_planner.currentText())
        if not (start_dt.year == y and start_dt.month == m and end_dt.year == y and end_dt.month == m):
            QMessageBox.warning(self, "Vacation", "Vacation dates must be inside the selected month.")
            return

        # highlight
        start_day = start_dt.day
        end_day = end_dt.day
        cols = self._planner_daily_columns
        for day in range(start_day, end_day + 1):
            row = 2 + (day - 1)
            for col in range(1, 1 + len(cols)):
                item = self.daily_table.item(row, col)
                if item:
                    item.setBackground(Qt.yellow)

    def load_month_table(self, year, month):
        """Populate the right-side Month Expenses table with categories."""
        self.month_table.clearContents()
        # Build rows from CATEGORIES["Month Expenses"]
        month_cats = CATEGORIES.get("Month Expenses", {})
        rows = []
        for mid, subs in month_cats.items():
            if subs is None:
                rows.append((mid, "", ""))  # category, value, notes
            else:
                # if a mid has multiple subs, create rows for each sub
                for sub in subs:
                    rows.append((f"{mid} > {sub}", "", ""))

        self.month_table.setRowCount(len(rows))
        for r, (cat, val, notes) in enumerate(rows):
            cat_item = QTableWidgetItem(cat)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            val_item = QTableWidgetItem("")  # editable
            notes_item = QTableWidgetItem("")
            self.month_table.setItem(r, 0, cat_item)
            self.month_table.setItem(r, 1, val_item)
            self.month_table.setItem(r, 2, notes_item)

        # load existing month expenses from DB
        num_days = calendar.monthrange(year, month)[1]
        start = f"{year:04d}-{month:02d}-01"
        end = f"{year:04d}-{month:02d}-{num_days:02d}"
        try:
            expenses = reports.get_expenses_by_date_range(start, end)
        except Exception:
            try:
                expenses = crud.get_expenses(year=year, month=month)
            except Exception:
                expenses = []

        # match month entries: main == "Month Expenses" => map by mid/sub
        self._planner_month_id_map.clear()
        for exp in expenses:
            try:
                exp_id = exp[0]; main = exp[1]; mid = exp[2]; sub = exp[3]; date_str = exp[4]; val = exp[5]
                if main != "Month Expenses":
                    continue
                # represent category label like in table: "Mid" or "Mid > Sub"
                if sub:
                    label = f"{mid} > {sub}"
                else:
                    label = mid
                # find row
                for r in range(self.month_table.rowCount()):
                    if self.month_table.item(r, 0).text() == label:
                        self.month_table.item(r, 1).setText(str(val))
                        self._planner_month_id_map[r] = exp_id
                        break
            except Exception:
                continue

    def _parse_value(self, text):
        """Parse value text converting 12,5 to 12.5 and returning float or None."""
        if text is None:
            return None
        s = str(text).strip()
        if s == "":
            return None
        s = s.replace(",", ".")
        try:
            v = float(s)
            return v
        except Exception:
            return None

    def get_selected_cell_coords(self):
        """Return ('daily', row, col) or ('month', row) or None"""
        # check daily table selection
        sel = self.daily_table.selectedIndexes()
        if sel:
            idx = sel[0]
            row = idx.row(); col = idx.column()
            # ensure it's a data cell (row >=2, col >=1)
            if row >= 2 and col >= 1:
                return ('daily', row, col)
        # else month table
        sel2 = self.month_table.selectedIndexes()
        if sel2:
            r = sel2[0].row()
            return ('month', r)
        return None

    def update_selected_cell(self):
        sel = self.get_selected_cell_coords()
        if not sel:
            QMessageBox.information(self, "Update", "Select a daily cell or month row to update.")
            return
        if sel[0] == 'daily':
            _, row, col = sel
            text = self.daily_table.item(row, col).text() if self.daily_table.item(row, col) else ""
            v = self._parse_value(text)
            if v is None:
                QMessageBox.warning(self, "Update", "Enter a valid numeric value before updating.")
                return
            # compute date and category info
            day = int(self.daily_table.item(row, 0).text())
            year = int(self.year_combo_planner.currentText())
            month = int(self.month_combo_planner.currentText())
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            mid, sub = self._planner_daily_columns[col - 1]
            # if existing expense id, update, else add
            exp_id = self._planner_daily_id_map.get((row, col))
            try:
                if exp_id:
                    crud.update_expense(exp_id, "Daily Expenses", mid, sub or None, date_str, v, "")
                else:
                    new_id = crud.add_expense("Daily Expenses", mid, sub or None, date_str, v, "")
                    self._planner_daily_id_map[(row, col)] = new_id
                QMessageBox.information(self, "Updated", "Expense updated successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            _, r = sel
            text = self.month_table.item(r, 1).text() if self.month_table.item(r, 1) else ""
            v = self._parse_value(text)
            if v is None:
                QMessageBox.warning(self, "Update", "Enter a valid numeric value before updating.")
                return
            # date = YYYY-MM-01
            year = int(self.year_combo_planner.currentText())
            month = int(self.month_combo_planner.currentText())
            date_str = f"{year:04d}-{month:02d}-01"
            label = self.month_table.item(r, 0).text()
            # parse label into mid/sub
            if " > " in label:
                mid, sub = label.split(" > ", 1)
            else:
                mid, sub = label, None
            exp_id = self._planner_month_id_map.get(r)
            try:
                if exp_id:
                    crud.update_expense(exp_id, "Month Expenses", mid, sub, date_str, v, "")
                else:
                    new_id = crud.add_expense("Month Expenses", mid, sub, date_str, v, "")
                    self._planner_month_id_map[r] = new_id
                QMessageBox.information(self, "Updated", "Month expense updated.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_selected_cell(self):
        sel = self.get_selected_cell_coords()
        if not sel:
            QMessageBox.information(self, "Delete", "Select a daily cell or month row to delete.")
            return
        if sel[0] == 'daily':
            _, row, col = sel
            exp_id = self._planner_daily_id_map.get((row, col))
            if not exp_id:
                # nothing to delete
                self.daily_table.item(row, col).setText("")
                QMessageBox.information(self, "Delete", "No saved expense for the selected cell. Cell cleared.")
                return
            ok = QMessageBox.question(self, "Delete", "Delete selected expense?")
            if ok != QMessageBox.StandardButton.Yes:
                return
            try:
                crud.delete_expense(exp_id)
                self.daily_table.item(row, col).setText("")
                del self._planner_daily_id_map[(row, col)]
                QMessageBox.information(self, "Deleted", "Expense deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            _, r = sel
            exp_id = self._planner_month_id_map.get(r)
            if not exp_id:
                for c in (1,2):
                    self.month_table.item(r, c).setText("")
                QMessageBox.information(self, "Delete", "No saved month expense. Row cleared.")
                return
            ok = QMessageBox.question(self, "Delete", "Delete selected month expense?")
            if ok != QMessageBox.StandardButton.Yes:
                return
            try:
                crud.delete_expense(exp_id)
                for c in (1,2):
                    self.month_table.item(r, c).setText("")
                del self._planner_month_id_map[r]
                QMessageBox.information(self, "Deleted", "Month expense deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_planner(self):
        """Save all non-empty cells (daily + month) to DB (batch)."""
        year = int(self.year_combo_planner.currentText())
        month = int(self.month_combo_planner.currentText())
        num_days = calendar.monthrange(year, month)[1]
        cols = self._planner_daily_columns

        errors = []
        saved_count = 0

        # Daily cells
        for i in range(num_days):
            row = 2 + i
            day = i + 1
            for c in range(1, 1 + len(cols)):
                item = self.daily_table.item(row, c)
                text = item.text() if item else ""
                v = self._parse_value(text)
                if v is None:
                    continue  # skip empty
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                mid, sub = cols[c - 1]
                exp_id = self._planner_daily_id_map.get((row, c))
                try:
                    if exp_id:
                        crud.update_expense(exp_id, "Daily Expenses", mid, sub or None, date_str, v, "")
                    else:
                        new_id = crud.add_expense("Daily Expenses", mid, sub or None, date_str, v, "")
                        self._planner_daily_id_map[(row, c)] = new_id
                    saved_count += 1
                except Exception as e:
                    errors.append(str(e))

        # Month table
        for r in range(self.month_table.rowCount()):
            label = self.month_table.item(r, 0).text()
            text = self.month_table.item(r, 1).text() if self.month_table.item(r, 1) else ""
            notes = self.month_table.item(r, 2).text() if self.month_table.item(r, 2) else ""
            v = self._parse_value(text)
            if v is None:
                continue
            year = int(self.year_combo_planner.currentText())
            month = int(self.month_combo_planner.currentText())
            date_str = f"{year:04d}-{month:02d}-01"
            if " > " in label:
                mid, sub = label.split(" > ", 1)
            else:
                mid, sub = label, None
            exp_id = self._planner_month_id_map.get(r)
            try:
                if exp_id:
                    crud.update_expense(exp_id, "Month Expenses", mid, sub, date_str, v, notes or "")
                else:
                    new_id = crud.add_expense("Month Expenses", mid, sub, date_str, v, notes or "")
                    self._planner_month_id_map[r] = new_id
                saved_count += 1
            except Exception as e:
                errors.append(str(e))

        if errors:
            QMessageBox.critical(self, "Save errors", "\n".join(errors))
            self.planner_status_label.setText("Errors during save.")
        else:
            QMessageBox.information(self, "Saved", f"✅ All saved ({saved_count} items).")
            self.planner_status_label.setText(f"Saved {saved_count} items.")
        # after save, reload maps to ensure IDs are consistent from DB
        self.load_month_grid()

    # ---------------- end of Monthly Planner code ----------------


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())
