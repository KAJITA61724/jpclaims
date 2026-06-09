from jpclaims.qc import generate_qc_report


def test_qc_report(fake_person, fake_claims, minimal_defs):
    from jpclaims.datamart import build_patient_datamart

    dm, _ = build_patient_datamart(
        person=fake_person,
        claim=fake_claims,
        code_definitions=minimal_defs,
        return_report=True,
    )
    report = generate_qc_report(
        input_tables={"person": fake_person, "claim": fake_claims},
        output=dm,
        code_definitions=minimal_defs,
    )
    assert report["output_row_count"] == 3
    assert report["code_definition_hash"]
    assert "definition_hit_counts" in report
