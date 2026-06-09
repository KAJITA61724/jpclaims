# Project Status

## Current release

- Package: jpclaims
- Current release: v0.1.0
- Status: Public MVP released
- License: Apache-2.0
- Python: 3.10+

## What is implemented

- Japanese claims-like raw table normalization
- Standard event model
- YAML-driven diagnosis, medication, procedure definitions
- Observation window handling
- Washout/incident flag support
- Same-month and same-claim co-occurrence
- Patient-level datamart
- Monthly panel
- Utilization and cost features
- Health checkup latest-value features
- Composite features
- Exclusive group assignment
- QC report
- Synthetic examples
- GitHub Actions test workflow

## What is intentionally not included

- Real claims data
- Proprietary master files
- Patient-identifiable information
- Commercial code dictionaries
- Clinical validation of phenotype definitions
- Clinical decision support

## Known limitations

- PDC/MPR is simplified or experimental
- DPC episode handling is minimal
- HTML QC report is minimal
- OMOP export is not implemented
- Polars/DuckDB/Spark backends are not implemented
- APIs may change before v1.0

## Next possible milestones

### v0.1.x

- Documentation refinements
- More synthetic tests
- More examples

### v0.2

- PDC/MPR
- DPC episode support
- richer HTML QC
- Elixhauser framework
- OMOP export helper
- DuckDB/Polars support

### v0.3

- large-scale processing
- Spark backend
- phenotype library
- cost trajectory features
