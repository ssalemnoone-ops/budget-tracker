# Budget Tracker

An early-stage Python command-line expense tracker. Record categorized expenses, view them in a table, and calculate total spending from a local CSV file.

## Run

Requires Python 3.10 or newer. From the project folder:

```bash
python3 -m pip install tabulate
python3 budget.py
```

Use the menu to add an expense, calculate the total, view entries, or quit. Type `EXIT` during expense entry to cancel. The included `budget.csv` contains only the headers; your entries are stored locally when you use the app.

## Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

The initial test suite covers input handling and total calculation. All 9 tests passed before this upload.

## Status and next steps

This is an initial working version, with more updates planned. Current limits include dates restricted to 2026–2028, amounts stored as formatted strings, and no edit/delete function.

Planned improvements:
- Improve amount validation and use decimal arithmetic for money.
- Add filtering and spending summaries by category or month.
- Support editing/deleting entries and expand test coverage.

Future updates will use descriptive commits explaining each change. This first version provides a baseline for tracking progress.
