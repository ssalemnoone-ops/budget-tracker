from decimal import Decimal

import pytest

import analysis
import budget
import storage
from validation import parse_month


@pytest.fixture
def expenses():
    return [
        {"date": "2026-11-01", "category": "Groceries", "description": "Food", "amount": Decimal("10.10")},
        {"date": "2026-11-30", "category": "Groceries", "description": "Food", "amount": Decimal("9.90")},
        {"date": "2026-11-10", "category": "Transit", "description": "Train", "amount": Decimal("5.00")},
        {"date": "2026-10-31", "category": "Transit", "description": "Train", "amount": Decimal("15.00")},
        {"date": "2027-11-01", "category": "Groceries", "description": "Food", "amount": Decimal("40.00")},
    ]


def test_category_aggregation_and_shares(expenses):
    original = [row.copy() for row in expenses]
    totals = analysis.summarize_by_category(iter(expenses))
    assert totals == {"Groceries": Decimal("60.00"), "Transit": Decimal("20.00")}
    assert analysis.category_percentages(totals) == {"Groceries": Decimal("75"), "Transit": Decimal("25")}
    assert expenses == original


def test_no_spending():
    assert analysis.summarize_by_category([]) == {}
    assert analysis.category_percentages({}) == {}
    assert analysis.category_percentages({"Groceries": Decimal("0")}) == {"Groceries": Decimal("0")}
    assert analysis.summarize_by_month([]) == {}


def test_monthly_aggregation_and_year_boundaries(expenses):
    totals = analysis.summarize_by_month(iter(expenses))
    assert list(totals) == ["2026-10", "2026-11", "2027-11"]
    assert totals == {"2026-10": Decimal("15.00"), "2026-11": Decimal("25.00"), "2027-11": Decimal("40.00")}
    assert analysis.calculate_total(analysis.expenses_for_month(expenses, "2026-11")) == Decimal("25.00")
    assert analysis.expenses_for_month(expenses, "2026-12") == []


@pytest.mark.parametrize("limit,remaining,used", [("100", "75", "25"), ("25", "0", "100"), ("20", "-5", "125")])
def test_month_budget_under_at_and_over(expenses, limit, remaining, used):
    assert analysis.calculate_budget_status(expenses, "2026-11", Decimal(limit)) == {
        "budget": Decimal(limit), "spent": Decimal("25"),
        "remaining": Decimal(remaining), "percentage_used": Decimal(used),
    }


def test_budget_without_spending():
    status = analysis.calculate_budget_status([], "2026-11", Decimal("100"))
    assert status["spent"] == Decimal("0.00")
    assert status["remaining"] == Decimal("100.00")
    assert status["percentage_used"] == 0


@pytest.mark.parametrize("month", ["2026-00", "2026-13", "2026-1", "2026-11-01", "0000-11", "bad"])
def test_invalid_month(month):
    with pytest.raises(ValueError):
        parse_month(month)


def test_valid_month():
    assert parse_month(" 2030-02 ") == "2030-02"


@pytest.mark.parametrize("limit", ["0", "-10", "nan", "inf", "10.001"])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        analysis.calculate_budget_status([], "2026-11", limit)








def test_reports_and_budget_menu_flow(tmp_path, monkeypatch, capsys, expenses):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "budget.db")
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "budget.db")
    for expense in expenses:
        storage.save_expense(expense)
    answers = iter(["5", "6", "7", "2026-13", "2026-11", "-1", "20", "8", "2026-11", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    output = capsys.readouterr().out
    assert "75.0%" in output
    assert "2027-11" in output
    assert "Budget saved for 2026-11: $20.00" in output
    assert "Spent: $25.00" in output
    assert "Over budget by: $5.00" in output
    assert "Budget used: 125.0%" in output
    assert "80.0%" in output  # November groceries share, excluding other months.
    assert storage.load_budgets() == {"2026-11": Decimal("20.00")}


@pytest.mark.parametrize("limit,message", [("100", "Remaining: $75.00"), ("25", "Budget fully used. Remaining: $0.00")])
def test_status_display(expenses, monkeypatch, capsys, limit, message):
    monkeypatch.setattr(storage, "load_expenses", lambda: expenses)
    monkeypatch.setattr(storage, "load_budgets", lambda: {"2026-11": Decimal(limit)})
    monkeypatch.setattr("builtins.input", lambda _: "2026-11")
    budget.show_monthly_budget()
    assert message in capsys.readouterr().out


def test_no_budget_or_spending(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "missing.db")
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "missing.db")
    answers = iter(["5", "6", "8", "2026-11", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    output = capsys.readouterr().out
    assert "No budget set for this month" in output
    assert "Spent: $0.00" in output
    assert storage.load_budgets() == {}


@pytest.mark.parametrize("answers", [["7", "exit", "4"], ["7", "2026-11", "exit", "4"], ["8", "exit", "4"]])
def test_budget_cancellation(tmp_path, monkeypatch, answers):
    path = tmp_path / "budget.db"
    monkeypatch.setattr(storage, "DB_FILE", path)
    values = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(values))
    budget.main()
    assert storage.load_budgets() == {}
