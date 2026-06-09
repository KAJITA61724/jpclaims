"""Observation and index window utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from jpclaims.dates import add_months, months_between, ym_to_int, ym_to_month_index


WindowScope = Literal[
    "all",
    "observation_period",
    "baseline",
    "followup",
    "washout",
    "index",
    "index_window",
    "custom",
]


@dataclass
class WindowSpec:
    scope: WindowScope
    months: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    start_ym: int | None = None
    end_ym: int | None = None


def define_observation_window(person: pd.DataFrame) -> pd.DataFrame:
    out = person.copy()
    out["observed_months"] = months_between(
        out["observation_start_ym"], out["observation_end_ym"]
    ).astype(int)
    return out


def filter_by_observation_window(
    events: pd.DataFrame,
    person: pd.DataFrame,
    month_col: str = "event_month",
) -> pd.DataFrame:
    obs = person.set_index("person_id")[["observation_start_ym", "observation_end_ym"]]
    merged = events.merge(obs, left_on="person_id", right_index=True, how="left")
    start = ym_to_int(merged["observation_start_ym"])
    end = ym_to_int(merged["observation_end_ym"])
    month = ym_to_int(merged[month_col])
    mask = month.ge(start) & month.le(end)
    return merged.loc[mask].drop(columns=["observation_start_ym", "observation_end_ym"])


def filter_by_index_window(
    events: pd.DataFrame,
    index_dates: pd.DataFrame,
    start_offset: int,
    end_offset: int,
    month_col: str = "event_month",
) -> pd.DataFrame:
    idx = index_dates.rename(columns={"index_ym": "index_month"})[
        ["person_id", "index_month"]
    ]
    merged = events.merge(idx, on="person_id", how="inner")
    rel = ym_to_month_index(merged[month_col]) - ym_to_month_index(merged["index_month"])
    return merged.loc[rel.between(start_offset, end_offset)].drop(columns=["index_month"])


def make_lookback_window(index_ym: pd.Series, months: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start_ym": add_months(index_ym, -months),
            "end_ym": add_months(index_ym, -1),
        }
    )


def make_followup_window(index_ym: pd.Series, months: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start_ym": add_months(index_ym, 1),
            "end_ym": add_months(index_ym, months),
        }
    )


def check_continuous_enrollment(person: pd.DataFrame, required_months: int) -> pd.Series:
    observed = months_between(person["observation_start_ym"], person["observation_end_ym"])
    return observed.ge(required_months).astype(int)


def compute_window_availability(person: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    windows = windows or [3, 6, 12, 24]
    out = person[["person_id"]].copy()
    observed = months_between(person["observation_start_ym"], person["observation_end_ym"])
    for n in windows:
        out[f"baseline_{n}m_available_flag"] = observed.ge(n).astype(int)
        out[f"followup_{n}m_available_flag"] = observed.ge(n).astype(int)
        out[f"washout_{n}m_available_flag"] = observed.ge(n).astype(int)
    return out


def months_from_obs_start(person: pd.DataFrame, event_first_ym: pd.Series) -> pd.Series:
    obs = person.set_index("person_id")["observation_start_ym"]
    aligned_obs = person["person_id"].map(obs)
    return ym_to_month_index(event_first_ym) - ym_to_month_index(aligned_obs)
