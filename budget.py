"""Command-line interface. Run this file to start the calculator."""
from datetime import date as Date, timedelta
from decimal import Decimal

from tabulate import tabulate

import analysis
import forecast
import storage
from validation import parse_amount, parse_month


class Getter:
    def get_date(self):
        while True:
            value = input("Date (YYYY-MM-DD): ").strip()
            if value.lower() == "exit":
                return "exit"
            try:
                # The round trip also enforces the exact YYYY-MM-DD format.
                parsed = Date.fromisoformat(value)
                if parsed.isoformat() == value:
                    return value
            except ValueError:
                pass
            print("Please enter a valid date in YYYY-MM-DD format.")

    def get_category(self):
        categories = {
            "1": "Groceries",
            "2": "Dining & Restaurants",
            "3": "Gas & Automotive",
            "4": "Travel",
            "5": "Transportation & Transit",
            "6": "Entertainment",
            "7": "Recurring Bills & Utilities",
            "8": "Shopping & Retail",
            "9": "Health & Wellness",
            "10": "Other / Miscellaneous",
            "0" : "Description of Options"
        }

        print("Available Categories:")
        for number, category in categories.items():
            print(f"{number}. {category}")

        while True:
            choice = input("Please select a category number: ").strip()
            if choice.lower() == 'exit':
                return 'exit' 
            if choice == '0':
                print(""" 
            • Groceries: Supermarkets, local food markets, and specialty food stores.
            • Dining & Restaurants: Fast food, bars, cafes, and sit-down restaurants.
            • Gas & Automotive: Fuel stations, automated car washes, and auto repair shops.
            • Travel: Airlines, hotels, cruise lines, car rentals, and travel agencies.
            • Transportation & Transit: Rideshares (Uber/Lyft), public transit, taxis, and parking lots.
            • Entertainment: Movie theatres, concerts, sporting events, and theme parks.
            • Recurring Bills & Utilities: Phone, internet, streaming services (Netflix/Spotify), and insurance.
            • Shopping & Retail: Clothing, electronics, department stores, and online retail (Amazon).
            • Health & Wellness: Pharmacies, dentists, gyms, and medical services.
            • Other / Miscellaneous: Cash advances, annual fees, and unclassified merchants.
            """)
                continue
            elif choice in categories:
                print(categories[choice])
                return categories[choice]

            print("Invalid category. Please try again.")

    def get_description(self):
        while True:
            description = input("Please enter a description (1–20 characters):\n").strip()
            if description.lower() == 'exit':
                return 'exit' 
            if 1 <= len(description) <= 20:
                return description
            print("Please use between 1 and 20 characters.")

    def get_amount(self):
        while True:
            text = input("Please enter the amount: ").strip()
            if text.lower() == "exit":
                return "exit"
            try:
                return parse_amount(text)
            except ValueError as exc:
                print(exc)


def main():
    try:
        storage.migrate_legacy_data()
    except (OSError, ValueError, storage.DatabaseError) as exc:
        print(f"Could not initialize the database: {exc}")
        return
    print("Welcome to the Budget Calculator")
    while True:
        action = get_action()
        if action == 4:
            print("Thank you for using Budget Calculator.")
            return
        try:
            if action == 1:
                get_expense()
            elif action == 2:
                total = analysis.calculate_total(storage.load_expenses())
                print(f"${total:.2f}")
            elif action == 3:
                expenses = storage.load_expenses()
                # Format a copy so display strings never replace numeric amounts.
                rows = [{**expense, "amount": f"${expense['amount']:.2f}"}
                        for expense in expenses]
                print(tabulate(rows, headers="keys", tablefmt="grid")
                      if expenses else "No expenses recorded yet.")
            elif action == 5:
                print_category_summary(storage.load_expenses())
            elif action == 6:
                totals = analysis.summarize_by_month(storage.load_expenses())
                rows = [{"Month": month, "Spent": f"${amount:.2f}"}
                        for month, amount in totals.items()]
                print(tabulate(rows, headers="keys", tablefmt="grid")
                      if rows else "No expenses recorded yet.")
            elif action == 7:
                set_monthly_budget()
            elif action == 8:
                show_monthly_budget()
            elif action == 9:
                edit_expense()
            elif action == 10:
                remove_expense()
            elif action == 11:
                show_forecast()
            elif action == 12:
                show_forecast_backtest()
        except (OSError, ValueError, storage.DatabaseError) as exc:
            print(f"Could not process expenses: {exc}")


