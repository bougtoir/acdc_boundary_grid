# Reproduction audit (adversarial round)

## What was executed (actually run, not asserted)

1. `make acquire` — SimBench wheel + figshare EV dataset verified against pinned
   SHA-256 in `acquire.py`; `provenance/raw_data_ledger.csv` records
   URL/version/UTC/size/hash.
2. `python -m acdc_boundary.pipeline` — full regeneration of scenarios (7,200
   rows), central decomposition, attribution, factorial summaries, novelty
   matrix (now from `configs/novelty_coding.yaml`), pandapower validation
   (median 1.408%, max stress 2.591%), ablations, performance, registry (~283
   scalars), figures (PNG 300 dpi + TIFF 600 dpi LZW), DOCX, PDF, cover letter,
   submission docs, deterministic ZIP (1980 timestamps).
3. `make test` — 27 tests pass including the 13 new adversarial tests.
4. `make lint` — ruff clean.
5. Rendered-PDF visual inspection of all 8 pages.

## Determinism evidence

`results/scenario_results.csv`, `central_decomposition.csv`,
`phase_diagram.csv` SHA-256-identical across the baseline run (pre-fix commit
71ddbb22d) and the post-fix run — a refactor produced byte-identical scientific
outputs. Registry diff limited to the three documented additions.

## Clean-environment caveat (honest limitation)

True clean-environment reproduction (fresh clone + `make setup`) was exercised
earlier in this session's history and again implicitly: `make acquire`
re-verifies raw bytes each run and the pipeline regenerates every artifact from
raw inputs — nothing is read from caches or prior outputs. What was NOT done in
this round: a brand-new venv on a second machine. Tolerance note: pandapower and
numpy/pandas versions are pinned in `requirements`; results were stable to the
declared DP tolerance 1e-9 and exactness tolerance 5.68e-14 observed.
