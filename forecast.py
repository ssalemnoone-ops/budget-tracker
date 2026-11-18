"""Month-end forecasts from daily totals in integer cents."""
from calendar import monthrange
from datetime import timedelta
from decimal import Decimal

import numpy as np


SIMULATIONS = 5_000
MIN_SIMULATION_DAYS = 7
BACKTEST_DAY = 10


def _observed_days(daily_cents, as_of):
    """Include one value for each elapsed calendar day, even without purchases."""
    return [
        daily_cents.get(as_of.replace(day=day).isoformat(), 0)
        for day in range(1, as_of.day + 1)
    ]


def forecast_month_end(daily_cents, as_of):
    """Project the observed daily average through month end, in dollars."""
    observed = _observed_days(daily_cents, as_of)
    days_in_month = monthrange(as_of.year, as_of.month)[1]
    return Decimal(sum(observed) * days_in_month) / (100 * as_of.day)


def simulate_month_end(daily_cents, as_of, budget=None, *, seed=0):
    """Resample observed daily totals to estimate a range and overspend chance."""
    if as_of.day < MIN_SIMULATION_DAYS:
        raise ValueError(f"Log at least {MIN_SIMULATION_DAYS} calendar days before simulating.")
    observed = _observed_days(daily_cents, as_of)
    spent = sum(observed)
    days_remaining = monthrange(as_of.year, as_of.month)[1] - as_of.day

    # Each simulation is an integer-cent total. Guard against NumPy integer overflow.
    if max(max(observed), spent + days_remaining * max(observed)) > np.iinfo(np.int64).max:
        raise ValueError("Spending is too large for the simulation.")
    rng = np.random.default_rng(seed)
    samples = rng.choice(
        np.asarray(observed, dtype=np.int64),
        size=(SIMULATIONS, days_remaining),
        replace=True,
    )
    totals = spent + samples.sum(axis=1)
    # Use observed simulation outcomes as the percentile endpoints.
    lower, upper = np.percentile(totals, [10, 90], method="inverted_cdf")
    chance_over = None
    if budget is not None:
        budget_cents = int(budget * 100)
        chance_over = float((totals > budget_cents).mean())

    return {
        "lower": Decimal(int(lower)) / 100,
        "upper": Decimal(int(upper)) / 100,
        "chance_over": chance_over,
    }


def backtest(daily_cents, first_month, last_completed_day):
    """Compare day-10 forecasts with actual totals for fully logged months."""
    results = []
    month = first_month.replace(day=1)
    while month <= last_completed_day:
        days = monthrange(month.year, month.month)[1]
        month_end = month.replace(day=days)
        if month_end > last_completed_day:
            break
        predicted = forecast_month_end(daily_cents, month.replace(day=BACKTEST_DAY))
        actual = Decimal(sum(_observed_days(daily_cents, month_end))) / 100
        results.append({
            "month": month.isoformat()[:7],
            "forecast": predicted,
            "actual": actual,
            "absolute_error": abs(predicted - actual),
        })
        if month_end == last_completed_day:
            break
        month = month_end + timedelta(days=1)
    return results
