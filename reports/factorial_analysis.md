# Full-Factorial Architecture Evidence

```csv
total_result_rows,design_cases,joint_optimization_rows,spatial_seed_values,joint_rows_in_repeated_outcome_groups,joint_unique_outcome_rows_excluding_seed,interpretation
7200,5,1440,3,733,990,Design-grid frequencies and frozen spatial allocations; not independent real-world replications or probabilities.
```

- Joint all-AC cells: 897/1440.
- Joint hybrid cells: 399/1440.
- Joint root-converted-DC cells: 144/1440.

Architecture counts by boundary-efficiency grid:

```csv
converter_efficiency,all-AC,hybrid,root-converted DC
0.94,360,0,0
0.96,360,0,0
0.98,93,195,72
0.99,84,204,72
```

The stratified machine-readable summary contains 480 rows.
Frequencies are properties of the sampled design grid. Frozen spatial seeds
are sensitivity allocations, not independent feeders or statistical
replications. Repeated values at endpoint native-DC shares are structural.
