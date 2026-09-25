# Scientific hard-code audit

- Headline scenario counts, architecture counts, attribution values, discrepancy
  classifications, ablation results, validation results, and performance values are
  loaded from `results/manuscript_values.csv`.
- Balanced per-efficiency, per-native-share, and per-feeder cell counts are generated in
  the scalar registry.
- The design-cell count, benchmark repetition count, and DC-voltage scenario are
  registry-backed.
- No frozen headline numeric literal was found in the manuscript generator.
- Constants that remain in source define the declared model, document styling, equation
  structure, or numbering rather than copied scientific findings.

Decision: PASS.
