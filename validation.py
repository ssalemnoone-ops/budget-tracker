"""Shared validation, independent of prompts and file storage."""
from datetime import date
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def parse_amount(text):
    """Return a positive, finite amount with at most two decimal places."""
    try:
        amount = Decimal(text.strip())
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Enter a positive amount.")
        rounded = amount.quantize(CENT)
        if rounded != amount:
            raise ValueError("Use at most two decimal places.")
        return rounded
    except InvalidOperation as exc:
        raise ValueError("Enter a valid amount, such as 12.50.") from exc


def parse_month(text):
    """Validate an exact YYYY-MM month, with no restriction on the year."""
    value = text.strip()
    try:
        parsed = date.fromisoformat(value + "-01")
    except ValueError as exc:
        raise ValueError("Enter a valid month in YYYY-MM format.") from exc
    if parsed.isoformat()[:7] != value:
        raise ValueError("Enter a valid month in YYYY-MM format.")
    return value
