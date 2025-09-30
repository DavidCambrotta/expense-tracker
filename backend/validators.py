# backend/validators.py
from datetime import datetime, timedelta
from typing import Any

def validate_date(date_str: str) -> bool:
    """
    Accept YYYY-MM-DD (also accept YYYY/MM/DD by normalizing). Also enforce:
      - date <= today
      - date >= today - 10 years
    Raises ValueError on invalid input.
    """
    if not isinstance(date_str, str):
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    # allow slashes by replacing them
    date_normalized = date_str.replace("/", "-")
    try:
        dt = datetime.strptime(date_normalized, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    today = datetime.today().date()
    ten_years_ago = today - timedelta(days=365 * 10)

    if dt > today:
        raise ValueError("Date cannot be in the future.")
    if dt < ten_years_ago:
        raise ValueError("Date cannot be older than 10 years.")

    return True


def validate_value(value: Any) -> float:
    """Accept both '12.1' and '12,1' (and numeric types). Returns float if valid, else raises."""
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        val = float(value)
    except (ValueError, TypeError):
        raise ValueError("Invalid value. Must be a number.")
    if val <= 0:
        raise ValueError("Value must be positive.")
    return val
