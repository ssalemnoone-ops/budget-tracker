# Learn SQL through your budget calculator

## 1. Python, SQL, and SQLite

Python runs your menus and analysis. SQL is the language used to ask a database to
read or change records. SQLite is the database engine executing those instructions.
Your database is the local file `budget.db`; no server is needed.

Previously, loading expenses meant reading every row of a CSV. Now `storage.py`
opens a connection and executes SQL. Your analysis code still receives dictionaries.

## 2. Tables, rows, and columns

A table resembles a spreadsheet: columns define fields and each row is a record.
Your database has three tables:

- `expenses`: id, date, category, description, amount_cents.
- `monthly_budgets`: month and amount_cents.
- `migrations`: name and applied_at, to remember that import has finished.

Example expense row: `1 | 2026-11-04 | Groceries | Lunch | 1250`.
The amount means $12.50. Integer cents avoid floating-point representation errors.
Python converts those cents back to a Decimal when loading records.

## 3. CREATE TABLE and constraints

The actual expenses definition starts:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category TEXT NOT NULL CHECK(length(trim(category)) > 0),
    description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 20),
    amount_cents INTEGER NOT NULL
        CHECK(typeof(amount_cents) = 'integer' AND amount_cents > 0)
);
```

`CREATE TABLE` defines the structure. `IF NOT EXISTS` makes repeated startup safe.
`INTEGER` and `TEXT` describe stored values. `NOT NULL` prohibits missing values.
`CHECK` rejects rows that violate a rule. `PRIMARY KEY` identifies a row uniquely;
`AUTOINCREMENT` prevents automatically assigned IDs from reusing deleted IDs.
Python also validates dates and amounts before sending them to SQLite.

## 4. INSERT: add an expense

`save_expense()` executes:

```python
connection.execute(
    "INSERT INTO expenses (date, category, description, amount_cents) VALUES (?, ?, ?, ?)",
    ("2026-11-04", "Groceries", "Lunch", 1250),
)
```

The columns name where each value goes. Each `?` is filled from the separate tuple
in the same order. This keeps input as data, including apostrophes, rather than
letting it become SQL code. Do not construct SQL by interpolating user input.
`cursor.lastrowid` returns the ID assigned to the new expense.

## 5. SELECT: retrieve records

`load_expenses()` uses:

```sql
SELECT id, date, category, description, amount_cents
FROM expenses
ORDER BY id;
```

`SELECT` chooses columns, `FROM` chooses a table, and `ORDER BY` sorts the result.
`fetchall()` collects the result rows. `sqlite3.Row` lets Python use column names,
such as `row['amount_cents']`. The function converts each result to a dictionary
with `amount` as a Decimal and includes the new `id` field.

To select one category, the pattern is:

```sql
SELECT * FROM expenses WHERE category = ?;
```

`WHERE` filters records. `*` means every column. Supply the category separately
when executing this query from Python.

## 6. UPDATE and DELETE: target one ID

`update_expense()` executes:

```sql
UPDATE expenses
SET date = ?, category = ?, description = ?, amount_cents = ?
WHERE id = ?;
```

The first four values replace the fields; the final value selects the record.
Without `WHERE`, UPDATE would change every row. Your interface asks you to re-enter
all fields and saves only after every input succeeds.

`delete_expense()` uses:

```sql
DELETE FROM expenses WHERE id = ?;
```

The interface displays the selected record and requires YES before executing it.
`cursor.rowcount` tells Python whether a row was affected. Try these operations
only on disposable sample data while learning.

## 7. Monthly budgets and UPSERT

The month is the primary key, so each month has at most one limit:

```sql
INSERT INTO monthly_budgets (month, amount_cents) VALUES (?, ?)
ON CONFLICT(month) DO UPDATE SET amount_cents = excluded.amount_cents;
```

For a new month this inserts. If that month exists, it updates its amount.
`excluded.amount_cents` means the amount from the attempted insert. This operation
is commonly called an upsert: update or insert.

## 8. Transactions: commit or roll back

The `_connect()` context manager opens a connection, prepares tables, and yields
the connection to the caller. Inside `with connection:`, successful changes commit
(save together). If an exception occurs, pending changes roll back. A `finally`
block closes the connection even when an operation fails.

The migration acquires a write lock with `BEGIN IMMEDIATE`, checks its marker,
imports both legacy sources, then inserts a completion marker in the same
transaction. If a row fails, records and marker roll back together. Restarting
checks the marker and skips import after a successful run.

## 9. Safe first practice

Create a separate practice database, never your personal budget database:

```sh
sqlite3 /tmp/budget-practice.db
```

Then enter:

```sql
CREATE TABLE IF NOT EXISTS practice_expenses (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);
INSERT INTO practice_expenses (category, amount_cents) VALUES ('Groceries', 1250);
INSERT INTO practice_expenses (category, amount_cents) VALUES ('Transit', 350);
SELECT * FROM practice_expenses;
SELECT category, SUM(amount_cents) FROM practice_expenses GROUP BY category;
```

`SUM` adds values and `GROUP BY` forms one group per category. These totals remain
in cents. Exit the SQLite terminal with `.quit`.

Exercises: select only Groceries; update one amount by ID; delete one row by ID;
explain why the monthly budget primary key differs from the expense primary key.
The current application still performs category and monthly analysis in Python;
these SQL exercises introduce a possible later extension.
