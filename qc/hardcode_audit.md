# Hardcode audit — data-to-manuscript numeric lineage (Phase 2)

Method: AST scan of every `.py` (all `ast.Constant` numeric literals, plus numeric
tokens inside string constants), regex scan of YAML/MD/TXT/Makefile producers.
1,630 literals inventoried in `numeric_literal_inventory.csv`.
Generated results tables (`results/*.csv`, `tables/*`, `figures/*`, `manuscript/build/*`)
are outputs, not sources; they were verified for internal consistency in Phase 3
rather than treated as literals.

Classification counts: A algorithmic 473, B documented constants 23,
C declared config params 1 (+ entire `configs/analysis_plan.yaml` block), D test
fixtures 107, E embedded manuscript/result literals 67, F suspicious/other 959
(most F rows are enumeration digits in prose strings — "1) … 2) …" — equation
constants, and report-file page/line numbers; each was triaged).

## Confirmed violations (fixed in Phase 5)

1. **`src/acdc_boundary/manuscript.py` — factorial levels duplicated as literals**
   - Line ~557: `for efficiency in (94, 96, 98, 99)` (Table V rows).
   - Line ~597: `for native_share in (0, 25, 50, 75, 100)` (Table VI rows).
   - Lines ~446/488/700/833: `for feeder in ("rural", "suburban", "urban")`.
   - Abstract prose (lines ~158–161): "Three public … feeders … two … topologies
     across four demand/DER portfolios, five native-DC shares, three spatial
     allocations, four boundary efficiencies, and five nested design cells."
   These are Class E: embedded scenario-count literals that silently go stale if
   `configs/analysis_plan.yaml` changes. Remediation: derive loops and the count
   words from `analysis_plan.yaml` / the value registry.

2. **`src/acdc_boundary/pipeline.py:_novelty_matrix` — hand-coded literature flags**
   A 7×7 matrix of 0/1 capability assertions plus DOI strings for six prior
   studies is written to `results/novelty_matrix.csv` as if derived. Class F→E:
   unverifiable claims rendered as computed evidence. Remediation: moved to
   `configs/novelty_coding.yaml` with an explicit "qualitative coding, manually
   verified" provenance field; manuscript caption updated to say so.

## Verified non-violations

- `acquire.py` `expected_sha256` literals: pinned integrity anchors checked against
  downloaded bytes — class B, correct design.
- `configs/analysis_plan.yaml` all scenario parameters: class C, each mirrored in
  Methods prose; rationale documented.
- `exactness.py`, `performance.py`, `tests/`: toy-case fixtures, class D.
- Manuscript equation strings (e.g. "1000", "8760", "√3", "2"): definitions of the
  model itself, class B — they are the specification, not results.
- Seed literals `[20260924, 20260925, 20260926]`: frozen scenario declaration in
  config, class C.
- No cached-result reads, no silent fallbacks: `pipeline.main` recomputes every
  artifact from raw inputs; `_build_pdf` removes stale PDFs; none of the ~280
  registry scalars is duplicated as a literal in the document builder (all prose
  numbers pass through `manuscript_values.csv` keys).

## Scan limitations

Regex/AST cannot prove a literal's semantics; class assignments are reviewer
judgments. The registry-based cross-check in Phase 3 (`claim_to_source_ledger.csv`)
is the stronger control: every number rendered in the DOCX is matched back to a
registry key or a declared constant.
