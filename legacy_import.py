"""Readers for preserved CSV/JSON files, used only during migration."""
import csv
import json
from pathlib import Path

from validation import parse_amount, parse_month

FIELDNAMES = ["date", "category", "description", "amount"]


def _read_legacy_expenses(path):
    """Read expenses; accept old dollar-prefixed amounts as well as new ones."""
    path = Path(path)
    try:
        file = path.open("r", newline="", encoding="utf-8")
    except FileNotFoundError:
        return []
    with file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        if reader.fieldnames != FIELDNAMES:
            raise ValueError("CSV headers must be: " + ", ".join(FIELDNAMES))
        expenses = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Incomplete CSV row near line {reader.line_num}.")
            try:
                row["amount"] = parse_amount(row["amount"].strip().removeprefix("$"))
            except ValueError as exc:
                raise ValueError(f"Invalid amount near CSV line {reader.line_num}: {exc}") from exc
            expenses.append(row)
        return expenses


def _read_legacy_budgets(path):
    """Return month-to-Decimal limits, or an empty mapping for a new budget."""
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ValueError("The monthly budget file contains invalid JSON.") from exc
    if not isinstance(data, dict):
        raise ValueError("The monthly budget file must map months to amounts.")
    budgets = {}
    for month, amount in data.items():
        if not isinstance(amount, str):
            raise ValueError("Monthly budget amounts must be stored as strings.")
        budgets[parse_month(month)] = parse_amount(amount)
    return budgets
