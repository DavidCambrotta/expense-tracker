import pytest
from backend import database

@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    """Reset DB before each test using a temporary SQLite file."""
    test_db = tmp_path / "test_expenses.db"
    monkeypatch.setattr(database, "DB_NAME", str(test_db))
    database.init_db()
    yield
