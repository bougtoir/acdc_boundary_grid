# Phase R01 Handoff — Baseline Freeze

## Status

**CONDITIONAL PASS**

The scientific baseline reproduced exactly at machine precision. Rebuilt DOCX, PDF,
cover-letter DOCX, and ZIP bytes differ from the committed copies despite unchanged
scientific content; this artifact-level nondeterminism is retained as an explicit R17
reproducibility issue rather than silently ignored.

## Recoverable checkpoint

- Baseline commit: `c6ce46d8db8974c0ceb6e5515ac143221045980a`
- Annotated tag: `acdc-boundary-pre-revision-20260924`
- Baseline-manifest commit: `f77df60d`
- Manifest: `qc/revision_baseline_manifest.csv` (98 files plus header)

## Commands run

```text
make acquire
make all
make test
make lint
make qc
```

Results: six tests passed; Ruff passed; QC passed; PDF was four US-Letter pages.

## Reproduced central values

| Registry value | Reproduced |
|---|---:|
| Mean joint-hybrid vs conductor-optimized AC loss change | -11.1733892911% |
| Median pandapower line-loss discrepancy | 1.4082432780% |
| Factorial rows | 7,200 |
| Joint all-AC / hybrid / root-DC selection | 62.2917% / 27.7083% / 10.0000% |
| Paired loss-change median | 0.0000% |
| Paired loss-change 5th–95th percentile | -46.6278266468% to 0.0000% |

All values agree with the frozen handoff values at the displayed precision and are
read from `results/manuscript_values.csv`, not manually substituted in analysis code.

## Files changed

- Added `qc/revision_baseline_manifest.csv`.
- The canonical baseline build regenerated the manuscript DOCX/PDF, cover-letter DOCX,
  and submission ZIP. These four generated binaries remain modified in the working tree
  pending deterministic artifact handling and the substantive revision rebuild.

## Unresolved issue

The generated document containers and PDF include build-dependent bytes. Scientific
CSV outputs and PNG/TIFF figures remained byte-identical. R17 must either make the
documents deterministic or explicitly define reproducibility at the extracted-content
level while preserving exact deterministic scientific outputs.
