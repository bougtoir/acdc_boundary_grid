# Phase R03 Handoff — Hostile Pre-Revision Review

## Status

**CONDITIONAL PASS for continuation; FAIL for submission**

The baseline science is repairable without changing frozen inputs. Three blockers,
eight major issues, eight moderate issues, and four optional improvements are recorded
in `qc/pre_revision_hostile_review.md`.

## Review lenses applied

1. TSG editor: contribution, scope, density, and claim discipline.
2. AC/DC distribution specialist: conductor/return paths, conversion, feasibility,
   and deployability limits.
3. Optimization reviewer: DP exactness, separability, ties, objective, and complexity.
4. Validation reviewer: nonlinear benchmark scope and discrepancy interpretation.
5. Reproducibility reviewer: factorial structure, registries, artifacts, and build
   determinism.

## Highest-priority findings

- Independently validate DP optima by brute-force enumeration.
- Expand the formulation to match every coded objective component and transition.
- Operationalize feeder-specific model-discrepancy thresholds.
- Replace the central cross-feeder mean emphasis with feeder-level attribution.
- Use the 1,440 joint cells and 7,200 total design rows without treating structural
  repetitions as independent replications.
- Separate converter mechanisms and add computational evidence.

## Files changed

- `qc/pre_revision_hostile_review.md`

## Git

- Review commit: `d0914219`
- Starting commit: `7d38484c`

## Unresolved issues

All feasible blocker/major/moderate corrections are assigned to R4–R23. No issue
requires new private data or human metadata, so the revision can continue.
