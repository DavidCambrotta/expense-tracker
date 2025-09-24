from datetime import datetime

def validate_date(date_str: str) -> bool:
    """Check if date is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_value(value) -> bool:
    """Check if value is a number >= 0."""
    try:
        val = float(value)
        return val >= 0
    except (ValueError, TypeError):
        return False
