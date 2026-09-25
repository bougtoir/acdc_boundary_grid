# Phase R09 Handoff — Converter-Component Ablations

## Status

**PASS**

## Implemented

Every canonical feeder/topology/portfolio/native-share/seed/efficiency cell was
resolved under matched ablations for:

- boundary conversion efficiency loss;
- converter standby loss;
- converter-capacity regularization;
- endpoint mismatch conversion;
- aggregate boundary electrical loss;
- electrical-ideal conversion;
- a full ideal-converter upper bound.

The outputs report architecture, boundary signature/count, DC bus/energy
fraction, and paired electrical-loss contrast. Removing the
converter-capacity regularizer changed architecture in 0.208% of cells,
whereas removing standby changed architecture in 5.069% and boundary location
in 24.931%. Eliminating boundary-efficiency loss changed architecture in
41.181%; the electrical-ideal and full-ideal bounds are reported separately.

All ranges are labeled as dimensionless planning scenarios. No vendor
efficiency curve, converter cost, or empirical utilization distribution is
claimed. The report distinguishes nominal efficiency from the amount of
downstream energy and peak capacity served by a boundary converter.

## Verification

```text
make all
completed successfully

Matched ablation rows: 11520
Ablations: 8
```

## Files changed

- `results/converter_ablations.csv`
- `tables/table_converter_ablations.csv`
- `reports/converter_ablations.md`

## Git

- Implementation commit: `df3b1e5c`
- Starting commit: `89fcdbc1`

## Unresolved issues

The ideal-converter variants are upper-bound scenarios rather than available
equipment. Vendor-specific curves remain intentionally unsupported.
