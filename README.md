# jpclaims

Python toolkit for cleaning and feature engineering Japanese health insurance claims data.

`jpclaims` normalizes vendor-specific Japanese receipt tables into a standard event model, then builds YAML-driven patient-level datamarts, monthly panels, and QC reports for epidemiological research.

## Purpose

This library is an OSS foundation for Japanese receipt research. It is **not** a simple CSV cleaner or imputation tool.

Pipeline:

1. Schema validation
2. Code normalization and matching (user-defined)
3. Patient timeline / observation windows
4. Long-format event tables
5. Washout-aware feature generation
6. QC reporting
7. Research- and ML-ready datamart output

## What this repository contains

| Included | Not included |
|----------|--------------|
| Library source code | Real receipt extracts |
| Synthetic `examples/sample_data/` | Commercial code masters |
| Example YAML definitions | Patient-identifiable data |
| Documentation | Study-specific aggregate tables |

**Diagnosis codes, drug codes, and procedure codes are never hardcoded in the library.** Users supply definitions via YAML, JSON, or CSV.

Study-specific examples (e.g. `examples/fpies_feature_definitions.yaml`) are **illustrative samples only**. Validity, sensitivity, and clinical appropriateness must be verified by each user. See `examples/README.md`.

## Important Notes

- This package does not include real patient-level claims data.
- This package does not include proprietary master files or code dictionaries.
- Users must provide their own diagnosis, drug, procedure, and master code definitions.
- Claims diagnoses are billing diagnoses and may not represent clinically confirmed diagnoses.
- Researchers should explicitly define suspected diagnosis handling, observation windows, washout periods, index dates, and outcome definitions.
- Do not use post-index information when constructing baseline features.
- This package is intended for research preprocessing and feature engineering, not for clinical decision-making.
- v0.1 is an early release; APIs may change before v1.0.

See also `docs/research_cautions.md` and `docs/data_privacy.md`.

## Supported input tables

- Patient master
- Medical / pharmacy claims
- Diagnoses
- Medications
- Procedures
- DPC (interface stub in v0.1)
- Health checkups
- Lab values when provided separately

## Positioning

`jpclaims` is not a competitor to OHDSI/OMOP. It is a Japan-specific preprocessing layer before optional OMOP conversion (planned v0.2+).

## Installation

Requires **Python 3.10+**.

```bash
pip install -e ".[dev]"
```

## Quick start

Run from the repository root after installation:

```bash
cd jpclaims
pip install -e ".[dev]"
```

```python
import pandas as pd
from jpclaims import load_code_definitions, normalize_events, build_patient_datamart

defs = load_code_definitions("examples/minimal_code_definitions.yaml")
events = normalize_events(
    patients=pd.read_csv("examples/sample_data/patients.csv"),
    claims=pd.read_csv("examples/sample_data/claims.csv"),
    diagnoses=pd.read_csv("examples/sample_data/diagnoses.csv"),
    medications=pd.read_csv("examples/sample_data/medications.csv"),
    procedures=pd.read_csv("examples/sample_data/procedures.csv"),
)
dm, report = build_patient_datamart(
    person=events["person"],
    claim=events["claim"],
    condition_event=events["condition_event"],
    drug_event=events["drug_event"],
    procedure_event=events["procedure_event"],
    code_definitions=defs,
    return_report=True,
)
print(len(dm), report["patient_retention_check"])
# Expected: 3 1.0
```

This flow is covered by `tests/test_quickstart.py`.

### YAML definition example

See `examples/minimal_code_definitions.yaml` for generic diagnosis, medication, procedure, and co-occurrence groups.

### QC report example

```python
from jpclaims.reports.json_report import write_json_report

dm, report = build_patient_datamart(..., return_report=True)
write_json_report(report, "qc_report.json")
print(report["code_definition_hash"], report["patient_retention_check"])
```

Runnable script: `examples/build_quality_report_example.py`

## Examples

| File | Description |
|------|-------------|
| `examples/minimal_code_definitions.yaml` | Generic diabetes / hypertension / dialysis demo |
| `examples/fpies_feature_definitions.yaml` | Illustrative case-definition sample (not validated) |
| `examples/sample_data/` | Fully synthetic CSV fixtures |
| `examples/build_*_example.py` | Runnable scripts |

## Main API

```python
from jpclaims import (
    read_claims,
    load_code_definitions,
    normalize_events,
    build_patient_timeline,
    build_patient_datamart,
    build_monthly_panel,
    generate_qc_report,
    extract_cooccurring_codes,
)
```

## Documentation

- [Project status](docs/project_status.md)
- [Data privacy](docs/data_privacy.md)
- [YAML code definitions](docs/code_definition_yaml.md)
- [Feature engineering](docs/feature_engineering.md)
- [Research cautions](docs/research_cautions.md)
- [Release checklist](docs/release_checklist.md)

## Development

```bash
pytest
ruff check src tests
```

CI runs on Python 3.10, 3.11, and 3.12 (see `.github/workflows/tests.yml`).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
