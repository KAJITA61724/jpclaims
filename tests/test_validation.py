import pandas as pd
import pytest

from jpclaims.exceptions import SchemaValidationError
from jpclaims.validation import validate_person


def test_person_validation_issues(fake_person):
    issues = validate_person(fake_person)
    assert issues == {}


def test_invalid_observation_window():
    df = pd.DataFrame(
        {
            "person_id": ["P1"],
            "observation_start_ym": [202412],
            "observation_end_ym": [202001],
        }
    )
    issues = validate_person(df)
    assert "observation_start_after_end" in issues
