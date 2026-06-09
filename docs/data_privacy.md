# Data Privacy

## Policy

The `jpclaims` repository must **never** contain:

- Real patient-level claims data
- Raw claims extracts from vendors or insurers
- Commercial code masters (drug, disease, procedure dictionaries)
- Environment files with credentials (`.env`, API keys)
- Small-cell tables or aggregates that could enable re-identification
- Internal study outputs with real patient counts or proprietary metrics

## Allowed data

Only **synthetic / fake data** may be committed:

- `examples/sample_data/*.csv` — fictional patient IDs (`P001`, etc.)
- `tests/fixtures/*.csv` — minimal test fixtures
- Dummy code definitions in YAML (no real prevalence or hit rates)

## Before every commit

1. Run `git status` and review all staged files
2. Confirm no paths under `data/`, `raw/`, `outputs/`, or `project/outputs/`
3. Confirm CSV files are only under `examples/sample_data/` or `tests/fixtures/`
4. Confirm no `.parquet`, `.pkl`, `.xlsx` artifacts

## If real data was accidentally committed

1. Do **not** push to a public remote
2. Remove the file from git history before public release
3. Rotate any exposed credentials
4. Document the incident per your institution's policy
