# Hostile Pre-Revision Review

Reviewed on 2026-09-24 from five independent perspectives: TSG editor,
AC/DC-distribution specialist, optimization reviewer, model-validation reviewer,
and reproducibility reviewer. Severity reflects likely review consequences;
feasibility reflects what can be corrected with the frozen inputs.

## BLOCKER — must be resolved before submission

### B1. The exact-dynamic-programming claim lacks independent optimality evidence

- **Fatality:** High; an optimization reviewer can reject an exactness claim supported
  only by the implementation that makes the claim.
- **Evidence:** Current tests cover one line-loss formula, all-AC feasibility, one
  ideal-boundary choice, ampacity scaling, PDF generation, and configured thresholds.
  They do not enumerate domain/conductor decisions independently.
- **Correction:** Add an independent brute-force enumerator for small trees; cover
  all-AC, root-DC, interior hybrid, converter-penalty, endpoint-mismatch, and
  conductor-driven architecture cases; compare objectives and unique optima and
  report tie handling.
- **Implementation phase:** R5.

### B2. The formulation is too compressed to reproduce the coded objective

- **Fatality:** High; only line, aggregate conversion, objective, and diagnostic
  expressions are shown. Endpoint mismatch, boundary standby, downstream quantities,
  regularizers, domain/conductor decisions, recursion, root condition, and backtracking
  are not formally defined.
- **Correction:** State the full graph, variables, all electrical and regularization
  components, DP state/recursion, root termination, and complexity. Follow the code
  where elegance and implementation differ.
- **Implementation phase:** R4.

### B3. Validation discrepancy is acknowledged but not operationalized

- **Fatality:** High; saying small differences are “indeterminate” does not classify
  any result. The paper can still be read as treating every negative contrast as
  meaningful.
- **Correction:** Use feeder-specific absolute pandapower line-loss discrepancy as a
  conservative screening threshold; classify paired cells as robust modeled benefit,
  indeterminate relative to model discrepancy, or no modeled benefit/AC retained.
  Add a maximum-discrepancy sensitivity rule without statistical-confidence language.
- **Implementation phase:** R8.

## MAJOR — likely major revision if uncorrected

### M1. The central -11.17% mean can be mistaken for a general DC saving

- **Problem:** The abstract foregrounds a three-feeder mean while the feeder-level
  contrasts differ and 62.3% of joint-design cells retain all-AC.
- **Correction:** Report every feeder and every nested comparison cell; call values
  modeled attribution contrasts or marginal planning value within the model.
- **Implementation phase:** R6 and R13.

### M2. The 7,200 rows are substantially underused and are not independent replications

- **Problem:** The current paper reports only overall architecture frequencies and
  three quantiles. The 7,200 rows include five design cells; only 1,440 are joint
  optimizations. Seeds are structurally irrelevant at native-DC shares 0 and 1, and
  477 joint rows repeat outcomes across seed after other factors are fixed.
- **Correction:** Stratify architecture, DC-bus fraction, and paired contrast by
  feeder, topology, portfolio, native-DC share, efficiency, and seed; explicitly
  describe repeated grid values as scenario structure rather than replication.
- **Implementation phase:** R7.

### M3. Converter mechanisms are confounded

- **Problem:** The “ideal” case jointly sets boundary and endpoint efficiencies to
  unity and standby to zero while retaining converter-capacity regularization. It
  cannot identify which component changes architecture.
- **Correction:** Separately ablate boundary efficiency loss, standby loss,
  converter-capacity regularization, endpoint mismatch, all electrical conversion
  losses, and the full idealized converter. Label dimensionless scenario ranges and
  avoid vendor/economic claims.
- **Implementation phase:** R9.

### M4. “Exact” applies only to an unconstrained separable screening objective

- **Problem:** Ampacity and voltage drop are post-optimization diagnostics, not
  feasibility constraints. Downstream power is fixed and domain-independent;
  converter losses do not alter upstream flow. “Exact planning model” without these
  qualifiers overstates physical scope.
