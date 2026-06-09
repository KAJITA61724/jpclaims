# Research Cautions

## Billing data is not clinical truth

Receipt disease names reflect **billing and coding practices**, not necessarily confirmed diagnoses. Always document code lists, lookback windows, and exclusion rules in study protocols.

## Suspected diagnoses

Japanese claims include `疑いフラグ` (suspected diagnosis). Including or excluding these changes case counts materially. State your rule explicitly.

## Study design responsibilities

Researchers must define:

- Observation period start / end
- Index date (if applicable)
- Baseline and follow-up windows
- Washout for incident cases
- Outcome definitions

The library implements these rules but does not choose them.

## Information leakage

Features computed from events **after** the index date must not appear in baseline covariates. Use window filters and review feature definitions before modeling.

## Not for clinical use

`jpclaims` is a research preprocessing tool. It must not be used for:

- Individual patient diagnosis
- Treatment decisions
- Real-time clinical alerts

## Code definition validity

Example YAML files (including disease-specific samples under `examples/`) are **not validated** for any particular study. Users are responsible for:

- Code list currency (reimbursement revisions)
- Clinical face validity
- Comparison with chart review or registry data where available

## v0.1 stability

APIs, column names, and YAML schema may change before v1.0. Pin versions in production research pipelines.
