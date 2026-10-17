# Phase R08 Handoff — Approximation-Discrepancy Screening

## Status

**PASS**

## Implemented

The original all-AC benchmark discrepancies were verified as 1.106% rural,
1.958% suburban, and 1.408% urban, with 1.408% median and 1.958% maximum.
Their denominator is nonlinear pandapower AC line loss.

A conservative screening heuristic compares the magnitude of each paired
joint-versus-conductor-optimized-AC electrical-loss contrast with:

1. the matching feeder discrepancy;
2. the global maximum feeder discrepancy;
3. twice the matching feeder discrepancy.

Under the primary feeder-specific rule, the 1,440 joint cells classify as:

- 897 no modeled loss benefit/all-AC retained;
- 531 robustly material under the screening rule;
- 12 indeterminate relative to model discrepancy.

The global-maximum sensitivity gives 897/525/18, and the doubled-feeder
sensitivity gives 897/513/30. The report states explicitly that this is not a
confidence interval, hypothesis test, or formal uncertainty propagation.

## Verification

```text
.venv/bin/pytest -q tests/test_analysis.py
1 passed

make all
completed successfully
```

## Files changed

- `results/model_discrepancy_classification.csv`
- `tables/table_model_discrepancy_classification.csv`
- `reports/model_discrepancy_classification.md`

## Git

- Implementation commit: `e6c93083`
- Starting commit: `23769269`

## Unresolved issues

The threshold transfers an AC-validation percentage to paired total modeled
electrical-loss contrasts and is therefore a transparent conservative screen,
not a calibrated hybrid-model error bound.
