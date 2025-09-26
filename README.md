# Expense Tracker

A simple **Python CLI application** to track daily expenses.  
Supports adding, listing, updating, deleting expenses, and generating reports (totals & monthly summary).  
Runs on **SQLite** database (created automatically on first run).  

---

## Features
- Add daily expenses with category, date, value, description
- List all expenses in a nice table
- Update or delete existing expenses
- Reports:
  - Total by category
  - Total by date range
  - Monthly summary
- Runs on Windows, packaged into a standalone `.exe`

---

## Installation (Development)

Clone the repo and install dependencies:

```bash
git clone https://github.com/yourname/expense-tracker.git
cd expense-tracker
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt