# Phase R05 Handoff — Independent DP Exactness Validation

## Status

**PASS**

## Implemented

An independent exhaustive enumerator evaluates every permitted domain assignment
and conductor multiplier combination without calling the production line,
endpoint, boundary, or evaluation functions.

Cases cover:

- all-AC optimum;
- root-converted all-DC optimum;
- interior hybrid optimum;
- high converter-capacity penalty;
- high endpoint-mismatch penalty;
- conductor-driven architecture change;
- explicit tied optimum.

All eight cases matched the production DP objective within
`1e-10 * max(1, |objective|)`. Every production assignment and conductor choice
belonged to the corresponding brute-force optimum set. All seven unique optima
matched architecture; the explicit tie had six optima and verified the declared
AC-then-smallest-conductor deterministic selection.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary/exactness.py \
  src/acdc_boundary/pipeline.py tests/test_model.py
All checks passed

.venv/bin/pytest -q tests/test_model.py tests/test_pipeline.py
9 passed
```

## Files changed

- `src/acdc_boundary/exactness.py`
- `src/acdc_boundary/pipeline.py`
- `src/acdc_boundary/manuscript.py`
- `tests/test_model.py`
- `results/dp_exactness_validation.csv`
- `qc/dp_exactness_validation.md`

## Git

- Commit: `7a3018fd`
- Starting commit: `10f1ebd0`

## Unresolved issues

The exactness result applies only to the declared separable screening objective.
Empirical scaling and full-feeder timing remain assigned to R10.
