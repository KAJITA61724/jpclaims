"""Composite and recipe-driven features."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_composite_features(
    features: pd.DataFrame,
    composite_definitions: dict[str, Any],
) -> pd.DataFrame:
    out = features.copy()
    for name, definition in composite_definitions.items():
        logic = definition.get("logic", "OR").upper()
        components = definition.get("components", [])
        present = [c for c in components if c in out.columns]
        if not present:
            out[name] = 0
            continue
        block = out[present].fillna(0)
        if logic == "OR":
            out[name] = (block.max(axis=1) > 0).astype(int)
        elif logic == "AND":
            out[name] = (block.min(axis=1) > 0).astype(int)
        elif logic == "THRESHOLD":
            threshold = int(definition.get("threshold", 1))
            out[name] = (block.sum(axis=1) >= threshold).astype(int)
        else:
            raise ValueError(f"Unsupported composite logic: {logic}")
    return out


def assign_exclusive_group(
    features: pd.DataFrame,
    group_name: str,
    rules: list[dict[str, Any]],
    default: str = "other",
) -> pd.DataFrame:
    out = features.copy()
    labels = pd.Series(default, index=out.index, dtype=object)
    for rule in rules:
        label = rule["label"]
        condition = rule["condition"]
        mask = _eval_simple_condition(out, condition)
        labels.loc[mask & labels.eq(default)] = label
    out[group_name] = labels
    return out


def assign_phenotype_group(
    features: pd.DataFrame,
    phenotype_definitions: dict[str, Any],
) -> pd.DataFrame:
    out = features.copy()
    for name, definition in phenotype_definitions.items():
        out = assign_exclusive_group(
            out,
            name,
            definition.get("rules", []),
            default=definition.get("default", "other"),
        )
    return out


def _eval_simple_condition(df: pd.DataFrame, condition: str) -> pd.Series:
    """Evaluate simple feature conditions like 'flag == 1' or 'a == 1 and b == 1'."""
    expr = condition.replace(" and ", " & ").replace(" or ", " | ")
    local_dict = {col: df[col] for col in df.columns}
    try:
        return pd.eval(expr, local_dict=local_dict).fillna(False)
    except Exception:
        return pd.Series(False, index=df.index)
