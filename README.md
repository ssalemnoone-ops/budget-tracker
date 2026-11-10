# Budget Calculator

A Python command-line expense tracker with SQLite storage, exact money values,
category reports, monthly summaries, and monthly spending limits.

## Run

Requires **Python 3.10 or newer**. On macOS or Linux:

```sh
git clone https://github.com/ssalemnoone-ops/budget-tracker.git
cd budget-tracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python budget.py
```

Run the tests with `python -m pytest -q`. To install just the application,
use `requirements.txt` instead of `requirements-dev.txt`.

### Try fictional sample data

In a fresh clone, **before the first launch**, optionally copy the examples:

```sh
cp examples/budget.sample.csv budget.csv
cp examples/budgets.sample.json budgets.json
python budget.py
```

The app imports these fictional records once. If you skip this step, it starts
with an empty database. Keep real financial data local; `.gitignore` excludes
runtime databases and legacy data files.

Python provides `sqlite3`; no database server or extra database package is needed.
The runtime dependency is `tabulate`; tests use `pytest`.

## Menu

1. Add expenses
2. Total expenses
3. View expenses, including their IDs
4. Quit
5. Category totals and percentage shares
6. Monthly spending totals
7. Set or update a monthly budget (`YYYY-MM`)
8. Monthly budget status and category shares
9. Edit an expense by ID (re-enter its four fields; EXIT cancels)
10. Delete an expense by ID (requires typing YES)

Dates use `YYYY-MM-DD`. Amounts must be positive with at most two decimal places.
Category percentages are rounded for display and may not add to exactly 100%.
Monthly limits are independent and do not roll over.

## Storage and migration

`budget.db` lives beside `storage.py`, independent of the launch directory.
On startup, the application creates its tables and imports `budget.csv` and
`budgets.json` from that directory once. Both old files are preserved unchanged.
Subsequent changes are saved only in SQLite; editing the old files will not update
the database. A migration marker prevents duplicates even after restarting.
Identical legitimate expenses in the CSV remain separate records.

If legacy data is invalid, the import rolls back without partial records or a
completion marker. Fix the original file and restart. Automatic import refuses to
mix legacy records into an already populated, unmarked database.

Back up `budget.db` while the app is closed. It contains personal financial data.
Deleting an expense from the running app is permanent; cancellation leaves it
unchanged. Legacy files are historical snapshots, not current backups.

## Code structure

| File | Responsibility |
| --- | --- |
| `budget.py` | Menus, prompts, formatting, and delete confirmation |
| `storage.py` | SQLite schema, inserts, queries, updates, deletes, migration |
| `legacy_import.py` | Read the preserved CSV and JSON for migration only |
| `analysis.py` | Calculations on expense dictionaries in memory |
| `validation.py` | Parse amounts and months |
| `tests/` | Temporary databases and behavior tests; never use personal data |
| `SQL_GUIDE.md` | Beginner walkthrough of the actual database code |

SQLite stores money as integer cents (1250 means $12.50). Loading converts it back
to `Decimal`, so existing analysis functions still work. Each expense has a unique
ID which stays unchanged when edited. `monthly_budgets.month` is a primary key,
so setting a limit again updates that month rather than creating a duplicate.

All variable query values use `?` placeholders. Successful writes commit; failures
roll back and connections always close. Reports still aggregate in Python; moving
storage to SQLite does not automatically change their O(n) time complexity.

## Second update

See [CHANGELOG.md](CHANGELOG.md) for the v0.2 milestone and
[SQL_GUIDE.md](SQL_GUIDE.md) for a beginner walkthrough of the database code.
