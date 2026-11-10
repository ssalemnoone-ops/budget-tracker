import sys
import re
from datetime import datetime
import csv
from tabulate import tabulate

class Getter:
    def get_date(self):
        pattern = '^(2026|2027|2028)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$'
        while True:
            print('Please enter the date in this format: YYYY-MM-DD')
            date = input("Date: ").strip()
            if date.lower() == 'exit':
                return 'exit' 
            if re.match(pattern, date):
                try:
                    datetime.strptime(date, "%Y-%m-%d") 
                    return date
                except ValueError:
                    print('Please input a valid date and try again.')
            else:
                print('Please input a valid date and try again.')

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
            choice = input("Please select the number of the wanted category: ")
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
            description = input("Please enter your descrition. (20 characters MAX):\n")
            if description.lower() == 'exit':
                return 'exit' 
            if len(description) <= 20:
                return description
            print("Too many words. Please use less than 20 characters and try again.")

    def get_amount(self):
        while True:
            try:
                price = input("Please enter the price: ")
                if price.lower().strip() == 'exit':
                    return 'exit' 
                price = float(price)
                return f"${price:.2f}"
            except ValueError:
                print("Please enter a valid numebr and try again.")
                continue


def main():
    print('Welcome to the budget Calulator')
    while True:
        action = get_action()
        if action == 1:
            get_expense()
        elif action == 2:
            print(total_expense())
            print('The procedure is completed.\n')
        elif action == 3:
            #print(view_expense())
            print(tabulate(view_expense(), headers="keys", tablefmt="grid")+'\n')
        elif action == 4:
            sys.exit('Thank You for Using Budget Calculator.')


def get_action():
    while True:
        try:
            action = int(input('Please select the number of an option:' 
                               '\n1. Insert your epense \n2. Calculate the total expense \n3. View your expense \n4. Quit\n'))
            match action:
                case 1:
                    return 1
                case 2:
                    return 2
                case 3:
                    return 3
                case 4:
                    return 4
        except ValueError:
            print('Please enter a valid number and try again.')

def get_expense():
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
        if amount.lower() == 'exit':
            break

        with open('budget.csv', 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["date", "category", "description", "amount"])


            writer.writerow({'date': date, 'category': category, 'description': description, 'amount': amount})
        print('The expense is recorded.\n')
    print('The procedure is completed.\n')
        


def view_expense():
    with open('budget.csv', 'r') as file:
        reader = csv.DictReader(file)
        expense = list(reader)

        return expense


def total_expense():
    with open('budget.csv', 'r') as file:
        reader = csv.DictReader(file)

        total = 0
        for row in reader:
            total += float(row["amount"].strip('$'))
        return f'${total}'

    
if __name__ == "__main__":
    main()