"""Calculations on expenses already in memory; no file access or printing."""
from decimal import Decimal

from validation import parse_amount, parse_month


def calculate_total(expenses):
    """Return a Decimal total, including Decimal('0.00') for an empty input."""
    return sum((expense["amount"] for expense in expenses), Decimal("0.00"))


def summarize_by_category(expenses):
    """Return each category's total; the input is never modified."""
    totals = {}
    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, Decimal("0.00")) + expense["amount"]
    return totals


def category_percentages(totals):
    """Return percentages from category totals; round only when displaying."""
    total = sum(totals.values(), Decimal("0.00"))
    return {category: amount / total * 100 if total else Decimal("0")
            for category, amount in totals.items()}


def summarize_by_month(expenses):
    """Return monthly totals in chronological order, keeping years distinct."""
    totals = {}
    for expense in expenses:
        month = parse_month(expense["date"][:7])
        totals[month] = totals.get(month, Decimal("0.00")) + expense["amount"]
    return dict(sorted(totals.items()))


def expenses_for_month(expenses, month):
    month = parse_month(month)
    return [expense for expense in expenses if expense["date"][:7] == month]


def calculate_budget_status(expenses, month, budget):
    """Return monthly spending and signed remaining funds (negative if over)."""
    budget = parse_amount(str(budget))
    spent = calculate_total(expenses_for_month(expenses, month))
    return {"budget": budget, "spent": spent, "remaining": budget - spent,
            "percentage_used": spent / budget * 100}
