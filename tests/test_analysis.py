from decimal import Decimal

from analysis import calculate_total


def test_total_without_any_file_or_user_input():
    expenses = [{"amount": Decimal("0.10")}, {"amount": Decimal("0.20")}]
    assert calculate_total(expenses) == Decimal("0.30")
    assert expenses[0]["amount"] == Decimal("0.10")


def test_empty_total_is_decimal():
    result = calculate_total([])
    assert result == Decimal("0.00")
    assert isinstance(result, Decimal)


def test_total_accepts_an_iterator():
    expenses = ({"amount": Decimal("1.25")} for _ in range(3))
    assert calculate_total(expenses) == Decimal("3.75")
