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

def get_monthly_summary():
    """
    Returns a list of tuples (month, total) where:
    - month is in YYYY-MM format
    - total is the sum of all expenses for that month
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT substr(date, 1, 7) as month, SUM(value)
        FROM expenses
        GROUP BY month
        ORDER BY month
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows