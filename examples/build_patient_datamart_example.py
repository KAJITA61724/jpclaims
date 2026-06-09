"""Example: build a patient datamart from CSV inputs."""

from pathlib import Path

import pandas as pd

from jpclaims import (
    build_patient_datamart,
    generate_qc_report,
    load_code_definitions,
    normalize_events,
)
from jpclaims.reports.json_report import write_json_report

EXAMPLES = Path(__file__).resolve().parent


def main() -> None:
    data_dir = EXAMPLES / "sample_data"
    defs = load_code_definitions(EXAMPLES / "minimal_code_definitions.yaml")

    patients = pd.read_csv(data_dir / "patients.csv")
    claims = pd.read_csv(data_dir / "claims.csv")
    diagnoses = pd.read_csv(data_dir / "diagnoses.csv")
    medications = pd.read_csv(data_dir / "medications.csv")
    procedures = pd.read_csv(data_dir / "procedures.csv")

    events = normalize_events(
        patients=patients,
        claims=claims,
        diagnoses=diagnoses,
        medications=medications,
        procedures=procedures,
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
    dm.to_parquet(EXAMPLES / "patient_datamart.parquet", index=False)
    write_json_report(report, EXAMPLES / "patient_datamart_qc.json")
    print(f"Wrote datamart with {len(dm)} rows")


if __name__ == "__main__":
    main()
