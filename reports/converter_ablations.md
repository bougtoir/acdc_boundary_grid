# Converter-Component Ablations

All ranges are dimensionless planning scenarios. They are not empirical
vendor curves or equipment-cost estimates. Baseline comparison is matched
within feeder, topology, portfolio, native-DC share, spatial seed, and
nominal boundary-efficiency grid point.

```csv
ablation,cells,all_ac_pct,hybrid_pct,root_dc_pct,architecture_change_pct,boundary_change_pct,mean_dc_bus_fraction,mean_loss_change_pct,mean_loss_contrast_change_pct_points
baseline,1440,62.291666666666664,27.708333333333336,10.0,0.0,0.0,0.171035293897136,-9.582444426062507,0.0
electrical_ideal_conversion,1440,33.33333333333333,33.33333333333333,33.33333333333333,66.59722222222221,75.76388888888889,0.4216791979949875,-28.958343754194008,-19.375899328131503
full_ideal_converter,1440,0.0,0.0,100.0,90.0,90.0,1.0,-48.62605710861592,-39.04361268255341
no_boundary_efficiency_loss,1440,21.11111111111111,58.88888888888889,20.0,41.18055555555556,64.65277777777779,0.4455141593299488,-42.55779696560637,-32.975352539543856
no_boundary_electrical_loss,1440,19.166666666666668,60.83333333333333,20.0,43.125,70.55555555555556,0.49808763361394937,-70.33850893062035,-60.75606450455785
no_capacity_regularizer,1440,62.083333333333336,27.916666666666668,10.0,0.20833333333333334,3.8194444444444446,0.17308689726452883,-9.588183312078238,-0.005738886015729536
no_endpoint_mismatch_loss,1440,100.0,0.0,0.0,37.708333333333336,37.708333333333336,0.0,0.0,9.582444426062507
no_standby_loss,1440,57.22222222222222,31.11111111111111,11.666666666666666,5.069444444444445,24.930555555555557,0.21751146027461815,-14.99471612092688,-5.412271694864371
```

Boundary-efficiency loss, standby loss, capacity regularization, endpoint
mismatch, aggregate boundary electrical loss, electrical-ideal conversion,
and a full idealized converter are separated. High nominal efficiency alone
does not establish adequate utilization; boundary changes remain conditioned
on the spatially downstream energy and peak power.
