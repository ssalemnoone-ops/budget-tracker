"""Reproduce the forecast experiment using fictional spending and temporary SQLite."""
import argparse
from calendar import monthrange
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile

import numpy as np

import forecast
import storage

DATA_SEED = 20261118
CUTOFFS = (7, 10, 15, 20)
YEAR = 2025


def generate_expenses(seed=DATA_SEED):
    """Generate a complete fictional year, including implicit zero-spending days."""
    rng = np.random.default_rng(seed)
    expenses = []
    for month in range(1, 13):
        days = monthrange(YEAR, month)[1]
        # These known schedules are deliberately not supplied to the current model.
        payments = [(1, "Recurring Bills & Utilities", "Synthetic rent", 90_000),
                    (8, "Recurring Bills & Utilities", "Synthetic streaming", 1_200),
                    (18, "Recurring Bills & Utilities", "Synthetic phone", 4_500)]
        if month in (3, 7, 11):
            payments.append((int(rng.integers(12, days + 1)), "Shopping & Retail",
                             "Synthetic large item", int(rng.integers(15_000, 40_001))))
        for day in range(1, days + 1):
            current = date(YEAR, month, day)
            # Some days have no discretionary transactions; weekends differ from weekdays.
            if rng.random() < 0.38:
                payments.append((day, "Groceries", "Synthetic groceries",
                                 int(rng.integers(800, 6_501))))
            dining_probability = 0.45 if current.weekday() >= 5 else 0.15
            if rng.random() < dining_probability:
                payments.append((day, "Dining & Restaurants", "Synthetic dining",
                                 int(rng.integers(800, 4_001))))
            if rng.random() < 0.18:
                payments.append((day, "Transportation & Transit", "Synthetic transit", 335))
        for day, category, description, cents in sorted(payments):
            expenses.append({"date": date(YEAR, month, day).isoformat(),
                             "category": category, "description": description,
                             "amount": Decimal(cents) / 100})
    return expenses


def evaluate(expenses):
    """Run 48 date-cutoff replays through the app's SQL and forecasting functions."""
    results = []
    with tempfile.TemporaryDirectory(prefix="budget-evaluation-") as temporary:
        database = Path(temporary) / "synthetic.db"
        for expense in expenses:
            storage.save_expense(expense, database)
        for month in range(1, 13):
            start = date(YEAR, month, 1)
            end = date(YEAR, month, monthrange(YEAR, month)[1])
            actual_daily = storage.load_daily_spending(start, end, database)
            actual = Decimal(sum(actual_daily.values())) / 100
            for day in CUTOFFS:
                cutoff = date(YEAR, month, day)
                # Future transactions cannot enter this SQL result.
                observed = storage.load_daily_spending(start, cutoff, database)
                predicted = forecast.forecast_month_end(observed, cutoff)
                simulated = forecast.simulate_month_end(
                    observed, cutoff, seed=DATA_SEED + month * 100 + day,
                )
                error = predicted - actual
                results.append({
                    "month": start.isoformat()[:7], "cutoff_day": day,
                    "forecast": float(predicted), "actual": float(actual),
                    "absolute_error": float(abs(error)), "signed_error": float(error),
                    "lower": float(simulated["lower"]), "upper": float(simulated["upper"]),
                    "covered": simulated["lower"] <= actual <= simulated["upper"],
                    "interval_width": float(simulated["upper"] - simulated["lower"]),
                })
    return results


