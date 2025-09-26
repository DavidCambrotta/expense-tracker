from datetime import datetime, timedelta

def validate_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
    
    today = datetime.today().date()
    ten_years_ago = today - timedelta(days=365*10)

    if dt > today:
        raise ValueError("Date cannot be in the future.")
    if dt < ten_years_ago:
        raise ValueError("Date cannot be older than 10 years.")
    
    return True

def validate_value(value) -> bool:
    """Check if value is a number >= 0."""
    try:
        val = float(value)
        return val >= 0
    except (ValueError, TypeError):
        return False
