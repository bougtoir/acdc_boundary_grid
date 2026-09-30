# Model-Discrepancy Screening Classification

The validation discrepancy denominator is pandapower nonlinear AC line loss.
The paired architecture contrast denominator is matched conductor-optimized
AC total modeled electrical loss. Applying the validation percentage to the
paired contrast is therefore a conservative screening heuristic, not a
confidence interval or formal error propagation.

```csv
feeder,threshold_pct
rural,1.1058435692372992
suburban,1.958356141622169
urban,1.4082432779974492
```

## Feeder-specific threshold

```csv
classification,cells
no modeled loss benefit/AC retained,897
robustly material under screening rule,531
indeterminate relative to model discrepancy,12
```

## Global maximum threshold

```csv
classification,cells
no modeled loss benefit/AC retained,897
robustly material under screening rule,525
indeterminate relative to model discrepancy,18
```

## Twice feeder-specific threshold

```csv
classification,cells
no modeled loss benefit/AC retained,897
robustly material under screening rule,513
indeterminate relative to model discrepancy,30
```

Classification rule: an all-AC solution or nonnegative electrical-loss
contrast is “no modeled loss benefit/AC retained”; a negative contrast
whose magnitude exceeds the selected threshold is “robustly material under
the screening rule”; remaining negative contrasts are indeterminate.
