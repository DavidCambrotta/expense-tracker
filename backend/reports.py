from .database import get_connection
from backend.database import get_connection

def list_all_categories():
    """Return all distinct category pairs from expenses."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT main_category, sub_category FROM expenses")
    categories = cur.fetchall()
    conn.close()
    return categories

def get_total_by_category(main_category, sub_category=None):
    """Return total spent for a given main + optional sub category."""
    conn = get_connection()
    cur = conn.cursor()
    if sub_category:
        cur.execute("""
            SELECT SUM(value) 
            FROM expenses 
            WHERE main_category=? AND sub_category=?
        """, (main_category, sub_category))
    else:
        cur.execute("""
            SELECT SUM(value) 
            FROM expenses 
            WHERE main_category=?
        """, (main_category,))
    total = cur.fetchone()[0]
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