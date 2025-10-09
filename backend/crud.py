from .database import get_connection
from .validation import validate_category, CATEGORIES
from .validators import validate_date, validate_value

def add_expense(main_cat, mid_cat, sub_cat, date, value, notes=""):
    # Validate category/subcategory first (will raise if invalid)
    main_cat, mid_cat, sub_cat = validate_category(main_cat, mid_cat, sub_cat)

    # Validate date & value
    validate_date(date)
    value = validate_value(value)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (main_category, mid_category, sub_category, date, value, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (main_cat, mid_cat, sub_cat, date, value, notes)
    )
    exp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return exp_id

def update_expense(expense_id, main_cat, mid_cat, sub_cat, date, value, notes=""):
    main_cat, mid_cat, sub_cat = validate_category(main_cat, mid_cat, sub_cat)
    validate_date(date)
    value = validate_value(value)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE expenses
        SET main_category = ?, mid_category = ?, sub_category = ?, date = ?, value = ?, notes = ?
        WHERE id = ?
    """, (main_cat, mid_cat, sub_cat, date, value, notes, expense_id))

    if cur.rowcount == 0:
        conn.close()
        raise LookupError(f"❌ No expense found with ID {expense_id}")
    conn.commit()
    conn.close()

def get_expenses(year: int = None, month: int = None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT id, main_category, mid_category, sub_category, date, value, notes
        FROM expenses
    """
    params = []

    if year and month:
        query += " WHERE strftime('%Y', date)=? AND strftime('%m', date)=?"
        params.extend([str(year), f"{month:02d}"])
    elif year:
        query += " WHERE strftime('%Y', date)=?"
        params.append(str(year))

    query += " ORDER BY date ASC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return [(r[0], r[1], r[2], r[3], r[4], float(r[5]), r[6]) for r in rows]

def get_available_years():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT strftime('%Y', date) FROM expenses ORDER BY 1 ASC")
    years = [int(r[0]) for r in cur.fetchall() if r[0]]
    conn.close()
    return years

def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise LookupError(f"❌ No expense found with ID {expense_id}")
    conn.commit()
    conn.close()
