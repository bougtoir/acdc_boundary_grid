# Computational Performance

## Environment and total runs

```csv
platform,python,processor,logical_cpus,memory_total,peak_process_rss_mb,software_versions,factorial_scenario_runtime_s,converter_ablation_runtime_s,pipeline_elapsed_before_document_build_s
Linux-6.8.0-1061-aws-x86_64-with-glibc2.35,3.10.12,INTEL(R) XEON(R) PLATINUM 8559C,2,8131560 kB,687.3828125,numpy=2.2.6;pandas=2.3.3;networkx=3.4.2;pandapower=3.4.0;simbench=1.6.1;python-docx=1.2.0;matplotlib=3.10.6,17.26815872300017,26.91076400599991,121.38203083000008
```

## Representative full-feeder solves

```csv
feeder,topology,nodes,edges,repeats,median_runtime_ms,minimum_runtime_ms,maximum_runtime_ms,state_evaluations,transition_evaluations
rural,original,14,13,30,0.24049899991496204,0.21559800006798469,0.41318700004921993,27,132
rural,synthetic_mst,14,13,30,0.294954499963751,0.23972500002855668,0.5737700000736368,27,150
suburban,original,43,42,30,0.7529264998993312,0.7381289999557339,1.0246939998523885,85,486
suburban,synthetic_mst,43,42,30,0.7677224999724785,0.7522419998622354,0.9410039999693254,85,498
urban,original,58,57,30,0.999863000060941,0.9808069999053259,1.2217349999446014,115,642
urban,synthetic_mst,58,57,30,1.0371869999517003,1.01641300011579,1.2458020000849501,115,678
```

## Independently enumerated toy scaling

```csv
nodes,edges,enumerated_designs,dp_state_evaluations,dp_transition_evaluations,dp_runtime_ms,brute_force_runtime_ms,objective_absolute_error
2,1,4,3,4,0.027566999960981775,0.026817999923878233,0.0
3,2,16,5,12,0.030820000120002078,0.05427400014923478,0.0
4,3,64,7,20,0.04274499997336534,0.21832900006302225,2.842170943040401e-14
5,4,256,9,28,0.054800999805593165,1.1509240000577847,0.0
6,5,1024,11,36,0.06737300009262981,4.554292999955578,0.0
7,6,4096,13,44,0.08677100004206295,18.69604800003799,0.0
8,7,16384,15,52,0.10289100009686081,124.94339599993509,5.684341886080802e-14
```

The analytical DP work is O(|E||D|^2|S|), with |D| at most two and
|S| at most three. Brute-force enumeration grows with every combined
domain/conductor design. Timing illustrates this declared implementation
on one VM; it is not used as an independent proof of asymptotic complexity.
