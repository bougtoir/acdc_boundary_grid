# Feeder-Level Architecture Attribution

Central conditions are K3, 50% native-DC annual energy, the first frozen
spatial allocation, and 98% boundary efficiency. Values are modeled
attribution contrasts, not causal or realized utility effects.

```csv
feeder,topology,inherited_ac_loss_kwh,conductor_optimized_ac_loss_kwh,fixed_conductor_hybrid_loss_kwh,joint_hybrid_loss_kwh,conductor_contrast_pct,fixed_design_dc_permission_contrast_pct,joint_incremental_architecture_contrast_pct,topology_sensitivity_vs_original_joint_pct
rural,original,4360.648718367322,4217.303402418491,3538.4652450298827,3396.380823853936,-3.287247499323931,-18.854613761350496,-19.46558025902954,0.0
rural,synthetic_mst,4595.118655170577,4334.676198666262,3975.4647318485972,3717.3965258057306,-5.6678069936508875,-13.48504728217899,-14.24050250974831,9.451699282282846
suburban,original,10070.623606682118,8992.580477320922,9123.498969075265,8063.6715334987,-10.704829923798235,-9.4048261021136,-10.329726224468143,0.0
suburban,synthetic_mst,12336.049656802526,10125.640843612855,12089.306028081455,9888.380529566228,-17.918287253089773,-2.0001834913578533,-2.343163437366914,22.62876145794365
urban,original,12052.019003994177,11505.911867987388,11622.970669478736,11077.332599287907,-4.531250206507332,-3.559970610511394,-3.724861389664442,0.0
urban,synthetic_mst,15245.717466821836,13101.919549693175,14989.128048870574,12845.83160794933,-14.061640075608475,-1.6830261908608681,-1.9545833782030948,15.965025811133533
```

- Conductor contrast compares conductor-optimized AC with inherited AC.
- Fixed-design DC-permission contrast compares fixed-conductor hybrid with
  fixed-conductor AC on the same topology.
- Joint incremental architecture contrast compares joint domain/conductor
  optimization with conductor-optimized AC on the same topology.
- Topology sensitivity compares a synthetic coordinate-based MST with the
  original benchmark. It is not an observed infrastructure effect.
