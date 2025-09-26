from datetime import datetime

def validate_date(date_str: str) -> bool:
    """Check if date is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_value(value):
    """Convert value to float, accept both 12.1 and 12,1 formats."""
    if isinstance(value, str):
        # Replace comma with dot
        value = value.replace(",", ".")
    try:
        val = float(value)
    except ValueError:
        raise ValueError("Invalid value. Must be a number.")
    if val <= 0:
        raise ValueError("Value must be positive.")
    return val
