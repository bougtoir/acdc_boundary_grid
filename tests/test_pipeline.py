from types import SimpleNamespace

import pandas as pd
import pytest

from acdc_boundary import pipeline
from acdc_boundary.pipeline import _build_pdf, _constraint_violation_count


def test_constraint_violations_use_configured_limits():
    joint = pd.DataFrame(
        {
            "max_ampacity_fraction": [0.7, 0.9, 0.7],
            "max_single_edge_drop_pu": [0.02, 0.02, 0.04],
        }
    )
    config = {
        "ampacity_limit_fraction": 0.8,
        "voltage_drop_limit_pu": 0.03,
    }
    assert _constraint_violation_count(joint, config) == 2


def test_build_pdf_replaces_stale_output_and_checks_page_limit(tmp_path, monkeypatch):
    manuscript = tmp_path / "paper.docx"
    manuscript.write_bytes(b"docx")
    pdf_dir = tmp_path / "build/pdf"
    pdf_dir.mkdir(parents=True)
    pdf = pdf_dir / "paper.pdf"
    pdf.write_bytes(b"stale")
    monkeypatch.setattr(pipeline, "MANUSCRIPT", tmp_path)

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        if command[0] == "libreoffice":
            assert not pdf.exists()
            pdf.write_bytes(b"fresh")
            return SimpleNamespace(stdout="", stderr="")
        assert command == ["pdfinfo", str(pdf)]
        return SimpleNamespace(stdout="Pages:           4\n", stderr="")

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    assert _build_pdf(manuscript, 10) == pdf
    assert pdf.read_bytes() == b"fresh"
    with pytest.raises(RuntimeError, match="outside the allowed range"):
        _build_pdf(manuscript, 3)
