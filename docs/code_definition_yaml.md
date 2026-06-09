# YAML Code Definition Guide

Researchers define phenotypes and feature groups in YAML. The library reads these at runtime; nothing is hardcoded in `src/`.

## Top-level sections

| Section | Purpose |
|---------|---------|
| `diagnosis_groups` | Disease / condition flags and counts |
| `medication_groups` | Drug exposure features |
| `procedure_groups` | Procedure / test features |
| `cooccurrence_groups` | Combined events (dx × med × proc) |
| `composite_features` | OR / AND / threshold proxies |
| `exclusive_groups` | Mutually exclusive phenotype labels |
| `comorbidity_groups` | Weighted comorbidity score inputs |
| `eligibility_rules` | Cohort inclusion (optional) |

## Match types

| `match` | Behavior |
|---------|----------|
| `exact` | Full string equality |
| `prefix` | Code starts with pattern (e.g. ICD-10 prefix) |
| `contains` | Substring match on name or code |
| `regex` | Regular expression |

Combine rules with `logic: OR` or `logic: AND` under a group.

## Diagnosis example

```yaml
diagnosis_groups:
  diabetes:
    code_column: icd10_code
    codes: ["E10", "E11", "E14"]
    match: prefix
    exclude_suspected: true
    primary_only: false
    output:
      flag: true
      month_count: true
      first_month: true
      incident:
        washout_months: 6
```

### Suspected diagnoses

Set `exclude_suspected: true` to drop rows where `suspected_flag == 1`.

### Primary diagnosis only

Set `primary_only: true` to keep rows where `primary_flag == 1`.

## Medication example

```yaml
medication_groups:
  antibiotic:
    code_column: atc_code
    codes: ["J01"]
    match: prefix
    output:
      flag: true
      total_days: true
      incident:
        washout_months: 6
```

## Co-occurrence

```yaml
cooccurrence_groups:
  diabetes_med_same_claim:
    time_scope: same_claim
    components:
      - table: condition_event
        group: diabetes
      - table: drug_event
        group: antidiabetic
```

### Time scopes

| `time_scope` | Meaning |
|--------------|---------|
| `same_patient` | Ever in observation |
| `same_month` | Same calendar month |
| `same_claim` | Same `source_claim_id` |
| `within_months` | Window-based (v0.2+) |

## Composite features

```yaml
composite_features:
  acute_support:
    logic: OR
    components:
      - med_steroid_flag_obs
      - med_infusion_flag_obs
  high_burden:
    logic: threshold
    threshold: 2
    components:
      - dx_a_flag_obs
      - dx_b_flag_obs
```

## Exclusive groups

```yaml
exclusive_groups:
  pathway:
    default: other
    rules:
      - label: aligned
        condition: combo_a_b_same_month_flag_obs == 1
      - label: comparison
        condition: dx_comparison_flag_obs == 1
```

## Washout / incident flags

When `output.incident.washout_months: 6` is set, the library generates:

`{prefix}_{group}_incident_6m_flag`

Positive when the first event occurs at least 6 months after `observation_start_ym`.
