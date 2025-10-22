# backend/validation.py
from typing import Tuple, Optional

CATEGORIES = {
    "Daily Expenses": {
        "Groceries": ["Food", "Others"],
        "Going Out": ["Restaurant", "Night Out", "Others"],
        "Transportation": ["Gasoline", "Trans/Bus", "Uber", "Vacation"],
        "Others": ["Health", "Cloths", "Sports", "Others"]
    },
    "Month Expenses": {
        "Rent": None,
        "Utilities": None,
        "Subscriptions": ["Phone", "Gym", "Cloud", "Cloud"]
    }
}

def validate_category(main_cat: str, mid_cat: Optional[str], sub_cat: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Validates a category path (main -> mid -> sub).
    - main_cat must exist in CATEGORIES.
    - mid_cat must exist under main_cat.
    - sub_cat must be provided only if mid_cat has a list of subcategories.
    """
    if main_cat not in CATEGORIES:
        raise ValueError(f"Invalid main category: {main_cat}")

    mids = CATEGORIES[main_cat]  # dict: subkey -> None | list

    # --- Validate mid_cat ---
    if mid_cat is None:
        raise ValueError(f"Please choose a mid category for '{main_cat}'.")
    if mid_cat not in mids:
        raise ValueError(f"Invalid mid category '{mid_cat}' for {main_cat}.")

    subs = mids[mid_cat]  # list of subcategories (or empty list)
    
    # Build valid sets
    #valid_top = set(subs.keys())
    #valid_nested = set()
    #for k, v in subs.items():
    #    if v:  # v is a list
    #        valid_nested.update(v)

    # If no sub_cat provided, accept only if there is at least one sub-option that is top-level and None
    #if sub_cat is None:
        # If there are nested options or multiple choices, we generally require an explicit sub_cat.
        # But to be permissive, allow None only if *every* sub-value is None (i.e., no nested lists).
    #    if any(v for v in subs.values()):  # there is at least one nested list -> require sub_cat
    #        raise ValueError(f"Please choose a subcategory for '{main_cat}'.")
    #    return main_cat, None

    # If sub_cat provided, accept if it's either a top-level sub-key or a nested option
    #if sub_cat not in valid_top and sub_cat not in valid_nested:
    #    raise ValueError(f"Invalid subcategory '{sub_cat}' for {main_cat}.")
    #
    #return main_cat, sub_cat

    # --- Validate sub_cat ---
    if subs is None:
        # mid_cat has no subcategories
        if sub_cat is not None:
            raise ValueError(f"'{main_cat} > {mid_cat}' does not accept a subcategory.")
        sub_cat = None
    else:
        # mid_cat has subcategories
        if sub_cat is None:
            raise ValueError(f"Please choose a subcategory for '{main_cat} > {mid_cat}'.")
        if sub_cat not in subs:
            raise ValueError(f"Invalid subcategory '{sub_cat}' for {main_cat} > {mid_cat}.")

    return main_cat, mid_cat, sub_cat