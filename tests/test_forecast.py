from datetime import date
from decimal import Decimal

import budget
import forecast
import storage


def test_baseline_counts_zero_days_and_excludes_later_entries():
    daily_cents = {"2026-11-02": 8_000, "2026-11-10": 12_000,
                   "2026-11-11": 5_000, "2026-10-10": 90_000}
    assert forecast.forecast_month_end(daily_cents, date(2026, 11, 10)) == Decimal("600")


def test_leap_year_month_end():
    assert forecast.forecast_month_end({"2028-02-01": 1000}, date(2028, 2, 10)) == Decimal("29")
    assert forecast.forecast_month_end({"2028-02-01": 1000}, date(2028, 2, 29)) == Decimal("10")


def test_simulation_treats_equal_to_budget_as_within_budget():
    daily_cents = {f"2026-11-{day:02}": 1_000 for day in range(1, 11)}
    result = forecast.simulate_month_end(daily_cents, date(2026, 11, 10), Decimal("300"))
    assert result == {"lower": Decimal("300"), "upper": Decimal("300"), "chance_over": 0.0}
    result = forecast.simulate_month_end(daily_cents, date(2026, 11, 10), Decimal("299.99"))
    assert result["chance_over"] == 1.0


def test_simulation_varies_with_sampled_days_and_is_reproducible():
    daily_cents = {"2026-11-02": 8_000, "2026-11-10": 12_000}
    cutoff = date(2026, 11, 10)
    result = forecast.simulate_month_end(daily_cents, cutoff, Decimal("600"))
    assert Decimal("200") <= result["lower"] < Decimal("600") < result["upper"]
    assert 0 < result["chance_over"] < 1
    assert result == forecast.simulate_month_end(daily_cents, cutoff, Decimal("600"))


def test_backtest_uses_later_days_only_for_actual_and_skips_partial_month():
    daily_cents = {"2026-10-02": 10_000, "2026-10-11": 25_000, "2026-11-04": 10_000}
    results = forecast.backtest(daily_cents, date(2026, 10, 1), date(2026, 11, 10))
    assert results == [{"month": "2026-10", "forecast": Decimal("310"),
                        "actual": Decimal("350"), "absolute_error": Decimal("40")}]


def test_sql_aggregation_and_forecast_menu(monkeypatch, capsys):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 11)

    monkeypatch.setattr(budget, "Date", FixedDate)
    for when, amount in [("2026-10-03", "100"), ("2026-10-25", "250"),
                         ("2026-11-02", "80"), ("2026-11-02", "20"),
                         ("2026-11-10", "100"), ("2026-11-11", "50")]:
        storage.save_expense(dict(date=when, category="Groceries", description="Demo", amount=amount))
    storage.save_monthly_budget("2026-11", Decimal("800"))
    assert storage.load_daily_spending(date(2026, 11, 1), date(2026, 11, 10)) == {
        "2026-11-02": 10_000, "2026-11-10": 10_000,
    }
    answers = iter(["11", "2026-11-10", "12", "2026-10", "4"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    budget.main()
    output = capsys.readouterr().out
    assert "Baseline month-end estimate: $600.00" in output
    assert "Simulated chance of exceeding $800.00" in output
    assert "Mean absolute error across 1 month(s): $40.00" in output