- **Correction:** State that the DP is exact only for the declared unconstrained,
  balanced, separable radial objective. Describe diagnostic-limit exceedances as
  screening flags, never as enforced network feasibility.
- **Implementation phase:** R4, R13, and R15.

### M5. Computational evidence is absent

- **Problem:** There is no analytical state-count expression, measured state
  evaluations, runtime, memory, or brute-force scaling comparison.
- **Correction:** Instrument representative solves and benchmark the canonical VM;
  pair empirical timing with analytical complexity.
- **Implementation phase:** R10.

### M6. The reported domain-share quantity is a bus fraction, not a served-load share

- **Problem:** Configuration calls “DC-served load share” a primary outcome, while
  code reports the unweighted fraction of non-root buses assigned DC.
- **Correction:** Rename the existing quantity explicitly and add an
  energy-weighted DC-assigned fraction if used as a service-share outcome.
- **Implementation phase:** R7.

### M7. Attribution is conditional on normalized regularization, not causal identification

- **Problem:** Architectures minimize electrical losses plus dimensionless material
  and converter-capacity penalties, while displayed contrasts emphasize electrical
  loss. The nested cells isolate permissions within this objective but do not identify
  a causal technology effect or deployable optimum.
- **Correction:** Report objective components, retain the weights, use “modeled
  contrast” language, and explain the estimand for fixed and joint comparisons.
- **Implementation phase:** R4, R6, and R15.

### M8. The paper is below the scientific density expected of a TSG Regular Paper

- **Problem:** Four pages cannot contain the promised formulation, validation,
  heterogeneity, ablations, and computational evidence.
- **Correction:** Rebuild around evidence into 8–10 compliant pages, not by adding
  background or whitespace.
- **Implementation phase:** R13–R15.

## MODERATE — scientifically important and feasible

1. **All-AC validation is narrow.** It covers one benchmark peak point per feeder.
   Add reproducible load-factor stress checks without claiming hybrid nonlinear
   validation (R11).
2. **Architecture tie policy is undocumented.** Python tuple ordering currently
   favors the first enumerated domain, AC, for equal objective values. State and test
   the tolerance/tie convention (R4–R5).
3. **Boundary-loss physics is simplified.** It applies efficiency loss to fixed
   downstream annual energy and standby to downstream peak capacity; losses do not
   feed back into upstream flow and directionality is not chronological. State this
   explicitly (R4 and R15).
4. **AC/DC conductor accounting is scenario-specific.** Four AC and three bipolar-DC
   conductors form a normalized material index, not a universal physical equivalence.
   Clarify grounding/return-path limitations (R4 and R15).
5. **Topology sensitivity requires careful naming.** The synthetic MST uses benchmark
   coordinates and calibrated lengths but is not observed or utility-approved
   infrastructure. Preserve this statement wherever results appear (R6–R7).
6. **Current document styling is not fully compliant.** The generator uses 9.5-point
   body and 18-point title rather than nominal PES sizes, and table captions follow
   tables instead of preceding them (R14 and R20).
7. **AI disclosure contains revision-process language.** Replace “must be reconciled”
   wording with a factual final disclosure while retaining human verification
   placeholders (R22).
8. **Generated office/PDF artifacts are not byte-deterministic.** Scientific tables
   and figures reproduce exactly, but document container/PDF metadata differ by build
   (R17).

## MINOR / optional

- Provide vector/editable figure sources where practical.
- Reduce repeated limitations paragraphs after the final logical-consistency pass.
- Use a notation table only if it saves space relative to repeated definitions.
- Avoid increasing the reference count unless a verified source supports a necessary
  method, engineering assumption, or comparison.

## Cross-review verdict

**FAIL for submission in its current form; scientifically repairable with the frozen
inputs.** No frozen scientific result needs suppression or replacement. The required
work is formalization, independent exactness evidence, broader use of canonical
results, explicit discrepancy screening, component ablations, performance evidence,
and conservative claim language. These feasible BLOCKER/MAJOR/MODERATE corrections
are assigned to R4–R23 and must be implemented rather than left as recommendations.
