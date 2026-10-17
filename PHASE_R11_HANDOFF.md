# Phase R11 Handoff — Nonlinear AC Validation Stress Checks

## Status

**PASS WITH DECLARED SCOPE**

## Implemented

The original pandapower balanced all-AC validation is retained. A reproducible
stress check applies the four configured portfolio peak multipliers to the
same peak snapshot in both the nonlinear pandapower model and the screening
loss approximation.

All 12 feeder/portfolio cases converged. Across the stress grid:

- minimum voltage remained at or above 0.983 pu;
- maximum line loading remained below 49%;
- absolute relative line-loss discrepancy remained at or below 2.591%.

The validation denominator, convergence state, voltage, and loading are
recorded in machine-readable outputs.

No unvalidated hybrid AC/DC OPF was added. The report explicitly limits the
evidence to balanced all-AC loss approximation and describes the hybrid model
as a screening/attribution approximation that does not validate converter
controls, unbalance, harmonics, grounding, or protection.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary/validation.py
All checks passed

make all
completed successfully
```

## Files changed

- `results/validation_results.csv`
- `results/validation_stress_results.csv`
- `tables/table_2_validation.csv`
- `tables/table_validation_stress.csv`
- `reports/validation_stress.md`

## Git

- Implementation commit: `95869464`
- Starting commit: `2531cea9`

## Unresolved issues

High-fidelity hybrid-network validation remains unavailable. This limitation
must remain explicit in the manuscript and conclusion.
