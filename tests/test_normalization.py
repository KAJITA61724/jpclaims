import pandas as pd
import pytest

from jpclaims.exceptions import SchemaValidationError
from jpclaims.normalization import normalize_events


def test_normalize_japanese_columns():
    patients = pd.DataFrame(
        {
            "加入者id": ["P1"],
            "加入者性別": [1],
            "加入者生年月": [201806],
            "観察開始年月": [202001],
            "観察終了年月": [202412],
            "保険種別": ["組合"],
            "家族id": ["F1"],
            "本人家族": ["家族"],
            "続柄": ["子"],
            "観察終了理由(死亡)フラグ": [0],
        }
    )
    events = normalize_events(patients=patients, validate=True)
    assert "person_id" in events["person"].columns
    assert events["person"]["person_id"].iloc[0] == "P1"


def test_missing_required_raises():
    with pytest.raises((ValueError, SchemaValidationError)):
        normalize_events(
            patients=pd.DataFrame({"person_id": ["P1"]}),
            validate=True,
        )