def summarize(results):
    summaries = []
    for cutoff in CUTOFFS:
        rows = [row for row in results if row["cutoff_day"] == cutoff]
        summaries.append({
            "cutoff_day": cutoff, "months": len(rows),
            "mae": float(np.mean([row["absolute_error"] for row in rows])),
            "bias": float(np.mean([row["signed_error"] for row in rows])),
            "coverage": float(np.mean([row["covered"] for row in rows])),
            "mean_interval_width": float(np.mean([row["interval_width"] for row in rows])),
        })
    return summaries


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_results(results, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter

    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharey=True, layout="constrained")
    labels = [date(YEAR, month, 1).strftime("%b") for month in range(1, 13)]
    x = np.arange(12)
    for axis, cutoff in zip(axes.flat, CUTOFFS):
        rows = [row for row in results if row["cutoff_day"] == cutoff]
        axis.fill_between(x, [r["lower"] for r in rows], [r["upper"] for r in rows],
                          color="#4477AA", alpha=0.18, label="Simulated 80% interval")
        axis.plot(x, [r["forecast"] for r in rows], color="#4477AA", marker="o",
                  linewidth=1.8, label="Baseline forecast")
        axis.plot(x, [r["actual"] for r in rows], color="#AA3377", marker="s",
                  linewidth=1.8, label="Actual spending")
        axis.set_title(f"Forecast after day {cutoff}", loc="left", fontweight="bold")
        axis.set_xticks(x, labels)
        axis.set_ylabel("Month-end spending ($)")
        axis.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        axis.grid(axis="y", alpha=0.22)
        axis.set_ylim(bottom=0)
        axis.spines[["top", "right"]].set_visible(False)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc="outside lower center", ncol=3, frameon=False)
    figure.suptitle("Forecast evaluation on 12 fictional months (2025)", fontsize=17,
                   fontweight="bold")
    figure.savefig(output / "forecast_evaluation.png", dpi=160)
    figure.savefig(output / "forecast_evaluation.svg")
    plt.close(figure)


