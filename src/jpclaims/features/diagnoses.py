"""Diagnosis feature generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from jpclaims.features._base import _aggregate_event_features


def build_diagnosis_features(
    person: pd.DataFrame,
    condition_event: pd.DataFrame | None,
    definitions: dict[str, Any],
) -> pd.DataFrame:
    blocks = []
    for group_name, definition in definitions.items():
        blocks.append(
            _aggregate_event_features(
                person, condition_event, group_name, "dx", definition
            )
        )
    if not blocks:
        return person[["person_id"]].copy()
    out = blocks[0]
    for block in blocks[1:]:
        out = out.merge(block, on="person_id", how="left")
    return out
