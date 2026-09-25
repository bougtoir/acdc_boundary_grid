# Phase R12 Handoff — Manuscript Scalar Registry

## Status

**PASS**

## Implemented

The pipeline now writes a 206-entry scalar registry covering the frozen
configuration, central feeder attribution, full-factorial architecture
counts, model-discrepancy screening, converter ablations, nonlinear
validation, exactness checks, and computational performance.

Every entry records a stable identifier, value, units, scenario, uncertainty
or interpretation, source file, generator, and version. The registry audit
fails on duplicate identifiers, missing required fields, or missing source
files.

## Verification

```text
.venv/bin/ruff check src/acdc_boundary/pipeline.py
All checks passed

.venv/bin/pytest -q
10 passed, 14 warnings

make all
completed successfully

qc/scalar_registry_audit.md
PASS: 206 unique identifiers, no missing fields or sources
```

## Files changed

- `src/acdc_boundary/pipeline.py`
- `results/manuscript_values.csv`
- `results/manuscript_scalar_registry.csv`
- `qc/scalar_registry_audit.md`
- regenerated performance records and submission artifacts

## Git

- Implementation commit: `100c5de7`
- Starting commit: `51f6b476`

## Unresolved issues

The manuscript generator must be refactored in R13 so every reported
scientific scalar is loaded from this registry rather than recomputed or
manually embedded in manuscript prose.
