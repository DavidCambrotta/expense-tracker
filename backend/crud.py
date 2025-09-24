from .database import get_connection

def add_expense(category, date, value, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (category, date, value, notes) VALUES (?, ?, ?, ?)",
        (category, date, value, notes)
    )
    conn.commit()
    conn.close()

def get_expenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_expense(expense_id, category, date, value, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET category=?, date=?, value=?, notes=? WHERE id=?",
        (category, date, value, notes, expense_id)
    )
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()
