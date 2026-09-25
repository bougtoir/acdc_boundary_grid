from acdc_boundary.qc import _citation_number_audit


def test_citation_audit_accepts_repeated_citations_after_first_use():
    sequence_pass, coverage_pass = _citation_number_audit(
        "First [1], then [2], then [1] again and finally [3].",
        3,
    )
    assert sequence_pass
    assert coverage_pass


def test_citation_audit_rejects_out_of_order_first_use():
    sequence_pass, coverage_pass = _citation_number_audit(
        "The second reference [2] appears before the first [1].",
        2,
    )
    assert not sequence_pass
    assert coverage_pass
