from datetime import date
from decimal import Decimal

import numpy as np

from evaluate_forecasts import CUTOFFS, YEAR, evaluate, generate_expenses, summarize


def test_synthetic_year_is_reproducible_and_has_zero_days_and_recurring_bills():
    expenses = generate_expenses()
    assert expenses == generate_expenses()
    assert expenses != generate_expenses(seed=42)
    days_with_spending = {row['date'] for row in expenses}
    assert 0 < len(days_with_spending) < 365
    assert all(row['date'].startswith(str(YEAR)) for row in expenses)
    rent = [row for row in expenses if row['description'] == 'Synthetic rent']
    assert len(rent) == 12
    assert all(row['date'].endswith('-01') and row['amount'] == Decimal('900')
               for row in rent)


def test_cutoff_forecasts_cannot_see_future_transaction_changes():
    early = {'date': date(YEAR, 1, 2).isoformat(), 'category': 'Groceries',
             'description': 'Test early', 'amount': Decimal('100')}
    late = {'date': date(YEAR, 1, 25).isoformat(), 'category': 'Shopping',
            'description': 'Test later', 'amount': Decimal('50')}
    original = evaluate([early, late])
    changed = evaluate([early, {**late, 'amount': Decimal('500')}])
    assert len(original) == 48
    assert {row['cutoff_day'] for row in original} == set(CUTOFFS)
    for before, after in zip(original[:4], changed[:4]):
        assert before['forecast'] == after['forecast']
        assert before['lower'] == after['lower']
        assert before['upper'] == after['upper']
        assert after['actual'] - before['actual'] == 450
    assert np.isclose(original[0]['forecast'], 100 * 31 / 7)
    summary = summarize(original)
    assert all(row['months'] == 12 for row in summary)
    for metrics in summary:
        rows = [row for row in original if row['cutoff_day'] == metrics['cutoff_day']]
        hits = sum(row['lower'] <= row['actual'] <= row['upper'] for row in rows)
        assert metrics['coverage'] == hits / 12
        assert metrics['mae'] >= 0
        assert metrics['mean_interval_width'] >= 0
