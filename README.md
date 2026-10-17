# Endogenous AC/DC Boundaries in Low-Voltage Distribution Networks

This project evaluates where AC distribution should end and DC distribution should
begin after separating the effect of the electrical domain from topology and conductor
redesign. It is a benchmark-based mechanism-identification study, not a field-deployment
claim.

Public repository: https://github.com/bougtoir/acdc_boundary_grid

The analysis uses three SimBench low-voltage feeders and a public EV charging-transaction
dataset. Raw source objects are downloaded into an immutable local archive and recorded
in `provenance/raw_data_ledger.csv`. Large raw files are intentionally excluded from Git.

## Reproduce

Prerequisites are Python 3.10, GNU Make, LibreOffice, and Poppler (`pdfinfo`).

```bash
make setup
make acquire
make all
make test
make qc
```

`make all` regenerates processed feeder inputs, scenario results, figures, tables,
manuscript values, the editable DOCX, cover letter, and submission ZIP. `make qc`
validates and adds the QC reports to the final ZIP.

## Scientific scope

- balanced radial planning approximation with explicit AC/DC boundary converters;
- symmetric endpoint-conversion accounting for AC-native and DC-native demand;
- fixed and optimized equivalent-parallel-conductor comparisons, with resistance
  inversely proportional and ampacity proportional to the conductor scale;
- original benchmark and explicitly synthetic minimum-length topology comparisons;
- converter efficiency, standby loss, native-DC share, DER/EV portfolio, and feeder
  archetype sensitivities;
- analytical toy-case tests and all-AC comparison with pandapower.

Protection, harmonics, grounding, detailed reliability, and deployable absolute cost
claims remain outside the model. Results are conditional break-even evidence.
