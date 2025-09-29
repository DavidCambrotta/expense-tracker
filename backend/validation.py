CATEGORIES = {
    "Daily Expenses": {
        "Groceries": None,
        "Going Out": ["Food", "Drinks", "Others"],
        "Travel": ["Gasoline", "Train/Bus", "Vacation"],
        "Health": None,
        "Others": ["Cloths", "Sports", "Others"]
    },
    "Monthly Expenses": {
        "Rent": None,
        "Utilities": None,
        "Phone": None,
        "Others": ["Gym", "Netflix"]
    }
}

def validate_category(main_cat: str, sub_cat: str | None = None) -> str:
    """Ensure category and optional subcategory are valid."""
    if main_cat not in CATEGORIES:
        raise ValueError(f"Invalid main category: {main_cat}")

    subs = CATEGORIES[main_cat]

    if sub_cat is None:
        # Accept only if no subcategories exist
        if subs is not None and any(v is not None for v in subs.values()):
            raise ValueError(f"{main_cat} requires a subcategory.")
        return main_cat

    if sub_cat not in subs and subs is not None:
        raise ValueError(f"Invalid subcategory '{sub_cat}' for {main_cat}.")

    return f"{main_cat} > {sub_cat}" if sub_cat else main_cat