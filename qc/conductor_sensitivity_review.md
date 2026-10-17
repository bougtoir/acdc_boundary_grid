# Skeptical review: conductor-accounting sensitivity (Phase 6)

Reviewer stance: hostile TSG power-distribution + optimization reviewer.

## Q1. Are the scenarios physically meaningful and correctly labeled?

- baseline_4ac_3dc: 3-phase AC + neutral; bipolar DC + metallic return — the
  original modeling convention. Physically meaningful.
- parity_3ac_3dc: AC three-phase without neutral; DC bipolar with dedicated
  return. Both realizable; labeled symmetric_physical.
- parity_4ac_4dc: a 4th DC conductor is NOT a defined physical option;
  labeled symmetric_accounting_only in config and in the manuscript table
  ("Parity (accounting)"). Not presented as physically feasible.
- bound_4ac_2dc / bound_3ac_2dc: bipolar DC without a dedicated return
  conductor is the favorable bound for DC material; labeled asymmetric_bound.

## Q2. Is the change bookkeeping-only, or does it secretly alter physics?

Verified in code (`model.line_metrics`): conductor counts multiply
`length_km x scale` into `material_index` only. Peak loss uses fixed 3-phase
(3I^2R) and 2-pole (2I^2R) terms; resistance, current, ampacity fraction, and
voltage drop contain no conductor-count term. Unit test
`test_conductor_counts_enter_only_material_index` asserts equality of all
electrical outputs across count scenarios and inequality of material_index.

## Q3. Fairness of the test

The 4/2 bound is the MOST DC-favorable physical count combination (AC keeps
its neutral while DC drops its return). If the 4/3 convention were hiding a
DC advantage, 4/2 would amplify it. Observed: architecture class, boundary
signatures, DC bus fraction, and architecture frequencies are invariant in
ALL 1,440 matched cells per scenario; the paired physical-loss contrast moved
only in the 4th significant digit (-9.5828% to -9.5819%).

## Q4. Could the invariance be trivial (material regularizer too weak to matter)?

material_weight=3.0 is a real regularizer — it demonstrably matters: conductor
scale selection changes across cells, and the conductor-optimization contrast
is -6.17% at the central cell. The sensitivity question is narrower: does the
AC:DC count ratio move the DOMAIN assignment? Within the tested grid it does
not. This is honestly stated: counts still affect material_index magnitude
(mean material index shifts across scenarios), and the manuscript limits the
claim to the tested accounting range.

## Q5. Hardcode audit of new code

- Scenario definitions live in configs/conductor_sensitivity.yaml with
  physical-basis labels; no scenario result is written into code.
- All Table XI and prose numbers come from results/manuscript_values.csv
  (value_id prefix conductor_*). Claim ledger: 325 tokens, 0 unmatched
  (includes table cells after the lineage checker extension).
- The tuple of scenario ids used for the min/max prose range in
  manuscript.py is a config-mirror list; flagged acceptable because it
  enumerates scenarios, not results. Residual nit: if the YAML gains a
  scenario, manuscript.py must be edited — documented limitation.

## Q6. Baseline stability

results/scenario_results.csv, central_decomposition.csv, phase_diagram.csv
SHA-256 identical to qc/baseline_manifest_conductor.txt. Baseline scenario
reproduces frozen architecture distribution (62.29/27.71/10.00%).

## Verdict

Sensitivity scenarios are correctly labeled, physically grounded where
claimed, and the invariance result is a legitimate null-sensitivity finding,
not an artifact. No BLOCKER/MAJOR defects. One MINOR: scenario-id list in
manuscript.py duplicates the YAML key list (must be edited together).
