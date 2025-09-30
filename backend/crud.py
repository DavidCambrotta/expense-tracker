from .database import get_connection
from .validators import validate_date, validate_value
from .validation import validate_category

def add_expense(main_cat, sub_cat, date, value, notes=None):
    #if not validate_date(date):
    #    raise ValueError("❌ Invalid date format. Use YYYY-MM-DD.")
    #if not validate_value(value):
    #    raise ValueError("❌ Value must be a number >= 0.")
    
    main_cat, sub_cat = validate_category(main_cat, sub_cat)
    validate_date(date)
    value = validate_value(value)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (main_category, sub_category, date, value, notes) VALUES (?, ?, ?, ?, ?)",
        (main_cat, sub_cat, date, value, notes)
    )
    exp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return exp_id

def get_expenses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, main_category, sub_category, date, value, notes FROM expenses")
    rows = cur.fetchall()
    conn.close()
    # convert value to float
    return [(r[0], r[1], r[2], r[3], float(r[4]), r[5]) for r in rows]

def update_expense(expense_id, category, date, value, notes=""):
    #if not validate_date(date):
    #    raise ValueError("❌ Invalid date format. Use YYYY-MM-DD.")
    #if not validate_value(value):
    #    raise ValueError("❌ Value must be a number >= 0.")

    main_cat, sub_cat = validate_category(main_cat, sub_cat)
    validate_date(date)
    value = validate_value(value)
    conn = get_connection()
    cursor = conn.cursor()
    cur.execute("""
        UPDATE expenses
        SET main_category = ?, sub_category = ?, date = ?, value = ?, notes = ?
        WHERE id = ?
    """, (main_cat, sub_cat, date, value, notes, expense_id))

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
