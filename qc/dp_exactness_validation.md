# Dynamic-Programming Exactness Validation

The production dynamic program was compared with an independently coded
exhaustive enumerator over every permitted bus-domain assignment and conductor
combination. The enumerator does not call the production line, endpoint, boundary,
or evaluation functions.

```csv
case,enumerated_designs,brute_force_optimum_count,dp_architecture,brute_force_architectures,absolute_objective_error,objective_tolerance
all_ac_optimum,36,1,all-AC,all-AC,5.684341886080802e-14,3.8891080332409987e-08
root_dc_optimum,36,1,root-converted DC,root-converted DC,0.0,1.8488888888888893e-08
interior_hybrid_optimum,36,1,hybrid,hybrid,0.0,2.5228193290243156e-08
high_converter_penalty,36,1,all-AC,all-AC,0.0,8.889108033241007e-08
high_endpoint_mismatch,36,1,hybrid,hybrid,0.0,6.967263773468763e-08
conductor_driven_fixed,4,1,hybrid,hybrid,0.0,1.0712305324715301e-07
conductor_driven_optimized,36,1,all-AC,all-AC,0.0,8.045552477685444e-08
explicit_tie,6,6,all-AC,all-AC|root-converted DC,0.0,1e-10
```

- Cases: 8
- Objective agreements: 8/8
- DP assignments contained in brute-force optimum sets: 8/8
- DP conductor selections contained in brute-force optimum sets: 8/8
- Unique-optimum architecture checks: 8/8
- Numerical tolerance: 1e-10 times max(1, absolute optimum objective).
- Exact floating-point ties in the production iteration order prefer AC and then
  the smallest conductor multiplier. The explicit zero-cost tie case verifies that
  this selected solution belongs to the complete brute-force optimum set.
- The fixed- versus optimized-conductor pair verifies that conductor selection can
  change the architecture rather than merely its objective value.

Decision: **PASS**
