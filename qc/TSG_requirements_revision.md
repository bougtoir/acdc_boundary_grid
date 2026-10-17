# Live IEEE Transactions on Smart Grid Requirements — Revision Check

Checked on 2026-09-25 UTC. Live official instructions override inherited project
assumptions. The main PES Author's Kit page identifies Part 2 as revised May 2026.

## Applicable requirements

| Topic | Current requirement | Revision action |
|---|---|---|
| Scope | TSG explicitly includes AC/DC microgrids and active distribution networks, DER integration, and EV-grid interaction. | Retain TSG as the primary target and frame the work as distribution-planning methodology. |
| Initial length | All PES Transactions research papers must be no more than 10 pages at initial submission. | Remain within 10 pages, including references, without padding. |
| Format | US Letter, single-spaced, double-column; nominal 10-point body/equations, 9-point abstract/index terms, and 8-point captions/references. | Correct the existing 9.5-point body and 18-point title during the manuscript rebuild. |
| Abstract | 150–200 words; no equations, figures, tables, or references. | Enforce programmatically. |
| Index terms | Up to 10, alphabetized, using IEEE indexing terminology where possible. The live rule states no explicit minimum. | Keep the internal target of at least three while recording that it is not an official minimum. |
| Figures/tables | Place near, but not before, first mention; figure captions below, table captions above; figures use Arabic numerals and tables Roman numerals. | Rebuild callouts and caption placement in order. |
| Graphics | Accepted formats include PNG and TIFF; non-vector color/grayscale graphics should exceed 300 dpi, and black-and-white line art should exceed 600 dpi. | Retain 600-dpi TIFF as the archival raster deliverable and use 300-dpi PNG only as a review copy; add editable/vector sources where generated. |
| References | Consecutive bracketed IEEE references in order of first appearance. No explicit reference-count maximum was found. | Use only necessary verified references; do not pad. |
| Review model | TSG uses single-anonymous review with at least two independent reviewers. | Author metadata belongs in the manuscript, but unresolved human fields remain placeholders. |
| Supplementary material | The PES Transactions submission workflow states that PES does not allow supplementary material. | Do not label or upload a conventional supplement. Put essential evidence in the 10-page paper and retain detailed machine-readable validation in the reproducibility package/QC archive. |
| Code/data | The submission workflow asks whether code or data are associated with the manuscript and supports links/DOIs. | Keep the public repository and exact provenance ledger; do not redistribute restricted raw objects. |
| AI-assisted content | PES policy requires disclosure in Acknowledgments when AI-generated content is used. The disclosure must identify the AI system, affected sections, and level of use. Editing-only use is outside the mandatory scope, but this project used substantive assistance. | Name Cognition Devin and describe code, analysis, figures, and drafting assistance; retain human-verification placeholders. |

## Authoritative sources and preserved evidence

1. IEEE PES, “Preparation and Submission of Transactions Papers,” Part 2,
   revised May 2026:
   https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-transactions-papers/
   - “The required abstract (150–200 words) and up to 10 keywords” are reviewed.
   - “Transactions papers are limited to 10 pages at submission.”
   - The workflow note states: “PES does not allow the submission of supplementary material.”
2. IEEE PES, “Preparation of a Formatted Transactions/Journal Paper,” Part 4a:
   https://ieee-pes.org/publications/authors-kit/preparation-of-a-formatted-technical-work/
   - Specifies US-Letter, double-column layout and nominal type sizes.
   - Requires figures/tables near first mention and IEEE numbering/caption conventions.
3. IEEE PES, “Transactions on Smart Grid”:
   https://ieee-pes.org/publications/transactions-on-smart-grid/
   - Confirms scope and single-anonymous peer review.
4. IEEE PES Publications Board, “Updated IEEE PES Publications Policies,”
   dated 2025-12-08:
   https://ieee-pes.org/wp-content/uploads/2025/12/PES-Publications-Policies-12-11-25.pdf
   - Confirms the 10-page initial limit and the current substantive-AI disclosure elements.
5. IEEE Author Center, “File Formatting” and “Resolution and Size”:
   https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/file-formatting/
   https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/
   - Lists accepted graphics formats and raster resolution guidance.
6. IEEE Author Center, “Submission and Peer Review Policies”:
   https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/
   - Confirms the disclosure requirement for substantive AI-generated article content.

## Requirement conflicts resolved conservatively

- The revision prompt requests a supplement, but current PES instructions prohibit
  supplementary material. No conventional supplement will be included in the submission
  set. Detailed validation and brute-force outputs will instead remain in the reproducibility
  package and be summarized sufficiently in the main paper.
- Some older IEEE wording asks for section-level citations to the AI system, whereas the
  current PES policy requires the system, affected sections, and level of use in the
  Acknowledgments disclosure. The final disclosure will satisfy the current PES wording
  without inventing a bibliographic reference to the software.

## Phase decision

**PASS.** The generated seven-page Regular Research Paper is within the 10-page initial
limit. The official PES Author's Kit, TSG scope page, December 2025 PES publication-policy
PDF, IEEE Author Center AI policy, and graphics guidance were rechecked on 2026-09-25;
the requirements recorded above remain current. Compliance must still be rechecked
immediately before submission because the portal and policy pages can change.
