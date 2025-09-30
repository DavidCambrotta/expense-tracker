import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import crud, reports
from tabulate import tabulate
from colorama import Fore, Style, init
from backend.validation import CATEGORIES, validate_category

init(autoreset=True)

def print_menu():
    print(Fore.MAGENTA + "\n=== Expense Tracker ===")
    print(Fore.CYAN + "1. Add expense")
    print("2. List expenses")
    print("3. Update expense")
    print("4. Delete expense")
    print("5. Reports")
    print(Fore.RED + "0. Exit")

def print_reports_menu():
    print("\n--- Reports ---")
    print("1. Total by category")
    print("2. Total by date range")
    print("3. Monthly summary")
    print("0. Back")

def pick_main_and_sub():
    # choose main category
    main_keys = list(CATEGORIES.keys())
    while True:
        print("Choose main category:")
        for i, key in enumerate(main_keys, start=1):
            print(f"{i}. {key}")
        try:
            main_choice = int(input("Select number: ").strip())
            if not (1 <= main_choice <= len(main_keys)):
                raise ValueError()
        except ValueError:
            print(Fore.RED + "Invalid selection. Please enter a valid number.")
            continue
        main_cat = main_keys[main_choice - 1]
        break

    # build flattened option list while preserving choices
    subs = CATEGORIES[main_cat]  # dict
    options = []
    for subkey, subval in subs.items():
        if subval is None:
            # top-level single option (e.g., "Groceries", "Health")
            options.append(subkey)
        else:
            # flatten nested list (e.g., "Food", "Drinks", ...)
            options.extend(subval)

    sub_cat = None
    if options:
        while True:
            print(f"Choose subcategory for {main_cat}:")
            for i, opt in enumerate(options, start=1):
                print(f"{i}. {opt}")
            try:
                choice = int(input("Select number: ").strip())
                if not (1 <= choice <= len(options)):
                    raise ValueError()
            except ValueError:
                print(Fore.RED + "Invalid selection. Please enter a valid number.")
                continue
            sub_cat = options[choice - 1]
            break

    return main_cat, sub_cat

def handle_add():
    try:
        main_cat, sub_cat = pick_main_and_sub()

        date = input("Date (YYYY-MM-DD): ").strip()
        # do not normalize date here; backend will validate (but you may strip slashes)
        value_input = input("Value: ").strip().replace(",", ".")
        notes = input("Notes (optional): ").strip()

        exp_id = crud.add_expense(main_cat, sub_cat, date, value_input, notes)
        print(Fore.GREEN + f"✅ Expense added successfully (ID {exp_id}).")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

def handle_list():
    expenses = crud.get_expenses()
    if not expenses:
        print("⚠️ No expenses found.")
        return

    print("\n=== Expense List ===")
    for exp in expenses:
        exp_id, main_cat, sub_cat, date, value, notes = exp
        category_display = f"{main_cat}" + (f" > {sub_cat}" if sub_cat else "")
        #print(f"[{exp_id}] {category_display} | {date} | ${value} | {notes}") # -> debug
        value_float = float(value)  # 👈 convert here
        print(f"[{exp_id}] {category_display} | {date} | ${value_float:.2f} | {notes}")

    headers = ["ID", "Category","Sub Category", "Date", "Value", "Notes"]
    table = [[exp[0], exp[1], exp[2], exp[3], f"${exp[4]:.2f}", exp[5]] for exp in expenses]
    print("\n--- Expenses ---")
    print(tabulate(table, headers, tablefmt="grid"))

def handle_update():
    try:
        expense_id = int(input("Expense ID to update: "))
        category = input("New category: ")
        date = input("New date (YYYY-MM-DD): ")
        value = input("New value: ")
        notes = input("New notes (optional): ")
        crud.update_expense(expense_id, category, date, value, notes)
        print(Fore.GREEN + "✅ Expense updated successfully.")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

def handle_delete():
    try:
        expense_id = int(input("Expense ID to delete: "))
        crud.delete_expense(expense_id)
        print(Fore.GREEN + "✅ Expense deleted successfully.")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

def handle_reports():
    while True:
        print_reports_menu()
        choice = input("Choose report: ")
        if choice == "1":
            category = input("Category: ")
            try:
                total = reports.get_total_by_category(category)
                #print(f"Total for {category}: ${total:.2f}")

                #format them with tabulate if desired
                print(tabulate([[category, f"${total:.2f}"]], headers=["Category", "Total"], tablefmt="grid"))


            except Exception as e:
                print(Fore.RED + f"❌ Error: {e}")
        elif choice == "2":
            start = input("Start date (YYYY-MM-DD): ")
            end = input("End date (YYYY-MM-DD): ")
            try:
                total = reports.get_total_by_date_range(start, end)
                print(Fore.YELLOW + f"Total from {start} to {end}: ${total:.2f}")
            except Exception as e:
                print(Fore.RED + f"❌ Error: {e}")
        elif choice == "3":
            summary = reports.get_monthly_summary()
            if not summary:
                print("No data available.")
            else:
                #print("\n--- Monthly Summary ---")
                #for month, total in summary:
                #    print(f"{month}: ${total:.2f}")
                headers = ["Month", "Total"]
                table = [[month, f"${total:.2f}"] for month, total in summary]
                print("\n--- Monthly Summary ---")
                print(tabulate(table, headers, tablefmt="grid"))
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def menu():
    while True:
        print_menu()
        choice = input("Choose an option: ")
        if choice == "1":
            handle_add()
        elif choice == "2":
            handle_list()
        elif choice == "3":
            handle_update()
        elif choice == "4":
            handle_delete()
        elif choice == "5":
            handle_reports()
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
