# Adversarial review — AFTER fixes

Baseline: `qc/adversarial_review_before.md` (commit 71ddbb22d baseline;
`qc/baseline_manifest_adversarial.txt`).

## Disposition of every finding

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| B1 | MAJOR | Hardcoded factorial levels/counts in manuscript builder | FIXED — Table V/VI rows, feeder loops, and Abstract counts now derive from `configs/analysis_plan.yaml` and the registry (`design_case_count`) |
| B2 | MAJOR | Unverified hand-coded novelty matrix | FIXED — moved to `configs/novelty_coding.yaml` with an explicit manual-qualitative-coding provenance field, emitted as `coding_type` column in `results/novelty_matrix.csv` |
| B3 | MAJOR | EV dataset summarized but unused | FIXED — `ev_records_valid`, `ev_median_session_energy_kwh`, `ev_p95_session_power_kw` added to the registry and cited in Methods |
| B4 | MAJOR | DC drop ±375 V bipolar convention unstated | FIXED — convention named explicitly beside the drop equation |
| B5 | MAJOR | Snapshot basis of validation not explicit | FIXED — "single peak-loading snapshot … not the annual loss-hours integral" stated next to the validation description |
| B6 | MAJOR | 4-vs-3 conductor material advantage | PARTIALLY RESOLVED — ablation table already isolates the capacity regularizer; a conductor-count ablation was NOT added (would require a new unvalidated scenario). Marked unresolved-by-design: the n(AC)=4/n(DC)=3 asymmetry remains a stated model convention, disclosed as a normalized regularizer. |
| M1 | MINOR | Table IX: 6 of 8 ablations rendered | FIXED — all 8 rows rendered |
| M2 | MINOR | QC copied old hostile review verbatim as "final" | FIXED — final file now regenerated from `adversarial_review_after.md` |
| M3 | MINOR | evaluate() recomputed conductor scales | FIXED — evaluate accepts and uses `design.conductor_scales` |
| M4 | MINOR | _edge_choice double compute | FIXED — single line_metrics call per scale |
| M5 | MINOR | "robustly material" label | KEPT with existing caveat — the label is already qualified by "under screening rule" everywhere and by the explicit non-confidence-interval disclaimer; renaming the category itself would churn all artifacts for cosmetic gain |
| G9 defect | MAJOR | Tables V/VI/VII/VIII/IX rendered with right-side columns clipped in the PDF | FIXED — fixed table layout + explicit tblGrid/cell widths; verified in rendered pages 4–5 |

## Verification after fixes

- `results/scenario_results.csv`, `results/central_decomposition.csv`,
  `results/phase_diagram.csv` are BIT-IDENTICAL to the adversarial baseline
  (SHA-256 in baseline manifest) — the model refactor changed no validated
  outcome. `manuscript_values.csv` differs only by the three added EV scalars;
  `novelty_matrix.csv` only by the `coding_type` provenance column.
- 27 tests pass (14 pre-existing + 13 new metamorphic/property tests in
  `tests/test_adversarial.py`): DP = brute force on 4 random chains; optional-DC
  and conductor optimization never worsen the objective; determinism;
  nonnegative loss components; symmetric endpoint mismatch; zero-native-DC
  penalizes every DC node; nonnegative penalties cannot reduce a fixed design's
  objective; endpoint-efficiency and boundary-efficiency monotonicity.
- Rendered DOCX pages inspected (pdftoppm): 8 pages ≤ 10-page limit; all table
  columns visible; figures legible.

## Remaining UNRESOLVED items (disclosed, not hidden)

1. B6 conductor-count regularizer asymmetry — disclosed modeling convention.
2. Hybrid-side converter fidelity (bidirectional dispatch, unbalance, harmonics,
   protection, grounding, reliability) — outside validated scope; Limitations
   section carries these.
3. Validation covers the all-AC approximation at a peak snapshot; no hybrid OPF
   comparison exists — disclosed; discrepancy screen presented as screening.
4. Human metadata (authors/affiliations/ORCID/funding/COI/AI statement sign-off)
   remains placeholder by design.
5. All findings above: no fabricated verification was claimed anywhere; the
   adversarial tests actually run in `make test`.
