# Phase R07 Handoff — Full-Factorial Architecture Analysis

## Status

**PASS**

## Implemented

All 7,200 canonical rows are summarized by feeder, topology, K0–K3
portfolio, native-DC share, frozen spatial allocation, converter efficiency,
and design case. The 1,440 joint-optimization cells include:

- 897 all-AC cells;
- 399 hybrid cells;
- 144 root-converted-DC cells.

The machine-readable outputs report DC-assigned bus and energy fractions,
paired electrical-loss contrasts, distinct boundary signatures, and
native-DC-share transition sequences. At 94% and 96% boundary efficiency every
sampled joint cell retained all-AC; hybrid and root-converted designs appeared
only in the 98% and 99% scenario levels.

The structural-repetition output explicitly identifies design-grid
frequencies and frozen spatial allocations as sensitivity samples rather than
independent statistical replications or real-world probabilities.

## Verification

```text
make all
completed successfully

Joint rows: 1440
All-AC/hybrid/root-DC: 897/399/144
```

## Files changed

- `results/factorial_architecture_summary.csv`
- `results/factorial_transition_locations.csv`
- `results/factorial_structure.csv`
- `tables/table_factorial_architectures.csv`
- `reports/factorial_analysis.md`

## Git

- Implementation commit: `3fe51ec9`
- Starting commit: `ed2add29`

## Unresolved issues

These sampled-grid frequencies cannot be interpreted as deployment
probabilities. Manuscript integration remains assigned to R13–R15.
