"""Example: QC JSON report."""

from pathlib import Path

import pandas as pd

from jpclaims import build_patient_datamart, load_code_definitions, normalize_events
from jpclaims.reports.json_report import write_json_report

EXAMPLES = Path(__file__).resolve().parent


def main() -> None:
    data_dir = EXAMPLES / "sample_data"
    defs = load_code_definitions(EXAMPLES / "minimal_code_definitions.yaml")
    events = normalize_events(
        patients=pd.read_csv(data_dir / "patients.csv"),
        claims=pd.read_csv(data_dir / "claims.csv"),
        diagnoses=pd.read_csv(data_dir / "diagnoses.csv"),
    )
    _, report = build_patient_datamart(
        person=events["person"],
        claim=events.get("claim"),
        condition_event=events.get("condition_event"),
        code_definitions=defs,
        return_report=True,
    )
    write_json_report(report, EXAMPLES / "qc_report.json")
    print(report["code_definition_hash"])


if __name__ == "__main__":
    main()
