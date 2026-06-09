import pandas as pd
import pytest

from jpclaims.dates import months_between, months_diff, ym_to_int
from jpclaims.exceptions import SchemaValidationError
from jpclaims.io import preserve_string_codes
from jpclaims.validation import validate_required_columns


def test_required_columns_missing():
    df = pd.DataFrame({"person_id": ["P1"]})
    with pytest.raises(SchemaValidationError):
        validate_required_columns(df, "person")


def test_month_diff():
    start = pd.Series([202001])
    end = pd.Series([202003])
    assert int(months_diff(start, end).iloc[0]) == 2
    assert int(months_between(start, end).iloc[0]) == 3


def test_code_string_preservation():
    df = pd.DataFrame({"procedure_code": ["0123", "160180410"]})
    out = preserve_string_codes(df, "procedure_event")
    assert out["procedure_code"].iloc[0] == "0123"
