from decimal import Decimal
import sqlite3

import pytest

import storage


def expense(amount="12.50", description="Lunch"):
    return dict(date="2026-11-04", category="Groceries", description=description,
                amount=Decimal(amount))


def test_insert_id_persistence_and_integer_cents(tmp_path):
    path = tmp_path / "new.db"
    first = storage.save_expense(expense("0.10"), path)
    second = storage.save_expense(expense("0.20"), path)
    rows = storage.load_expenses(path)
    assert [row["id"] for row in rows] == [first, second]
    assert rows[0]["amount"] + rows[1]["amount"] == Decimal("0.30")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT amount_cents, typeof(amount_cents) FROM expenses ORDER BY id").fetchall() == [(10, "integer"), (20, "integer")]


def test_update_delete_only_target_record():
    first = storage.save_expense(expense())
    second = storage.save_expense(expense("5"))
    assert storage.update_expense(first, expense("20", "Changed"))
    assert storage.load_expenses()[0]["description"] == "Changed"
    assert storage.load_expenses()[1]["amount"] == Decimal("5")
    assert not storage.update_expense(999, expense())
    assert storage.delete_expense(first)
    assert not storage.delete_expense(first)
    assert [row["id"] for row in storage.load_expenses()] == [second]
    third = storage.save_expense(expense())
    assert third > second


def test_invalid_update_leaves_record_unchanged():
    expense_id = storage.save_expense(expense())
    with pytest.raises(ValueError):
        storage.update_expense(expense_id, expense("-1"))
    assert storage.load_expenses()[0]["amount"] == Decimal("12.50")


def test_sql_text_is_stored_as_data():
    text = "x'); DROP TABLE x;--"
    storage.save_expense(expense(description=text))
    assert storage.load_expenses()[0]["description"] == text
    storage.save_expense(expense())
    assert len(storage.load_expenses()) == 2


def test_budget_upsert_preserves_other_months():
    storage.save_monthly_budget("2026-11", Decimal("100"))
    storage.save_monthly_budget("2026-12", Decimal("200"))
    storage.save_monthly_budget("2026-11", Decimal("150.50"))
    assert storage.load_budgets() == {"2026-11": Decimal("150.50"), "2026-12": Decimal("200")}


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "1.234", "100000000000000000"])
def test_invalid_amounts_not_saved(amount):
    with pytest.raises(ValueError):
        storage.save_expense(expense(amount))
    assert storage.load_expenses() == []


def legacy_files(tmp_path, csv_content=None, json_content=None):
    csv = tmp_path / "budget.csv"
    json = tmp_path / "budgets.json"
    csv.write_text(csv_content if csv_content is not None else
                   "date,category,description,amount\n2026-11-04,Groceries,Lunch,$12.50\n2026-11-04,Groceries,Lunch,$12.50\n")
    json.write_text(json_content if json_content is not None else '{"2026-11": "100.00"}')
    return csv, json


def test_migration_once_keeps_identical_real_transactions_and_source_files(tmp_path):
    path = tmp_path / "migrate.db"
    csv, json = legacy_files(tmp_path)
    original = (csv.read_bytes(), json.read_bytes())
    assert storage.migrate_legacy_data(path)
    assert len(storage.load_expenses(path)) == 2
    assert storage.load_budgets(path) == {"2026-11": Decimal("100")}
    assert not storage.migrate_legacy_data(path)
    assert len(storage.load_expenses(path)) == 2
    assert original == (csv.read_bytes(), json.read_bytes())


def test_migration_rollback_then_retry(tmp_path):
    path = tmp_path / "migrate.db"
    csv, json = legacy_files(tmp_path, json_content='{')
    with pytest.raises(ValueError):
        storage.migrate_legacy_data(path)
    assert storage.load_expenses(path) == []
    json.write_text('{"2026-11": "100.00"}')
    assert storage.migrate_legacy_data(path)
    assert len(storage.load_expenses(path)) == 2


def test_late_invalid_csv_row_rolls_back_earlier_inserts(tmp_path):
    path = tmp_path / "migrate.db"
    csv, json = legacy_files(tmp_path, csv_content="date,category,description,amount\n2026-11-04,Groceries,Lunch,10\n2026-02-30,Groceries,Food,20\n")
    with pytest.raises(ValueError):
        storage.migrate_legacy_data(path)
    assert storage.load_expenses(path) == []
    assert storage.load_budgets(path) == {}
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM migrations").fetchone()[0] == 0


def test_import_refuses_to_mix_with_existing_database(tmp_path):
    path = tmp_path / "existing.db"
    storage.save_expense(expense(), path)
    legacy_files(tmp_path)
    with pytest.raises(ValueError, match="empty database"):
        storage.migrate_legacy_data(path)
    assert len(storage.load_expenses(path)) == 1


def test_default_path_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    storage.save_expense(expense())
    assert len(storage.load_expenses()) == 1


def test_database_constraints():
    with pytest.raises(sqlite3.IntegrityError):
        with storage._connect() as connection:
            connection.execute("INSERT INTO monthly_budgets VALUES (?, ?)", ("2026-11", -1))
    assert storage.load_budgets() == {}
