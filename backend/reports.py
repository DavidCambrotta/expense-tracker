from .database import get_connection

def get_total_by_category(category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(value) FROM expenses WHERE category=?", (category,))
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0

def get_total_by_date_range(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(value) FROM expenses WHERE date BETWEEN ? AND ?",
        (start_date, end_date)
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0
