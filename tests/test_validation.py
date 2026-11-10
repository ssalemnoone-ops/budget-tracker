
import pytest

from validation import parse_amount


@pytest.mark.parametrize('bad', ['abc', '', '-1', '0', 'NaN', 'sNaN', 'inf', '-inf', '1.234'])
def test_invalid_money(bad):
    with pytest.raises(ValueError):
        parse_amount(bad)
