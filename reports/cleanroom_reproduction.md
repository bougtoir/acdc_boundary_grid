# Clean-room reproduction

Run date: 2026-09-24 UTC.

A source-only copy was created without the virtual environment, raw data, processed
data, figures, results, tables, manuscript build, submission build, or generated QC.
The documented sequence completed successfully:

```text
make setup
make acquire
make all
make test
make lint
make qc
```

The clean environment downloaded and checksum-verified both primary sources. The test
suite reported 6 passed, Ruff reported no errors, and final QC passed.

The original workspace and clean-room build produced identical SHA-256 values for:

- `results/scenario_results.csv`:
  `a790e671e2de983a09d18cec661f1ac4d88c9b280941cd9b9cb13fdb3bd6fcd0`
- `results/manuscript_values.csv`:
  `86d46d49d45bc7a6c09c0dda2b5eac904ffa03a05bb5c1dd387b9f0cbea74e34`
- `results/validation_results.csv`:
  `c796b9f9d9bf151831d0bc2b3e1196b6814eedb5e5b0626c5d07d9b912b1caa3`
- all three generated table CSV files;
- all five generated PNG figures; and
- all five generated TIFF figures.

DOCX, PDF, ZIP, and provenance-ledger byte hashes are intentionally not used as the
determinism criterion because document metadata, archive timestamps, and retrieval
timestamps may vary while scientific content remains unchanged.
