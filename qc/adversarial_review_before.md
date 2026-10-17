# Adversarial Independent Review — BEFORE fixes

Manuscript under review: `manuscript/build/acdc_boundary_tsg.docx` (commit 71ddbb22d,
baseline hashes in `qc/baseline_manifest_adversarial.txt`). Review performed on the
current revised pipeline, not on prior review documents. Evidence references are file
paths and line anchors in `src/acdc_boundary/`.

---

## Reviewer 1 — TSG associate editor

1. **Novelty vs. closest prior work is asserted, not demonstrated.** `pipeline.py:_novelty_matrix`
   hard-codes a 7×7 binary comparison (Ahmed 2016, Lotfi 2017, Wu 2019, Zhang 2022,
   de Barros 2023, Wang 2022) with hand-entered 0/1 flags per attribute. The flags are
   unverifiable assertions — no code checks them against the cited papers, and
   `results/novelty_matrix.csv` is generated from the literal, giving an audit artifact
   the false appearance of derived evidence. Recommendation: keep the matrix only as
   explicitly-labeled qualitative coding in config with provenance notes, or drop it.
   Severity: MAJOR.
2. **Journal fit is defensible but fragile.** The contribution is a methodology/screening
   result with no deployable engineering recommendation. TSG accepts methodology papers,
   but the negative-results framing (all-AC retained in 62.3% of joint cells) must survive
   the "so what" test: the actionable output is mechanism attribution, and the manuscript
   states this honestly. Acceptable as-is; do not inflate.
3. **Author/affiliation/funding/ORCID metadata are placeholders** (Gate T). This is
   correctly left to humans; flagged only so the checklist is not over-read as done.
   Severity: MINOR (process, not science).

Editorial recommendation (Reviewer 1): **major revision** — the novelty matrix evidence
problem and several documentation-level inconsistencies below must be fixed before an
AE would send this out comfortably. Confidence: high.

## Reviewer 2 — AC/DC power systems engineer

1. **DC voltage-drop convention is asymmetric and unjustified.** `model.py:line_metrics`
   computes `drop_pu` for DC as `I·R/(V_DC/2)`, i.e. it assumes a ±375 V bipolar
   pole-to-neutral return, while AC uses `V_AC/√3` (phase voltage). For a 750 V
   pole-to-pole DC feeder this is a real modeling choice (unipolar 750 V return vs.
   bipolar ±375 V) that changes the diagnostic by 2×, and the manuscript states the
   formula without justification. Screening-only diagnostic, so non-blocking, but the
   bipolar assumption should be named explicitly. Severity: MAJOR (modeling
   justification), effort: small (one sentence + config note).
2. **Conductor-count convention (4 AC / 3 DC) drives the material regularizer and the
   DC advantage** — a 25% material reduction is built into the objective via
   `M_e=n(d_j)l_e s_e`. Combined with `material_weight=3.0` this is the single largest
   lever biasing the objective toward DC; the manuscript labels it a "controlled scenario
   index" but does not report how much of the joint contrast survives with n(AC)=n(DC).
   Recommend a one-line sensitivity statement or ablation. Severity: MAJOR.
3. **Standby loss scales with installed capacity, not utilization shape** —
   `standby_fraction * downstream_peak_kw * 8760` charges every boundary converter
   17.5 kWh/kW-year regardless of loading. That is a defensible upper-bound convention
   but is not compared to a utilization-weighted alternative. Disclosed; MINOR.
4. **EV dataset is acquired and summarized but influences nothing.** `data.py:ev_data_summary`
   writes `data_processed/ev_charging_summary.csv`; no result, registry value, or
   manuscript number consumes it, while Methods says it "is used only to check the scale
   of the high-EV stress portfolio." Either cite the summary values in text/registry or
   soften the claim. Severity: MAJOR (claim–implementation mismatch).

Editorial recommendation (Reviewer 2): **major revision**. Confidence: high.

