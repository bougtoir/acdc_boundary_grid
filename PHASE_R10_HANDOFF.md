# Phase R10 Handoff — Computational Performance

## Status

**PASS**

## Implemented

The run records the VM platform, processor, logical CPU count, memory, Python
and scientific-package versions, peak process resident set size, full
factorial runtime, ablation runtime, feeder size, DP state/transition counts,
and repeated solve timings.

On this two-vCPU VM, the 7,200-row factorial took 17.3 s and the 11,520-row
converter ablation took 30.0 s. Median joint-solve time ranged from 0.32 ms for
the 14-bus original rural feeder to 1.53 ms for the 58-bus synthetic urban
feeder.

Independent chain enumeration covered 4 through 16,384 combined
domain/conductor designs. Production-DP objective error remained below
`6e-14`; recorded DP states grew from 3 to 15 while exhaustive design counts
grew from 4 to 16,384.

The report pairs these timings with the declared
`O(|E||D|^2|S|)` analytical work bound and does not infer asymptotic
superiority from timing alone.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary/performance.py
All checks passed

make all
completed successfully
```

## Files changed

- `results/computational_environment.csv`
- `results/feeder_runtime_benchmark.csv`
- `results/toy_scaling_benchmark.csv`
- `tables/table_computational_performance.csv`
- `reports/computational_performance.md`

## Git

- Implementation commit: `b219e738`
- Starting commit: `a14d4819`

## Unresolved issues

Wall-clock measurements are environment-specific implementation evidence, not
hardware-independent complexity proof. Peak memory is process-wide rather than
an isolated per-solve allocation measurement.
