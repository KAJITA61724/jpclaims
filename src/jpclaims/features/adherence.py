"""Placeholder modules for v0.2 extensions."""

from __future__ import annotations

import pandas as pd


def build_adherence_features(*args, **kwargs) -> pd.DataFrame:
    return pd.DataFrame()


def build_health_checkup_features(checkup_event: pd.DataFrame | None, person: pd.DataFrame) -> pd.DataFrame:
    out = person[["person_id"]].copy()
    if checkup_event is None or checkup_event.empty:
        return out
    numeric_cols = ["bmi", "waist", "sbp", "dbp", "hba1c", "fpg", "ldl", "hdl", "tg", "ast", "alt", "ggtp", "egfr"]
    present = [c for c in numeric_cols if c in checkup_event.columns]
    if not present:
        return out
    latest = checkup_event.sort_values("checkup_month").groupby("person_id").tail(1)
    return out.merge(latest[["person_id", *present]], on="person_id", how="left")


def build_sequence_features(*args, **kwargs) -> pd.DataFrame:
    return pd.DataFrame()
