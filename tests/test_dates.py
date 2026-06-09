from jpclaims.dates import add_months, months_between, ym_to_int
import pandas as pd


def test_add_months():
    ym = pd.Series([202011])
    assert int(add_months(ym, 2).iloc[0]) == 202101


def test_months_between_inclusive():
    assert int(months_between(pd.Series([202001]), pd.Series([202003])).iloc[0]) == 3
