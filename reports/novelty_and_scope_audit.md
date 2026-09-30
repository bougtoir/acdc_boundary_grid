# Novelty and scope audit

Verified 2026-09-24 against DOI metadata and the current IEEE PES TSG scope page.

## Defensible contribution

Endogenous AC/DC assignment, hybrid distribution planning, DC-feeder placement,
converter siting, and topology-aware expansion are established topics. The manuscript
therefore claims a controlled architecture-attribution framework: matched comparison
cells isolate permission to use DC from conductor and topology redesign while retaining
all-AC and root-converted-DC endpoints.

## Prior-work boundary

The literature matrix covers:

- hybrid network configuration planning (Ahmed et al.);
- AC/DC microgrid planning (Lotfi and Khodaei);
- DC-feeder placement (Wu et al.);
- temporally coupled hybrid configuration (Zhang et al.);
- topology-constrained expansion planning (de Barros et al.);
- topology-variable reliability-aware planning (Wang et al.).

The study does not claim the first mixed-domain optimizer, first converter-placement
model, first hybrid expansion model, or first reliability-aware AC/DC design.

## Journal fit

IEEE Transactions on Smart Grid explicitly lists AC/DC microgrids, AC/DC active
distribution networks, DER-grid integration, and EV-grid integration. The paper is
positioned as an active-distribution planning and mechanism-identification study, not
as converter hardware, DC transmission, or a non-active distribution paper.

## Claim limits

- SimBench is a benchmark dataset, not observed utility infrastructure.
- Synthetic minimum-length trees are sensitivities, not reconstructed networks.
- Proxy portfolios are not chronological DER dispatch.
- Normalized objective weights are not absolute lifecycle economics.
- Protection, grounding, harmonics, reliability, and deployability are not validated.
- Effects smaller than the nonlinear-validation discrepancy are indeterminate.