def get_action():
    while True:
        try:
            action = int(input(
                "Please select an option:\n"
                "1. Insert an expense\n2. Calculate total expenses\n"
                "3. View expenses\n4. Quit\n"
                "5. Spending by category\n6. Monthly spending summaries\n"
                "7. Set monthly budget\n8. View monthly budget status\n"
                "9. Edit an expense\n10. Delete an expense\n"
                "11. Forecast month-end spending\n12. Backtest the baseline\n"
            ))
            if 1 <= action <= 12:
                return action
        except ValueError:
            pass
        print("Please enter a number from 1 to 12.")


def get_expense(path=None):
    print('Type "EXIT" at any time to exit the expense section.')
    get = Getter()
    while True:
        date = get.get_date()
        if date.lower() == 'exit':
            print('\n')
            break

        category = get.get_category()
        if category.lower() == 'exit':
            break

        description = get.get_description()
        if description.lower() == 'exit':
            break

        amount = get.get_amount()
        if amount == 'exit':
            break

        storage.save_expense({"date": date, "category": category,
                      "description": description, "amount": amount}, path)
        print('The expense is recorded.\n')
    print('The procedure is completed.\n')


def get_month():
    while True:
        value = input("Month (YYYY-MM, or EXIT to cancel): ").strip()
        if value.lower() == "exit":
            return None
        try:
            return parse_month(value)
        except ValueError as exc:
            print(exc)


def print_category_summary(expenses):
    totals = analysis.summarize_by_category(expenses)
    percentages = analysis.category_percentages(totals)
    rows = [{"Category": category, "Spent": f"${amount:.2f}",
             "Share": f"{percentages[category]:.1f}%"}
            for category, amount in sorted(totals.items(),
                                           key=lambda item: (-item[1], item[0]))]
    print(tabulate(rows, headers="keys", tablefmt="grid")
          if rows else "No expenses recorded yet.")


def set_monthly_budget():
    month = get_month()
    if month is None:
        return
    print(f"Set the total spending limit for {month} (positive amount).")
    amount = Getter().get_amount()
    if amount == "exit":
        return
    storage.save_monthly_budget(month, amount)
    print(f"Budget saved for {month}: ${amount:.2f}")


def show_monthly_budget():
    month = get_month()
    if month is None:
        return
    expenses = storage.load_expenses()
    budgets = storage.load_budgets()
    print(f"Spending for {month}")
    if month in budgets:
        status = analysis.calculate_budget_status(expenses, month, budgets[month])
        print(f"Budget: ${status['budget']:.2f}")
        print(f"Spent: ${status['spent']:.2f}")
        if status["remaining"] < 0:
            print(f"Over budget by: ${-status['remaining']:.2f}")
        elif status["remaining"] == 0:
            print("Budget fully used. Remaining: $0.00")
        else:
            print(f"Remaining: ${status['remaining']:.2f}")
        print(f"Budget used: {status['percentage_used']:.1f}%")
    else:
        spent = analysis.calculate_total(analysis.expenses_for_month(expenses, month))
        print(f"Spent: ${spent:.2f}")
        print("No budget set for this month. Choose option 7 to set one.")
    print_category_summary(analysis.expenses_for_month(expenses, month))


