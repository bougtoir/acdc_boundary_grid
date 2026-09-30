# Computational Performance

## Environment and total runs

```csv
platform,python,processor,logical_cpus,memory_total,peak_process_rss_mb,software_versions,factorial_scenario_runtime_s,converter_ablation_runtime_s,pipeline_elapsed_before_document_build_s
Linux-6.8.0-1061-aws-x86_64-with-glibc2.35,3.10.12,INTEL(R) XEON(R) PLATINUM 8559C,2,8131560 kB,689.9140625,numpy=2.2.6;pandas=2.3.3;networkx=3.4.2;pandapower=3.4.0;simbench=1.6.1;python-docx=1.2.0;matplotlib=3.10.6,17.927377535999995,36.39542201399996,97.05740966400003
```

## Representative full-feeder solves

```csv
feeder,topology,nodes,edges,repeats,median_runtime_ms,minimum_runtime_ms,maximum_runtime_ms,state_evaluations,transition_evaluations
rural,original,14,13,30,0.3162624999788477,0.310533000003943,0.4953019999902608,27,132
rural,synthetic_mst,14,13,30,0.3437969999993129,0.3356670000016493,0.5280070000139858,27,150
suburban,original,43,42,30,1.099277999998094,1.072637999982362,1.9826179999995475,85,486
suburban,synthetic_mst,43,42,30,1.1328045000027487,1.0870510000131617,1.8471920000138198,85,498
urban,original,58,57,30,1.4498430000173812,1.4241389999938292,2.758733000007396,115,642
urban,synthetic_mst,58,57,30,1.488093999995499,1.4669530000332998,1.6940080000154012,115,678
```

## Independently enumerated toy scaling

```csv
nodes,edges,enumerated_designs,dp_state_evaluations,dp_transition_evaluations,dp_runtime_ms,brute_force_runtime_ms,objective_absolute_error
2,1,4,3,4,0.027797000029750052,0.02476700001352583,0.0
3,2,16,5,12,0.03535599995529992,0.05317300002616321,0.0
4,3,64,7,20,0.04955099996095669,0.21344999998973435,2.842170943040401e-14
5,4,256,9,28,0.06472799998391565,1.1224460000107683,0.0
6,5,1024,11,36,0.08298099999137776,4.082454000013058,0.0
7,6,4096,13,44,0.10815299998512273,59.042557000054785,0.0
8,7,16384,15,52,0.13435100004244305,81.41743200002338,5.684341886080802e-14
```

The analytical DP work is O(|E||D|^2|S|), with |D| at most two and
|S| at most three. Brute-force enumeration grows with every combined
domain/conductor design. Timing illustrates this declared implementation
on one VM; it is not used as an independent proof of asymptotic complexity.
