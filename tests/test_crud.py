import pytest
from datetime import datetime, timedelta
from backend import crud, reports

# Helpers
TODAY = datetime.today().date()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
LAST_MONTH = (TODAY.replace(day=1) - timedelta(days=1))
LAST_MONTH_STR = LAST_MONTH.strftime("%Y-%m-%d")


def test_add_and_get_expense():
    exp_id = crud.add_expense("Daily Expenses", "Groceries", None , TODAY_STR, 12.5, "Test")
    assert exp_id is not None
    expenses = crud.get_expenses()
    assert any(exp[0] == exp_id for exp in expenses)


def test_update_expense():
    exp_id = crud.add_expense("Daily Expenses", "Travel", "Transport", TODAY_STR, 5.0, "Bus")
    crud.update_expense(exp_id,"Daily Expenses", "Travel", "Transport", TODAY_STR, 7.0, "Bus updated")
    expenses = crud.get_expenses()
    updated = [exp for exp in expenses if exp[0] == exp_id][0]
    assert updated[4] == 7.0


def test_delete_expense():
    exp_id = crud.add_expense("Daily Expenses", "Others", "Others", TODAY_STR, 2.0, "Pen")
    crud.delete_expense(exp_id)
    expenses = crud.get_expenses()
    assert all(exp[0] != exp_id for exp in expenses)


def test_reports_totals():
    crud.add_expense("Daily Expenses", "Going Out", "Food", TODAY_STR, 10, "")
    crud.add_expense("Daily Expenses", "Going Out", "Food", TODAY_STR, 20, "")
    crud.add_expense("Daily Expenses", "Travel", "Transport", TODAY_STR, 5, "")

    food_total = reports.get_total_by_category("Daily Expenses", "Going Out","Food")
    transport_total = reports.get_total_by_category("Daily Expenses", "Travel", "Transport")

    assert food_total == 30
    assert transport_total == 5


def test_monthly_summary():
    this_month_date1 = TODAY.replace(day=1).strftime("%Y-%m-%d")
    this_month_date2 = TODAY_STR
    last_month_date = LAST_MONTH_STR

    crud.add_expense("Daily Expenses", "Going Out", "Food", this_month_date1, 20, "")
    crud.add_expense("Daily Expenses", "Going Out", "Food", this_month_date2, 30, "")
    crud.add_expense("Daily Expenses", "Travel", "Transport", last_month_date, 15, "")

    summary = reports.get_monthly_summary()

    # Instead of strict tuple matching, check the values
    this_month = this_month_date1[:7]
    last_month = last_month_date[:7]

    dict_summary = dict(summary)
    assert dict_summary[this_month] >= 50.0
    assert dict_summary[last_month] >= 15.0

def test_invalid_value():
    with pytest.raises(ValueError, match="(?i)(value|amount|positive)"):
        crud.add_expense("Daily Expenses", "Going Out", "Food", TODAY_STR, -5, "Bad value")

def test_delete_nonexistent():
    with pytest.raises(LookupError, match="No expense"):
        crud.delete_expense(999999)


def test_update_nonexistent():
    with pytest.raises(LookupError, match="No expense"):
        crud.update_expense(999999, "Daily Expenses", "Going Out", "Food", TODAY_STR, 10, "Test")


def test_future_date_invalid():
    future_date = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError, match="future"):
        crud.add_expense("Daily Expenses", "Going Out", "Food", future_date, 10, "")


def test_too_old_date_invalid():
    old_date = (TODAY - timedelta(days=365*11)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError, match="older than 10 years"):
        crud.add_expense("Daily Expenses", "Going Out", "Food", old_date, 10, "")