## Reviewer 3 — mathematical optimization specialist

1. **DP exactness claim is correctly scoped.** `optimize_design` is exact only for the
   separable additive tree objective; `exactness.py` independently enumerates 8 toy
   cases incl. an explicit tie; max objective error 5.7e-14 < tolerance. Verified —
   no defect.
2. **Tie-breaking is order-dependent but documented and verified** (AC before DC,
   smaller scale first, verified via `explicit_tie`). OK.
3. **`evaluate()` re-derives conductor scales rather than using the DP decision** —
   `_edge_choice` is deterministic per (edge, domain), so results coincide, but the
   design object's `conductor_scales` are discarded and recomputed; a future change to
   `_edge_choice` (e.g. constraint-aware choice) would silently desync optimize vs.
   evaluate. Refactor to use `design.conductor_scales` — MINOR, prevents a latent
   inconsistency.
4. **Double evaluation per scale in `_edge_choice`** — `line_metrics` is called twice
   per (edge, domain, scale). Performance only; MINOR.
5. **Constraint diagnostics are post-hoc, and the manuscript says so.** Ampacity/drop
   exceedances are counted (0 cells currently) but not enforced in the DP. If any cell
   had violated, "exact optimum" would not mean "feasible optimum" — current count is 0,
   so this is latent, not active. MINOR, disclosed.

Editorial recommendation (Reviewer 3): **minor revision**. Confidence: high.

## Reviewer 4 — validation / uncertainty specialist

1. **Discrepancy screen denominator is not a validated error bound for the paired
   contrast.** ε_f is |approx−pandapower|/pandapower on all-AC peak-snapshot loss,
   applied to a Δ% computed on matched modeled AC loss. The report and manuscript both
   call it a "screening heuristic, not a confidence interval" — consistent with the
   prompt's required downgrade, already in place. The extrapolation of an all-AC
   discrepancy to hybrid solutions is additionally unvalidated (no hybrid OPF);
   Limitations says this explicitly. Acceptable; MINOR residual: the word "robust" in
   "robustly material under screening rule" still over-sells — recommend renaming the
   category label to "exceeds screening threshold" in a future revision; keep or note.
2. **All-AC validation uses a single operating snapshot** (idxmax of summed profiles),
   scaled by portfolio peak factors. It does not sample the annual loss-hours integral
   that the model actually uses (H_e from full profile). The 1.4%/2.6% discrepancies
   therefore bound peak-snapshot error, not annual-energy error. MAJOR interpretive gap —
   manuscript should state the snapshot basis next to the numbers (it partially does:
   "benchmark operating point").
3. **Factorial grid frequencies** are correctly framed as design-grid counts
   (`factorial_structure.interpretation`, manuscript II-D). Verified: 7,200 rows =
   3·2·4·5·3·4·5, 1,440 joint cells. No misuse found.
4. **−11.17% central contrast** = mean over 3 feeders of
   (hybrid_joint − all_ac_conductor)/all_ac_conductor under K3/50%/seed-min/η=0.98.
   Definition, denominator, and "modeled loss, not realized savings" framing verified
   in code and text. No defect. MINOR: mean over n=3 presented without the per-feeder
   range adjacent (range exists in Table III).

Editorial recommendation (Reviewer 4): **minor revision**. Confidence: high.

## Reviewer 5 — reproducibility & research-integrity auditor

1. **Hardcoded factorial levels inside the manuscript builder.** `manuscript.py`
   iterates `for efficiency in (94, 96, 98, 99)` (Table V) and
   `for native_share in (0, 25, 50, 75, 100)` (Table VI), and the Abstract hardcodes
   "three … feeders … four demand/DER portfolios, five native-DC shares, three spatial
   allocations, four boundary efficiencies, and five nested design cells" in prose.
   These literals duplicate `configs/analysis_plan.yaml`; a grid change would silently
   produce stale tables/abstract. Class E/F violation — MAJOR for this audit's purpose;
   fix by deriving levels from config/registry.
