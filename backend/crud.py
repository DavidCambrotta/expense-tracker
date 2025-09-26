from .database import get_connection
from .validators import validate_date, validate_value

def add_expense(category, date, value, notes=""):
    if not validate_date(date):
        raise ValueError("❌ Invalid date format. Use YYYY-MM-DD.")
    if not validate_value(value):
        raise ValueError("❌ Value must be a number >= 0.")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (category, date, value, notes) VALUES (?, ?, ?, ?)",
        (category, date, value, notes)
    )
    exp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return exp_id

def get_expenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_expense(expense_id, category, date, value, notes=""):
    if not validate_date(date):
        raise ValueError("❌ Invalid date format. Use YYYY-MM-DD.")
    if not validate_value(value):
        raise ValueError("❌ Value must be a number >= 0.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET category=?, date=?, value=?, notes=? WHERE id=?",
        (category, date, float(value), notes, expense_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise LookupError(f"❌ No expense found with ID {expense_id}")
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise LookupError(f"❌ No expense found with ID {expense_id}")
    conn.commit()
    conn.close()
