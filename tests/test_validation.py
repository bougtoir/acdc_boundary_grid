import pandas as pd

from acdc_boundary import validation


def test_baseline_validation_does_not_overwrite_stress_results(tmp_path, monkeypatch):
    stress_path = tmp_path / "validation_stress_results.csv"
    stress_path.write_text("full,stress,results\n", encoding="utf-8")
    benchmark = pd.DataFrame(
        [
            {
                "feeder": "toy",
                "stress_case": "benchmark_peak",
                "load_factor": 1.0,
                "pandapower_loss_kw": 1.0,
                "approximate_loss_kw": 1.0,
                "relative_error": 0.0,
                "minimum_voltage_pu": 1.0,
                "maximum_line_loading_pct": 1.0,
                "pandapower_converged": True,
            }
        ]
    )
    monkeypatch.setattr(validation, "RESULTS", tmp_path)
    monkeypatch.setattr(
        validation,
        "_calculate_all_ac_stress",
        lambda *_args, **_kwargs: benchmark,
    )

    result = validation.validate_all_ac({"toy": "unused"}, 0.95, 400.0)

    assert stress_path.read_text(encoding="utf-8") == "full,stress,results\n"
    assert "stress_case" not in result
    assert (tmp_path / "validation_results.csv").exists()
