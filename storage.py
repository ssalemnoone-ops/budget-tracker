"""SQLite persistence; public functions return Decimal amounts to Python."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3

from legacy_import import _read_legacy_budgets, _read_legacy_expenses
from validation import parse_amount, parse_month

DB_FILE = Path(__file__).resolve().with_name("budget.db")
DatabaseError = sqlite3.Error
SCHEMA = (
    """CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL CHECK(length(trim(category)) > 0),
        description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 20),
        amount_cents INTEGER NOT NULL
            CHECK(typeof(amount_cents) = 'integer' AND amount_cents > 0)
    )""",
    """CREATE TABLE IF NOT EXISTS monthly_budgets (
        month TEXT PRIMARY KEY NOT NULL,
        amount_cents INTEGER NOT NULL
            CHECK(typeof(amount_cents) = 'integer' AND amount_cents > 0)
    )""",
    """CREATE TABLE IF NOT EXISTS migrations (
        name TEXT PRIMARY KEY NOT NULL,
        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
)


@contextmanager
def _connect(path=None):
    """Commit successful operations, roll back failures, always close."""
    connection = sqlite3.connect(DB_FILE if path is None else path)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            for statement in SCHEMA:
                connection.execute(statement)
            yield connection
    finally:
        connection.close()


def _to_cents(amount):
    amount = parse_amount(str(amount))
    cents = int(amount * 100)
    if cents > 2**63 - 1:
        raise ValueError("Amount is too large for SQLite's integer storage.")
    return cents


def _expense_values(expense):
    value = expense["date"]
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError("Use an expense date in YYYY-MM-DD format.")
    category = expense["category"].strip()
    description = expense["description"].strip()
    if not category or not 1 <= len(description) <= 20:
        raise ValueError("Category is required; description must be 1–20 characters.")
    return value, category, description, _to_cents(expense["amount"])


def save_expense(expense, path=None):
    """Insert one expense and return its stable ID."""
    values = _expense_values(expense)
    with _connect(path) as connection:
        cursor = connection.execute(
            "INSERT INTO expenses (date, category, description, amount_cents) VALUES (?, ?, ?, ?)",
            values,
        )
        return cursor.lastrowid


def load_expenses(path=None):
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT id, date, category, description, amount_cents FROM expenses ORDER BY id"
        ).fetchall()
    return [{"id": row["id"], "date": row["date"], "category": row["category"],
             "description": row["description"],
             "amount": Decimal(row["amount_cents"]) / 100} for row in rows]


def update_expense(expense_id, expense, path=None):
    """Replace the fields of one ID; return whether it existed."""
    values = _expense_values(expense)
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE expenses SET date = ?, category = ?, description = ?, amount_cents = ? WHERE id = ?",
            (*values, expense_id),
        )
        return cursor.rowcount == 1


def delete_expense(expense_id, path=None):
    """Delete only the selected ID; the interface asks for confirmation."""
    with _connect(path) as connection:
        cursor = connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount == 1


def load_budgets(path=None):
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT month, amount_cents FROM monthly_budgets ORDER BY month"
        ).fetchall()
    return {row["month"]: Decimal(row["amount_cents"]) / 100 for row in rows}


def save_monthly_budget(month, amount, path=None):
    month = parse_month(month)
    cents = _to_cents(amount)
    with _connect(path) as connection:
        connection.execute(
            """INSERT INTO monthly_budgets (month, amount_cents) VALUES (?, ?)
               ON CONFLICT(month) DO UPDATE SET amount_cents = excluded.amount_cents""",
            (month, cents),
        )


def migrate_legacy_data(path=None, csv_path=None, budgets_path=None):
    """Import CSV and JSON together once; preserve both files, roll back on error.

    Call at app startup, before allowing new entries. A marker in the same
    transaction prevents duplicate imports on subsequent starts.
    """
    database = Path(DB_FILE if path is None else path)
    csv_path = database.with_name("budget.csv") if csv_path is None else Path(csv_path)
    budgets_path = database.with_name("budgets.json") if budgets_path is None else Path(budgets_path)
    with _connect(database) as connection:
        # Acquire the write lock before checking the marker so two starts cannot import twice.
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM migrations WHERE name = ?", ("legacy_csv_json_v1",)
        ).fetchone():
            return False
        if connection.execute("SELECT 1 FROM expenses LIMIT 1").fetchone() or connection.execute(
            "SELECT 1 FROM monthly_budgets LIMIT 1"
        ).fetchone():
            raise ValueError("Automatic import requires an empty database; existing data was preserved.")
        expenses = _read_legacy_expenses(csv_path)
        budgets = _read_legacy_budgets(budgets_path)
        for expense in expenses:
            connection.execute(
                "INSERT INTO expenses (date, category, description, amount_cents) VALUES (?, ?, ?, ?)",
                _expense_values(expense),
            )
        for month, amount in budgets.items():
            connection.execute(
                "INSERT INTO monthly_budgets (month, amount_cents) VALUES (?, ?)",
                (parse_month(month), _to_cents(amount)),
            )
        connection.execute("INSERT INTO migrations (name) VALUES (?)", ("legacy_csv_json_v1",))
    return True
