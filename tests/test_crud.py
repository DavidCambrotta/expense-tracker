import pytest
import sys, os
from backend import models, crud, reports

#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_DB = "test_expenses.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Override DB name for testing
    monkeypatch.setattr("backend.database.DB_NAME", TEST_DB)
    
    # Initialize clean DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    models.init_db()
    
    yield  # run the test
    
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_and_get_expense():
    crud.add_expense("Food", "2025-09-23", 12.50, "Lunch")
    expenses = crud.get_expenses()
    assert len(expenses) == 1
    assert expenses[0][1] == "Food"
    assert expenses[0][2] == "2025-09-23"
    assert expenses[0][3] == 12.50
    assert expenses[0][4] == "Lunch"

def test_update_expense():
    crud.add_expense("Food", "2025-09-23", 10, "Snack")
    expenses = crud.get_expenses()
    expense_id = expenses[0][0]

    crud.update_expense(expense_id, "Transport", "2025-09-24", 5.75, "Bus fare")
    updated = crud.get_expenses()[0]
    assert updated[1] == "Transport"
    assert updated[2] == "2025-09-24"
    assert updated[3] == 5.75
    assert updated[4] == "Bus fare"

def test_delete_expense():
    crud.add_expense("Misc", "2025-09-23", 7.0, "Coffee")
    expenses = crud.get_expenses()
    expense_id = expenses[0][0]

    crud.delete_expense(expense_id)
    assert crud.get_expenses() == []

def test_reports_totals():
    crud.add_expense("Food", "2025-09-01", 20, "")
    crud.add_expense("Food", "2025-09-15", 30, "")
    crud.add_expense("Transport", "2025-09-20", 10, "")

    assert reports.get_total_by_category("Food") == 50
    assert reports.get_total_by_date_range("2025-09-01", "2025-09-30") == 60

def test_monthly_summary():
    crud.add_expense("Food", "2025-09-01", 20, "")
    crud.add_expense("Food", "2025-09-15", 30, "")
    crud.add_expense("Transport", "2025-10-05", 15, "")

    summary = reports.get_monthly_summary()
    assert ("2025-09", 50.0) in summary
    assert ("2025-10", 15.0) in summary

def test_invalid_date():
    with pytest.raises(ValueError):
        crud.add_expense("Food", "09-23-2025", 10, "")

def test_invalid_value():
    with pytest.raises(ValueError):
        crud.add_expense("Food", "2025-09-23", -5, "")

def test_delete_nonexistent():
    with pytest.raises(LookupError):
        crud.delete_expense(999)

def test_update_nonexistent():
    with pytest.raises(LookupError):
        crud.update_expense(999, "Test", "2025-09-23", 5, "")
