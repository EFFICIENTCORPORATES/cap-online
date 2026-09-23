# May 2027 — Validation Summary

## Corpus completeness

- Source PDFs: **40**
- Individual Beautified Markdown files: **40**
- Paired PDF ↔ Beautified MD files: **40/40**
- Structured ICAI block records: **1429**
- Missing units repaired in this pass: **Chapter 2 Framework, AS 23, AS 27**

## Machine validation

- Structural V6-style machine validation: **PASS**
- Duplicate unique IDs: **0**
- Duplicate short IDs within a Unit: **0**
- Invalid ICAI_BLOCK JSON markers: **0**
- Mean text-layer fidelity coverage: **88.4%**
- Lowest file text-layer fidelity coverage: **77.8%**
- All frontmatter source filenames/page counts, block page ranges, and code-fence balance were checked.

## Retrieval counts

- topic: **402**
- illustration: **218**
- illustration_question: **8**
- illustration_solution: **7**
- example: **104**
- note: **90**
- tyk_question: **548**
- case_scenario: **8**
- summary: **1**

TYK categories:

- MCQ: **271**
- SBQ: **191**
- TF: **8**
- TQ: **111**


## AS 2 manual review correction

The Test Your Knowledge section of **AS 2 — Valuation of Inventory** was manually checked against the ICAI source PDF.

- Q9 is a **Theoretical Question (TQ)**.
- Q10 to Q16 are **Scenario Based Questions (SBQ)**.
- Q16 exists in the source PDF but was previously merged into Q15 because the extracted source line appears as `31st March 2025.16.` without a clean question break.
- Q16 is now an independent `TYK-SBQ-16` block.
- AS 2 TYK count is now **16 questions**: 8 MCQ + 1 TQ + 7 SBQ.


## QA status

**Machine-validated V6-style; full visual page-by-page validation remains pending.**

This wording is intentional. The V5/V6 reference standard requires visual inspection of accounting geometry, diagrams, highlighted boxes, merged tables, and page-spanning layouts before a file is labelled fully `verified`. This pass does not falsely promote the corpus beyond the validation actually performed.
