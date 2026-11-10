# Changelog

## v0.2 — SQLite Storage and Spending Analysis

- Separate the command-line interface, persistence, validation, and calculations.
- Store expenses and monthly limits in SQLite, with exact integer-cent amounts.
- Import legacy CSV/JSON data once in a transaction, preserving the source files.
- Add stable expense IDs, editing, and deletion with confirmation.
- Add category totals and percentages, monthly summaries, and budget status.
- Validate dates and amounts, handle empty data, and test failure cases.
- Include 86 automated tests, a beginner SQL guide, and fictional sample data.

## Initial version

- Add, view, and total expenses through a command-line interface backed by CSV.
