# Phase R06 Handoff — Matched Architecture Attribution

## Status

**PASS**

## Implemented

The canonical 7,200-row scenario build now records DC bus/energy fractions,
domain and boundary signatures, conductor signatures, and DP evaluation counts.
For each feeder and both original and synthetic-MST topologies, the central K3
cell reports absolute electrical losses for inherited AC, conductor-optimized
AC, fixed-conductor hybrid, joint domain/conductor hybrid, and
electrical-ideal hybrid designs.

The generated attribution table separates:

- conductor optimization versus inherited AC;
- fixed-design DC permission versus fixed-conductor AC;
- joint architecture value versus conductor-optimized AC;
- electrical-ideal conversion as an upper-bound scenario;
- synthetic-topology sensitivity versus the original benchmark.

All language is limited to modeled, incremental, or attribution contrasts.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary tests/test_analysis.py
All checks passed

.venv/bin/pytest -q
10 passed

make all
completed successfully
```

## Files changed

- `src/acdc_boundary/model.py`
- `src/acdc_boundary/analysis.py`
- `src/acdc_boundary/performance.py`
- `src/acdc_boundary/validation.py`
- `src/acdc_boundary/pipeline.py`
- `src/acdc_boundary/paths.py`
- `tests/test_analysis.py`
- `results/scenario_results.csv`
- `results/central_decomposition.csv`
- `results/phase_diagram.csv`
- `results/uncertainty_summary.csv`
- `results/feeder_attribution.csv`
- `tables/table_1_central_decomposition.csv`
- `tables/table_feeder_attribution.csv`
- `reports/feeder_attribution.md`

## Git

- Implementation commit: `bc6a79b8`
- Starting commit: `aee95e29`

## Unresolved issues

The synthetic MST is a coordinate-based sensitivity design, not observed
utility infrastructure. The manuscript integration remains assigned to R13.
