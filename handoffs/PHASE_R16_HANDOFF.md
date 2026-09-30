# Phase R16 Handoff — Citation and Fabrication Audit

## Status

**PASS**

## Evidence

- DOI/title/author metadata are checked against preserved Crossref and Figshare records.
- Every configured reference is called out, and first appearances are numbered in order.
- Figure and table callouts precede their captions; table captions are above tables.
- Scientific scalars are accepted only through `results/manuscript_values.csv`.
- The exact requested audit name is `qc/fabrication_audit_revision.md`.

## Commands

```text
make qc
```

## Git

- Scientific implementation: `4bb4e3c5`
- Current merge baseline: `a8034203`

## Unresolved

Human authors must still verify the final bibliography and declarations before submission.
