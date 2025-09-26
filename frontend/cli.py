import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import crud, reports
from tabulate import tabulate
from colorama import Fore, Style, init

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

def handle_add():
    category = input("Category: ")
    date = input("Date (YYYY-MM-DD): ")
    value = input("Value: ")
    description = input("Description (optional): ")
    try:
        crud.add_expense(category, date, value, description)
        print(Fore.GREEN + "✅ Expense added successfully.")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

def handle_list():
    expenses = crud.get_expenses()
    if not expenses:
        print("No expenses found.")
        return
    #print("\n--- Expenses ---")
    #for exp in expenses:
    #    print(f"[{exp[0]}] {exp[1]} | {exp[2]} | ${exp[3]:.2f} | {exp[4]}")

    headers = ["ID", "Category", "Date", "Value", "Description"]
    table = [[exp[0], exp[1], exp[2], f"${exp[3]:.2f}", exp[4]] for exp in expenses]
    print("\n--- Expenses ---")
    print(tabulate(table, headers, tablefmt="grid"))

def handle_update():
    try:
        expense_id = int(input("Expense ID to update: "))
        category = input("New category: ")
        date = input("New date (YYYY-MM-DD): ")
        value = input("New value: ")
        description = input("New description (optional): ")
        crud.update_expense(expense_id, category, date, value, description)
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
