# Reproducibility audit

Raw source verification:
```json
[
  {
    "dataset_id": "simbench-1.6.1-wheel",
    "exists": true,
    "sha256_match": true
  },
  {
    "dataset_id": "ev-charging-22495141-v1",
    "exists": true,
    "sha256_match": true
  }
]
```

- Scenario results SHA-256: `ec9231ca36644a8c863dda8b2c5d8b4e9946cb4147fc7d02b579f358688835d5`
- Manuscript values SHA-256: `bb2f5d1bf013c084842b95db98d239fba049197546a867e2f3724b38ad5f810f`
- Deterministic seeds are frozen in `configs/analysis_plan.yaml`.
- Analytical unit tests cover AC loss, AC-only feasibility, and ideal-boundary selection.
- Stored dynamic-programming exactness cases pass independently: True
- Large raw source objects are preserved locally and excluded from Git.
- Reproduction commands are `make setup`, `make acquire`, `make all`, `make test`, and `make qc`.

Decision: PASS