2. **`converter_ablations` spec order vs. Table IX.** Manuscript claims "Eight matched
   ablations" (three sentences state it) but Table IX renders only 6 rows; the two
   omitted ablations (no_endpoint_mismatch_loss, no_boundary_electrical_loss) appear
   only in running text. Table should list all 8 or the text should say which are
   tabulated. MINOR–MAJOR (text/table consistency).
3. **QC self-review artifact.** `qc.py` copies `hostile_tsg_review_round_2.md`
   verbatim into `final_hostile_review_revision.md`, and writes identical content to
   `fabrication_audit.md` and `fabrication_audit_revision.md`. A "final review" that is
   a byte-copy of a previous round is a stale-asset risk and looks like review
   laundering. MINOR (this review supersedes both; file renamed outputs required).
4. **No silent fallbacks or cached-result reuse found.** `pipeline.main` regenerates
   every artifact from raw inputs each run; `_build_pdf` deletes stale PDF; deterministic
   ZIP; scenario CSV regenerated. Verified — PASS aspect.
5. **`qc.py` figure/table callout loops hardcode `range(1,6)` and 10 roman numerals** —
   coupled to current document shape; acceptable for a checker but brittle. MINOR.
6. **`download()` trusts `expected_sha256` literals in acquire.py** — these are pinned
   provenance anchors (correct design: checksum declared, download verified against it).
   Not a hardcode violation; class B with documented source. OK.

Editorial recommendation (Reviewer 5): **major revision** on items 1–3 alone (integrity
surface, not science). Confidence: high.

---

## Consolidated action table

| # | Severity | Finding | Evidence | Fix |
|---|----------|---------|----------|-----|
| B1 | MAJOR | Manuscript builder hardcodes factorial levels + counts | manuscript.py Table V/VI loops, Abstract prose | Derive from config/registry |
| B2 | MAJOR | Novelty matrix is unverified hand-coded literature claims | pipeline.py:_novelty_matrix | Move to config with provenance note, label as qualitative coding |
| B3 | MAJOR | EV dataset summarized but unused by any result/claim | data.py:ev_data_summary; Methods text | Add registry values + cite, or remove claim |
| B4 | MAJOR | DC drop_pu assumes ±375 V bipolar without justification | model.py:line_metrics | Name the convention in text/config |
| B5 | MAJOR | Validation is single peak snapshot; H_e integral unvalidated | validation.py | State snapshot basis explicitly beside numbers |
| B6 | MAJOR | Material regularizer bakes 4-vs-3 conductor advantage | model.py | Add one ablation/sensitivity note or caveat |
| M1 | MINOR | Table IX lists 6 of 8 ablations while text says eight | manuscript.py | Render all 8 rows |
| M2 | MINOR | QC copies round-2 review verbatim into "final" file | qc.py | Generate final files from current run |
| M3 | MINOR | evaluate() ignores DP conductor_scales | model.py:evaluate | Pass design.conductor_scales through |
| M4 | MINOR | _edge_choice double-computes line_metrics | model.py | Single call per scale |
| M5 | MINOR | "robustly material" label over-sells screening | analysis.py, manuscript | Note as sensitivity-screening label |
| m1 | minor | Central mean lacks adjacent per-feeder range in text | manuscript | Table III covers it — acceptable |
| m2 | minor | Standby charged on capacity not utilization | model.py | Disclosed; keep |

## Overall editorial recommendation (pre-fix)

**Major revision.** Soundness of the core DP/attribution machinery is verified; the
defects are claim-evidence alignment (novelty matrix, EV data, Table IX), hardcoded
scenario literals in the document generator, and modeling conventions that need
one-line justifications rather than new experiments. TSG submission is reasonable
after B1–B6 and M1–M3 are resolved.
