# Feature Engineering

## Output model

`build_patient_datamart()` produces **one row per patient** (left join from `person`).

## Naming convention

| Prefix | Domain | Example columns |
|--------|--------|-----------------|
| `dx_` | Diagnosis | `dx_diabetes_flag_obs`, `dx_diabetes_first_ym_obs` |
| `med_` | Medication | `med_steroid_total_days_obs`, `med_steroid_new_user_flag` |
| `proc_` | Procedure | `proc_dialysis_total_points_obs` |
| `combo_` | Co-occurrence | `combo_dx_med_same_month_flag_obs` |

### Suffixes

| Suffix | Meaning |
|--------|---------|
| `_flag_obs` | Any event in observation period (0/1 int) |
| `_count_obs` | Row count in observation period |
| `_month_count_obs` | Distinct months with events |
| `_first_ym_obs` / `_last_ym_obs` | First / last YYYYMM (NA if absent) |
| `_incident_{n}m_flag` | Washout-clean new onset |
| `_all` variants | Full record span including outside observation |

## Missing value policy

- Flags → `0` (int)
- Counts → `0` (int)
- First / last year-month → **NA** (never zero-filled)
- Continuous checkup values → NA

## Windows

Observation, baseline, follow-up, and washout windows are first-class concepts. See `jpclaims.windows` for:

- `define_observation_window`
- `filter_by_observation_window`
- `filter_by_index_window`
- `compute_window_availability`

## Monthly panel

`build_monthly_panel()` expands to person × month with:

- `monthly_visit_flag`, `monthly_visit_count`, `monthly_cost`
- `monthly_dx_{group}_flag`, `monthly_med_{group}_flag`, etc.

## QC integration

Every datamart build can return a QC dict with row counts, retention, flag rates, definition hit counts, and `code_definition_hash`.
