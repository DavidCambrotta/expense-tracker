from backend import crud

def menu():
    while True:
        print("\n--- Expense Tracker ---")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Exit")

        choice = input("Choose an option: ")
        
        if choice == "1":
            category = input("Category: ")
            date = input("Date (YYYY-MM-DD): ")
            value = float(input("Value: "))
            notes = input("Notes (optional): ")
            crud.add_expense(category, date, value, notes)
            print("✅ Expense added!")
        
        elif choice == "2":
            expenses = crud.get_expenses()
            for e in expenses:
                print(e)
        
        elif choice == "3":
            break
        else:
            print("Invalid choice.")
