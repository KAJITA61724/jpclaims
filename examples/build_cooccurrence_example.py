"""Example: co-occurring code extraction."""

from pathlib import Path

import pandas as pd

from jpclaims import extract_cooccurring_codes, load_code_definitions, normalize_events

EXAMPLES = Path(__file__).resolve().parent


def main() -> None:
    data_dir = EXAMPLES / "sample_data"
    defs = load_code_definitions(EXAMPLES / "minimal_code_definitions.yaml")
    events = normalize_events(
        patients=pd.read_csv(data_dir / "patients.csv"),
        diagnoses=pd.read_csv(data_dir / "diagnoses.csv"),
        medications=pd.read_csv(data_dir / "medications.csv"),
    )
    target_def = defs["diagnosis_groups"]["diabetes"]
    target_def["group"] = "diabetes"
    long_df = extract_cooccurring_codes(
        target_events=events["condition_event"],
        context_events=events["drug_event"],
        target_definition=target_def,
        context_code_columns=["drug_code", "atc_code"],
        scope="same_claim",
    )
    print(long_df.head())


if __name__ == "__main__":
    main()
