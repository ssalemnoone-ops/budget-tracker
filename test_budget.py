import pytest
from budget import Getter, get_action, total_expense


def test_get_date(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2026-08-27")

    get = Getter()
    assert get.get_date() == "2026-08-27"


def test_get_date_invalid(monkeypatch):
    inputs = iter(["invalid", "2026-08-27"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    get = Getter()
    assert get.get_date() == "2026-08-27"


def test_get_category(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "1")

    get = Getter()
    assert get.get_category() == "Groceries"


def test_get_description(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Lunch")

    get = Getter()
    assert get.get_description() == "Lunch"


def test_get_description_too_long(monkeypatch):
    inputs = iter(["This description is too long", "Lunch"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    get = Getter()
    assert get.get_description() == "Lunch"


def test_get_amount(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "12.5")

    get = Getter()
    assert get.get_amount() == "$12.50"


def test_get_amount_invalid(monkeypatch):
    inputs = iter(["abc", "12.5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    get = Getter()
    assert get.get_amount() == "$12.50"


def test_get_action(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2")

    assert get_action() == 2


def test_total_expense(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with open("budget.csv", "w", newline="") as file:
        file.write("date,category,description,amount\n")
        file.write("2026-08-27,Groceries,Lunch,$12.50\n")
        file.write("2026-08-28,Travel,Train,$7.50\n")

    assert total_expense() == "$20.0"