# backend/validation.py
from typing import Tuple, Optional

CATEGORIES = {
    "Daily Expenses": {
        "Groceries": None,
        "Going Out": ["Food", "Drinks", "Others"],
        "Travel": ["Gasoline", "Transport", "Vacation"],
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

def validate_category(main_cat: str, sub_cat: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Accepts either:
      - a top-level sub-key (e.g. "Groceries", "Going Out")
      - OR an item from any nested lists (e.g. "Drinks", "Gasoline")
    Returns (main_cat, sub_cat) if valid, raises ValueError otherwise.
    """
    if main_cat not in CATEGORIES:
        raise ValueError(f"Invalid main category: {main_cat}")

    subs = CATEGORIES[main_cat]  # dict: subkey -> None | list

    # Build valid sets
    valid_top = set(subs.keys())
    valid_nested = set()
    for k, v in subs.items():
        if v:  # v is a list
            valid_nested.update(v)

    # If no sub_cat provided, accept only if there is at least one sub-option that is top-level and None
    if sub_cat is None:
        # If there are nested options or multiple choices, we generally require an explicit sub_cat.
        # But to be permissive, allow None only if *every* sub-value is None (i.e., no nested lists).
        if any(v for v in subs.values()):  # there is at least one nested list -> require sub_cat
            raise ValueError(f"Please choose a subcategory for '{main_cat}'.")
        return main_cat, None

    # If sub_cat provided, accept if it's either a top-level sub-key or a nested option
    if sub_cat not in valid_top and sub_cat not in valid_nested:
        raise ValueError(f"Invalid subcategory '{sub_cat}' for {main_cat}.")

    return main_cat, sub_cat

