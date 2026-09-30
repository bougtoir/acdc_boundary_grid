import pandas as pd

from acdc_boundary.analysis import classify_model_discrepancy


def test_discrepancy_screening_separates_three_declared_categories() -> None:
    keys = [
        {
            "feeder": "toy",
            "topology": "original",
            "portfolio": "K3",
            "native_dc_share": share,
            "seed": 1,
            "converter_efficiency": 0.98,
        }
        for share in (0.0, 0.5, 1.0)
    ]
    rows = []
    for key in keys:
        rows.append(
            {
                **key,
                "case": "all_ac_conductor",
                "total_loss_kwh": 100.0,
                "objective": 100.0,
                "architecture": "all-AC",
            }
        )
    for key, loss, architecture in zip(
        keys,
        (100.0, 90.0, 99.0),
        ("all-AC", "hybrid", "hybrid"),
        strict=True,
    ):
        rows.append(
            {
                **key,
                "case": "hybrid_joint",
                "total_loss_kwh": loss,
                "objective": loss,
                "architecture": architecture,
            }
        )
    classified, _ = classify_model_discrepancy(
        pd.DataFrame(rows),
        pd.DataFrame([{"feeder": "toy", "relative_error": 0.02}]),
    )
    assert classified.classification_feeder_threshold.tolist() == [
        "no modeled loss benefit/AC retained",
        "robustly material under screening rule",
        "indeterminate relative to model discrepancy",
    ]
