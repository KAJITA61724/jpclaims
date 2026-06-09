"""Generic code matching engine."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _normalize_codes(codes: list[Any]) -> list[str]:
    return [str(c) for c in codes]


def _match_series(values: pd.Series, codes: list[str], match: str) -> pd.Series:
    s = values.fillna("").astype(str)
    if match == "exact":
        code_set = set(codes)
        return s.isin(code_set)
    if match == "prefix":
        return s.apply(lambda v: any(v.startswith(c) for c in codes))
    if match == "contains":
        pattern = "|".join(re.escape(c) for c in codes)
        return s.str.contains(pattern, regex=True, na=False)
    if match == "regex":
        pattern = "|".join(f"({c})" for c in codes)
        return s.str.contains(pattern, regex=True, na=False)
    raise ValueError(f"Unknown match type: {match}")


def apply_match_rule(df: pd.DataFrame, rule: dict[str, Any]) -> pd.Series:
    """Apply a single match rule to a dataframe."""
    col = rule.get("code_column") or rule.get("name_column")
    if col is None:
        raise ValueError("Match rule requires code_column or name_column")
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    codes = _normalize_codes(rule.get("codes", []))
    match = rule.get("match", "exact")
    result = _match_series(df[col], codes, match)
    if rule.get("exclude_suspected") and "suspected_flag" in df.columns:
        suspected = pd.to_numeric(df["suspected_flag"], errors="coerce").fillna(0).astype(int)
        result = result & suspected.eq(0)
    if rule.get("primary_only") and "primary_flag" in df.columns:
        primary = pd.to_numeric(df["primary_flag"], errors="coerce").fillna(0).astype(int)
        result = result & primary.eq(1)
    return result


def apply_group_definition(df: pd.DataFrame, definition: dict[str, Any]) -> pd.Series:
    """Apply AND/OR logic across sub-rules in a group definition."""
    logic = definition.get("logic", "OR").upper()
    sub_rules = definition.get("rules")
    if sub_rules:
        inherited = {
            k: definition[k]
            for k in ("exclude_suspected", "primary_only")
            if k in definition
        }
        parts = [apply_match_rule(df, {**inherited, **r}) for r in sub_rules]
    else:
        parts = [apply_match_rule(df, definition)]
    if not parts:
        return pd.Series(False, index=df.index)
    if logic == "AND":
        out = parts[0]
        for p in parts[1:]:
            out = out & p
        return out
    out = parts[0]
    for p in parts[1:]:
        out = out | p
    return out


def filter_matched_rows(df: pd.DataFrame, definition: dict[str, Any]) -> pd.DataFrame:
    mask = apply_group_definition(df, definition)
    return df.loc[mask].copy()
