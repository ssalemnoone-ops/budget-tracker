# v0.1 — Original Budget Calculator

This is the original code and its original tests, copied unchanged from
[the first published version](https://github.com/ssalemnoone-ops/budget-tracker/tree/d02e5515cca4356f98f5cf7b77a1efb8fb059ed9).

It shows the starting point: a single Python file, CSV persistence, a command-line
menu, expense totals, and 9 pytest tests. Its original behavior and limitations are
preserved, including the 2026–2028 date restriction and floating-point amounts.

## Run this version separately

From the repository root, activate the environment created using the main README,
then enter this directory:

```sh
cd archive/v0.1
cp budget.sample.csv budget.csv
python budget.py
```

The sample file contains only a CSV header, with no personal transactions.
Run from this directory so the original relative CSV path stays inside the archive.
Copy the sample only when starting a new archive budget; it replaces any existing CSV.

Run the original tests from this directory with:

```sh
python -m pytest -q
```

The local pytest configuration isolates these historical tests from the current app.
The original Quit option exits with a message and a nonzero status; this was fixed
in the current version.

## See the progression

- [Current application and progression table](../../README.md)
- [Changes between the original and SQLite update](https://github.com/ssalemnoone-ops/budget-tracker/compare/d02e5515cca4356f98f5cf7b77a1efb8fb059ed9...22b993c70184f08226d0899c0f9fe948077ef862)
