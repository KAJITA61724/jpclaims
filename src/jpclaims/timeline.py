"""Patient timeline helpers."""

from __future__ import annotations

import pandas as pd

from jpclaims.dates import ym_to_int
from jpclaims.windows import define_observation_window


def build_patient_timeline(person: pd.DataFrame) -> pd.DataFrame:
    """Build a person-level timeline summary from the person table."""
    out = define_observation_window(person.copy())
    out["observation_start_ym"] = ym_to_int(out["observation_start_ym"])
    out["observation_end_ym"] = ym_to_int(out["observation_end_ym"])
    if "birth_ym" in out.columns:
        out["birth_ym"] = ym_to_int(out["birth_ym"])
    return out
