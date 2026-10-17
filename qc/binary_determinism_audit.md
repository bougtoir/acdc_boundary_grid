# Binary determinism audit

## Deterministic components

- Office and submission archives use sorted entries, fixed 1980 timestamps, fixed
  compression, and normalized ZIP metadata.
- The submission ZIP is byte-stable when its inputs are unchanged.
- Scientific scenario, attribution, exactness, discrepancy, ablation, and nonlinear
  validation results are deterministic under the frozen configuration and seeds.

## Intentionally variable components

- Runtime, peak resident memory, and repeated-solve timing are measured on each run and
  therefore legitimately change with machine load.
- Those measured values are registry-backed and flow into the computational-performance
  report, manuscript, DOCX, PDF, and submission ZIP.
- LibreOffice PDF conversion may also write producer-level binary metadata that is not
  scientifically meaningful.

## Decision

Full-pipeline byte identity is not an acceptance criterion because it would require
freezing measured performance evidence or post-processing the PDF. Reproducibility is
instead established by frozen inputs and seeds, raw-data checksums, deterministic
scientific outputs, the scalar registry, source-controlled generators, and cross-file
QC. No frozen scientific result is silently replaced.
