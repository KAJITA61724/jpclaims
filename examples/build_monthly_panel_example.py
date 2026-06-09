"""Example: build monthly panel."""

from pathlib import Path

import pandas as pd

from jpclaims import build_monthly_panel, load_code_definitions, normalize_events

EXAMPLES = Path(__file__).resolve().parent


def main() -> None:
    data_dir = EXAMPLES / "sample_data"
    defs = load_code_definitions(EXAMPLES / "minimal_code_definitions.yaml")
    events = normalize_events(
        patients=pd.read_csv(data_dir / "patients.csv"),
        claims=pd.read_csv(data_dir / "claims.csv"),
        diagnoses=pd.read_csv(data_dir / "diagnoses.csv"),
        medications=pd.read_csv(data_dir / "medications.csv"),
        procedures=pd.read_csv(data_dir / "procedures.csv"),
    )
    panel = build_monthly_panel(
        person=events["person"],
        claim=events["claim"],
        condition_event=events["condition_event"],
        drug_event=events["drug_event"],
        procedure_event=events["procedure_event"],
        code_definitions=defs,
    )
    panel.to_parquet(EXAMPLES / "monthly_panel.parquet", index=False)
    print(panel.head())


if __name__ == "__main__":
    main()
