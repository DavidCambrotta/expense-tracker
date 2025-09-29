CATEGORIES = {
    "Daily Expenses": {
        "Groceries": None,
        "Going Out": ["Food", "Drinks", "Others"],
        "Travel": ["Gasoline", "Train/Bus", "Vacation"],
        "Health": None,
        "Others": ["Cloths", "Sports", "Others"]
    },
    "Month Expenses": {
        "Rent": None,
        "Utilities": None,
        "Phone": None,
        "Others": ["Gym", "Netflix"]
    }
}

def validate_category(main_cat: str, sub_cat: str | None = None):
    """Validate category and subcategory selection."""
    if main_cat not in CATEGORIES:
        raise ValueError(f"Invalid main category: {main_cat}")

    subs = CATEGORIES[main_cat]

    if sub_cat:
        if subs is None or (sub_cat not in subs and sub_cat not in (subs or [])):
            raise ValueError(f"Invalid subcategory '{sub_cat}' for {main_cat}.")
    else:
        # If a subcategory is required, raise error
        if subs and any(v for v in subs.values()):
            raise ValueError(f"{main_cat} requires a subcategory.")

    return main_cat, sub_cat
