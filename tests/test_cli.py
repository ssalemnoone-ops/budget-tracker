from decimal import Decimal

import pytest

import budget
import storage
from analysis import calculate_total
from budget import Getter, get_action, get_expense
from storage import load_expenses


def test_get_date(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '2026-08-27')
    get = Getter()
    assert get.get_date() == '2026-08-27'


def test_get_date_invalid(monkeypatch):
    inputs = iter(['invalid', '2026-08-27'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    get = Getter()
    assert get.get_date() == '2026-08-27'


def test_get_category(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '1')
    get = Getter()
    assert get.get_category() == 'Groceries'


def test_get_description(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: 'Lunch')
    get = Getter()
    assert get.get_description() == 'Lunch'


def test_get_description_too_long(monkeypatch):
    inputs = iter(['This description is too long', 'Lunch'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    get = Getter()
    assert get.get_description() == 'Lunch'


def test_get_amount(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '12.5')
    get = Getter()
    assert get.get_amount() == Decimal('12.50')


def test_get_amount_invalid(monkeypatch):
    inputs = iter(['abc', '12.5'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    get = Getter()
    assert get.get_amount() == Decimal('12.50')


def test_get_action(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '2')
    assert get_action() == 2


@pytest.mark.parametrize('value', ['2024-02-29', '2030-01-01', '1999-12-31'])
def test_dates_outside_original_range(monkeypatch, value):
    monkeypatch.setattr('builtins.input', lambda _: value)
    assert Getter().get_date() == value


@pytest.mark.parametrize('bad', ['2026-02-29', '2026-04-31', '2026-1-01', '20260101'])
def test_date_reprompts(monkeypatch, bad):
    inputs = iter([bad, '2024-02-29'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert Getter().get_date() == '2024-02-29'


def test_amount_reprompts_for_negative_and_nonfinite(monkeypatch):
    inputs = iter(['-10', 'nan', 'inf', '12.50'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert Getter().get_amount() == Decimal('12.50')


def test_invalid_menu_numbers(monkeypatch, capsys):
    inputs = iter(['11', '0', 'abc', '4'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert get_action() == 4
    assert capsys.readouterr().out.count('Please enter a number from 1 to 10.') == 3


@pytest.mark.parametrize('method', ['get_date', 'get_category', 'get_description', 'get_amount'])
def test_exit_at_each_prompt(monkeypatch, method):
    monkeypatch.setattr('builtins.input', lambda _: ' EXIT ')
    assert getattr(Getter(), method)() == 'exit'


@pytest.mark.parametrize('answers', [['exit'], ['2026-10-29', 'exit'], ['2026-10-29', '1', 'exit'], ['2026-10-29', '1', 'Lunch', 'exit']])
def test_cancel_does_not_write_partial_expense(monkeypatch, tmp_path, answers):
    inputs = iter(answers)
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    path = tmp_path / 'budget.csv'
    get_expense(path)
    assert not path.exists()


def test_complete_entry_then_exit(tmp_path, monkeypatch):
    inputs = iter(['2026-10-29', '1', 'Lunch', '12.50', 'exit'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    path = tmp_path / 'budget.csv'
    get_expense(path)
    assert len(load_expenses(path)) == 1
    assert calculate_total(load_expenses(path)) == Decimal('12.50')


def test_main_add_view_total_and_quit(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "budget.db")
    answers = iter(["1", "2026-11-01", "1", "Lunch", "12.50", "exit", "3", "2", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    output = capsys.readouterr().out
    assert "Lunch" in output
    assert "$12.50" in output
    assert "Thank you" in output
    assert len(load_expenses()) == 1


def test_view_does_not_replace_amounts_with_strings(monkeypatch, capsys):
    expenses = [{"date": "2026-11-01", "category": "Groceries",
                 "description": "Lunch", "amount": Decimal("12.50")}]
    monkeypatch.setattr(storage, "load_expenses", lambda: expenses)
    answers = iter(["3", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    assert "$12.50" in capsys.readouterr().out
    assert expenses[0]["amount"] == Decimal("12.50")


def test_main_empty_budget(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "missing.csv")
    answers = iter(["2", "3", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    output = capsys.readouterr().out
    assert "$0.00" in output
    assert "No expenses recorded yet." in output


def test_edit_and_delete_flow(monkeypatch, capsys):
    item = dict(date="2026-11-04", category="Groceries", description="Lunch", amount=Decimal("12.50"))
    expense_id = storage.save_expense(item)
    answers = iter(["9", str(expense_id), "2026-11-05", "1", "Dinner", "20", "10", str(expense_id), "no", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    assert storage.load_expenses()[0]["amount"] == Decimal("20")
    assert "Deletion cancelled" in capsys.readouterr().out
    answers = iter(["10", str(expense_id), "yes", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    assert storage.load_expenses() == []


def test_edit_cancel_preserves_record(monkeypatch):
    expense_id = storage.save_expense(dict(date="2026-11-04", category="Groceries", description="Lunch", amount=Decimal("12.50")))
    answers = iter([str(expense_id), "2026-11-05", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.edit_expense()
    assert storage.load_expenses()[0]["date"] == "2026-11-04"
