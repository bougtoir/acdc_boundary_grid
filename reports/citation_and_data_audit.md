# Citation and data audit

Audit date: 2026-09-24 UTC.

## Literature metadata

Seven literature and benchmark DOIs were checked against Crossref. Titles, author lists,
journals, volumes, issues, pages or article numbers, and DOIs in
`configs/references.yaml` agree with the returned records. The Ahmed et al. Crossref
record reports an early-access page range of 1–1 and no volume or issue; the manuscript
preserves that metadata rather than inventing final pagination.

The EV dataset DOI was checked against the Figshare API because it is a dataset record,
not a Crossref journal work. The verified citation is E. Lee, K. Baek, and J. Kim,
“A dataset for multi-faceted analysis of electric vehicle charging transactions,”
figshare, 2023, doi: 10.6084/m9.figshare.22495141.v1. The API reports version 1,
CC BY 4.0, 72,856 sessions, and the 7,605,859-byte `ChargingRecords.csv`.

API response snapshots are retained under the ignored immutable raw-data directory.

## Primary-data integrity

- SimBench wheel SHA-256:
  `f1d8c879cc35bca17552ac6fd0ea95e9097bc0300f61d66f13eb1d755017a763`.
- Figshare charging CSV SHA-256:
  `d541259bed55e2a9bc3413756954e7a059b50f9c9031f1dfc6ec87cbf3afd358`.

The acquisition module verifies expected hashes before analysis and does not overwrite a
valid local object. Publisher, URL, identifier, version, UTC retrieval time, license,
redistribution decision, local path, size, hash, and processing lineage are recorded in
the provenance ledger and manifest.

## Fabrication checks

- No synthetic topology is described as observed infrastructure.
- No proxy portfolio is described as measured DER operation.
- Manuscript values are generated from `results/manuscript_values.csv`.
- Author identities, affiliations, funding, conflicts, contributions, and ORCIDs remain
  explicit placeholders rather than inferred facts.
