# Phase R17 Handoff — Clean Reproducibility

## Status

**PASS WITH DOCUMENTED BINARY VARIANCE**

## Evidence

- Acquisition, analysis, manuscript, tests, and QC run through the canonical Make targets.
- Raw-data size and SHA-256 checks pass against the persistent provenance ledger.
- Deterministic scientific CSVs and figures reproduce from frozen inputs and seeds.
- Live timing/RSS values and LibreOffice PDF metadata are intentionally documented as
  non-byte-deterministic rather than treated as scientific discrepancies.
- The exact requested audit name is `qc/reproducibility_audit_revision.md`.

## Commands

```text
make setup
make acquire
make all
make test
make qc
```

## Git

- Scientific implementation: `4bb4e3c5`
- Current merge baseline: `a8034203`

## Unresolved

Gate T human metadata and an optional archival DOI remain outside automated reproduction.