def select_expense():
    expenses = storage.load_expenses()
    if not expenses:
        print("No expenses recorded yet.")
        return None
    rows = [{**expense, "amount": f"${expense['amount']:.2f}"} for expense in expenses]
    print(tabulate(rows, headers="keys", tablefmt="grid"))
    while True:
        value = input("Expense ID (or EXIT to cancel): ").strip()
        if value.lower() == "exit":
            return None
        try:
            expense_id = int(value)
        except ValueError:
            print("Please enter an expense ID.")
            continue
        for expense in expenses:
            if expense["id"] == expense_id:
                return expense
        print("No expense has that ID. Please try again.")


def edit_expense():
    expense = select_expense()
    if expense is None:
        return
    print("Enter the replacement fields. Type EXIT at any prompt to cancel.")
    getter = Getter()
    replacement = {}
    for field, prompt in [("date", getter.get_date), ("category", getter.get_category),
                          ("description", getter.get_description), ("amount", getter.get_amount)]:
        value = prompt()
        if value == "exit":
            print("Edit cancelled.")
            return
        replacement[field] = value
    if storage.update_expense(expense["id"], replacement):
        print("Expense updated.")
    else:
        print("Expense no longer exists.")


def remove_expense():
    expense = select_expense()
    if expense is None:
        return
    answer = input(f"Delete expense {expense['id']} ({expense['description']}, "
                   f"${expense['amount']:.2f})? Type YES to confirm: ").strip()
    if answer.lower() != "yes":
        print("Deletion cancelled.")
        return
    if storage.delete_expense(expense["id"]):
        print("Expense deleted.")
    else:
        print("Expense no longer exists.")


def show_forecast():
    print("Enter the last fully logged day in the month. Days without entries count as $0.")
    value = Getter().get_date()
    if value == "exit":
        return
    as_of = Date.fromisoformat(value)
    if as_of > Date.today():
        print("Choose today or an earlier date.")
        return

    daily_cents = storage.load_daily_spending(as_of.replace(day=1), as_of)
    if not daily_cents:
        print("No spending logged through that date. Record expenses before forecasting.")
        return
    spent = Decimal(sum(daily_cents.values())) / 100
    estimate = forecast.forecast_month_end(daily_cents, as_of)
    print(f"Spent through {as_of}: ${spent:.2f}")
    print(f"Baseline month-end estimate: ${estimate:.2f}")

    month = as_of.isoformat()[:7]
    budget = storage.load_budgets().get(month)
    if as_of.day < forecast.MIN_SIMULATION_DAYS:
        print(f"Simulation becomes available after {forecast.MIN_SIMULATION_DAYS} fully logged days.")
        return

    simulated = forecast.simulate_month_end(daily_cents, as_of, budget)
    print(f"Middle 80% of simulated totals: ${simulated['lower']:.2f}–${simulated['upper']:.2f}")
    if budget is None:
        print("Set a monthly budget with option 7 to estimate the chance of exceeding it.")
    else:
        print(f"Simulated chance of exceeding ${budget:.2f}: {simulated['chance_over']:.1%}")
    print("The simulation samples calendar days from this month through the cutoff date.")


def show_forecast_backtest():
    print("Enter the first fully logged month. All completed months from then are evaluated.")
    value = get_month()
    if value is None:
        return
    first_month = Date.fromisoformat(value + "-01")
    last_completed_day = Date.today().replace(day=1) - timedelta(days=1)
    if first_month > last_completed_day:
        print("Choose a completed month.")
        return

    daily_cents = storage.load_daily_spending(first_month, last_completed_day)
    if not daily_cents:
        print("No spending logged in the selected period.")
        return
    results = forecast.backtest(daily_cents, first_month, last_completed_day)
    rows = [
        {"Month": row["month"], "Day-10 forecast": f"${row['forecast']:.2f}",
         "Actual": f"${row['actual']:.2f}", "Absolute error": f"${row['absolute_error']:.2f}"}
        for row in results
    ]
    print(tabulate(rows, headers="keys", tablefmt="grid"))
    mean_error = sum(row["absolute_error"] for row in results) / len(results)
    print(f"Mean absolute error across {len(results)} month(s): ${mean_error:.2f}")


if __name__ == "__main__":
    main()