def write_report(expenses, results, summary, output):
    days_with_spending = len({expense["date"] for expense in expenses})
    zero_days = 365 - days_with_spending
    metrics = "\n".join(
        f"| {row['cutoff_day']} | {row['months']} | ${row['mae']:,.2f} | "
        f"${row['bias']:,.2f} | {row['coverage']:.1%} | ${row['mean_interval_width']:,.2f} |"
        for row in summary
    )
    worst = max(results, key=lambda row: row["absolute_error"])
    report = f"""# Version 3 forecast evaluation

**All data and results on this page come from fictional spending.** This experiment
assesses the current method on one specified generator. It does not establish its
accuracy for a real person's budget.

![Baseline forecasts, actual totals, and simulation intervals](forecast_evaluation.svg)

## Results

| Cutoff day | Months | Baseline MAE | Baseline bias | 80% interval coverage | Mean interval width |
| --- | --- | --- | --- | --- | --- |
{metrics}

MAE is mean absolute error in dollars. Bias averages forecast minus actual, so
positive values indicate overprediction. Coverage is the fraction of actual month
totals inside the lower and upper endpoints, inclusive. Each row contains only
12 months, so one hit changes coverage by 8.3 percentage points. The four cutoff
rows reuse the same months and are dependent evaluations.

The largest baseline miss occurred in {worst['month']} at day {worst['cutoff_day']}.
It forecast ${worst['forecast']:,.2f} against ${worst['actual']:,.2f} actual spending,
an absolute error of ${worst['absolute_error']:,.2f}.

## Data and experiment design

- Fixed data seed `{DATA_SEED}` and calendar year `{YEAR}`.
- {len(expenses)} fictional transactions and {zero_days} zero-spending calendar days.
- Rent of $900 on day 1, streaming of $12 on day 8, and phone service of $45 on day 18.
- Daily grocery probability 0.38, dining probability 0.45 on weekends and 0.15 on
  weekdays, and transit probability 0.18. Amounts are generated as integer cents.
- One additional purchase between $150 and $400 in March, July, and November,
  randomly scheduled on day 12 or later.
- All calendar days are fully observed. Missing transaction dates mean zero spending.
- Every cutoff uses only that month's days 1 through the cutoff, inclusive.
- 5,000 simulation paths for each cutoff, with seed `{DATA_SEED} + month * 100 + day`.
- The model uses the same functions as the application. SQLite groups transactions
  by date and filters the forecast inputs before they reach NumPy.

## How the experiment works

`evaluate_forecasts.py` creates a disposable SQLite database and inserts the generated
transactions. A separate query obtains the actual full-month total for scoring.
Forecast queries end on the cutoff date, preventing later spending from entering
predictions. Zero-spending days are filled in by the forecasting code.

The baseline multiplies observed spending by days-in-month / elapsed-days.
The bootstrap samples observed daily amounts with replacement for each remaining
day, adds spending already observed, and takes the 10th and 90th percentiles.
Its expected point forecast equals the baseline mathematically. This experiment
therefore evaluates baseline point accuracy alongside the bootstrap's interval
coverage and width. It does not claim a second, superior point forecasting model.

## Findings and limitations

Across these months, baseline MAE falls from ${summary[0]['mae']:,.2f} at day 7 to
${summary[-1]['mae']:,.2f} at day 20. Every baseline prediction exceeds its actual
monthly total. Interval coverage is {summary[0]['coverage']:.1%} at day 7,
{summary[1]['coverage']:.1%} at day 10, {summary[2]['coverage']:.1%} at day 15, and
{summary[3]['coverage']:.1%} at day 20. Coverage does not improve monotonically.

Rent arrives at the beginning of every month. Scaling that early total to the
whole month overpredicts spending. Resampling daily totals can select the rent day
multiple times, producing very wide simulated ranges. Coverage must be assessed
alongside interval width. A wide interval can cover actual spending while offering
little precision. The reported coverage is measured on these fictional months,
and the label 80% is the simulation's nominal level.

The generator also includes weekday effects and occasional future purchases.
Independent sampling misses those patterns and cannot anticipate a large expense
that has no analogue among the days already observed. Estimates may improve later
in a month, but that pattern needs to be measured for each dataset.

The fixed generator and seed make the run reproducible. Repeated runs using that
same seed are not independent validation. There are no fitted parameters or tuning
steps, and these months are an exploratory benchmark. A next model could schedule
known bills separately from variable daily spending, then be evaluated on fresh
synthetic seeds and fully logged real months.

## Reproduce

From the project root, with its virtual environment active, run

```sh
python -m pip install -r requirements-dev.txt
python evaluate_forecasts.py
```

The output directory defaults to `reports/v3`. Use `--output-dir /tmp/budget-report`
to write a separate copy. The script uses temporary SQLite storage and generates
all of its own data. It never opens the application's personal `budget.db`.

Outputs include `synthetic_expenses.csv`, `predictions.csv`, `summary.csv`, this
report, and PNG/SVG charts. The CSV files retain unrounded metric values. Displayed
dollars are rounded to cents. Inspect `environment.txt` for package versions.
"""
    (output / "REPORT.md").write_text(report, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent / "reports" / "v3")
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    expenses = generate_expenses()
    results = evaluate(expenses)
    summary = summarize(results)
    write_csv(output / "synthetic_expenses.csv", expenses)
    write_csv(output / "predictions.csv", results)
    write_csv(output / "summary.csv", summary)
    plot_results(results, output)
    write_report(expenses, results, summary, output)
    import matplotlib
    import platform
    import sqlite3
    (output / "environment.txt").write_text(
        f"Python {platform.python_version()}\nNumPy {np.__version__}\n"
        f"Matplotlib {matplotlib.__version__}\nSQLite {sqlite3.sqlite_version}\n"
        f"Data seed {DATA_SEED}\nSimulation paths {forecast.SIMULATIONS}\n",
        encoding="utf-8",
    )
    print(f"Evaluated {len(results)} forecasts on {len(expenses)} fictional transactions.")
    for row in summary:
        print(f"Day {row['cutoff_day']:2}: MAE ${row['mae']:.2f}, "
              f"coverage {row['coverage']:.1%}, mean width ${row['mean_interval_width']:.2f}")
    print(f"Report saved to {output / 'REPORT.md'}")


if __name__ == "__main__":
    main()
