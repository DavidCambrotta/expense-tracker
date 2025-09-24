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