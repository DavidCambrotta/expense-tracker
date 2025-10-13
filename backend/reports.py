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

def get_totals_grouped():
    """Return totals grouped by main and subcategory."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT main_category, sub_category, SUM(value) as total
        FROM expenses
        GROUP BY main_category, sub_category
        ORDER BY main_category, sub_category
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

### for cli.py   
def get_total_by_category(main_cat, mid_cat=None, sub_cat=None):
    """
    Return total expenses for a given category path.
    - main_cat is required
    - mid_cat optional
    - sub_cat optional
    """
    conn = get_connection()
    cur = conn.cursor()

    if mid_cat and sub_cat:
        cur.execute(
            "SELECT SUM(value) FROM expenses WHERE main_category=? AND mid_category=? AND sub_category=?",
            (main_cat, mid_cat, sub_cat),
        )
    elif mid_cat:
        cur.execute(
            "SELECT SUM(value) FROM expenses WHERE main_category=? AND mid_category=?",
            (main_cat, mid_cat),
        )
    else:
        cur.execute(
            "SELECT SUM(value) FROM expenses WHERE main_category=?",
            (main_cat,),
        )

    total = cur.fetchone()[0]
    conn.close()
    return total or 0.0

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
    Returns a list of (YYYY-MM, total_value) for all expenses.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT substr(date, 1, 7) as month, SUM(value)
        FROM expenses
        GROUP BY month
        ORDER BY month DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_totals_grouped(level="main"):
    """
    Returns totals grouped by category level:
    - "main": totals by main_category
    - "mid": totals by main_category + mid_category
    - "sub": totals by full path main+mid+sub
    """
    conn = get_connection()
    cur = conn.cursor()

    if level == "main":
        cur.execute(
            "SELECT main_category, SUM(value) FROM expenses GROUP BY main_category"
        )
    elif level == "mid":
        cur.execute(
            "SELECT main_category, mid_category, SUM(value) FROM expenses "
            "GROUP BY main_category, mid_category"
        )
    elif level == "sub":
        cur.execute(
            "SELECT main_category, mid_category, sub_category, SUM(value) FROM expenses "
            "GROUP BY main_category, mid_category, sub_category"
        )
    else:
        raise ValueError("Invalid grouping level. Use 'main', 'mid', or 'sub'.")

    rows = cur.fetchall()
    conn.close()
    return rows