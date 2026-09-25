# Phase R04 Handoff — Code-Matching Formulation

## Status

**PASS**

## Implemented

- Defined the rooted tree, domains, edge-domain convention, endpoint native-DC
  shares, conductor multipliers, converter boundaries, and scenario scaling.
- Specified AC/DC current, resistance, annual line loss, endpoint conversion,
  boundary efficiency/standby loss, material index, converter-capacity index,
  total electrical loss, and regularized objective.
- Specified the exact DP state, recursion, child transition, root termination,
  backtracking, tie order, and analytical complexity.
- Stated that ampacity and voltage-drop limits are post-optimization diagnostics,
  not feasibility constraints.
- Limited exactness to the fixed-profile, additive, balanced radial approximation.
- Expanded the manuscript Methods source with editable OMML equation containers;
  final professional-equation and layout QC remains scheduled for R20.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary/model.py src/acdc_boundary/manuscript.py
All checks passed

.venv/bin/pytest -q tests/test_model.py
6 passed
```

## Files changed

- `src/acdc_boundary/model.py`
- `src/acdc_boundary/manuscript.py`
- `reports/mathematical_formulation.md`

## Git

- Commit: `2b7bc0d9`
- Starting commit: `9408b84e`

## Unresolved issues

The final manuscript still requires the full result hierarchy, professional Word
equation rendering, discrepancy classification, and final page-format audit. Those
are assigned to R8 and R13–R20.
