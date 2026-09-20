# Correction Audit Report — Corrected V2

## Release-level semantic corrections

- Exhaustive source Example registry: **53 source Examples**.
- Bank Reconciliation Statement Illustration 1: split into Question + Solution; `(x) Errors` retained separately.
- Illustration reconciliation: **235 questions + 235 solutions**.
- Rectification Theory Question 3: unique question key plus explicit reference to source Answer 2.
- Result counts distinguish source items from returned answer/solution blocks.

## Source Example distribution

| Source PDF | Examples |
|---|---:|
| `CA_L1_P01_C10_U1_IntroductionToPartnershipAccounts.pdf` | 4 |
| `CA_L1_P01_C10_U2_TreatmentOfGoodwillInPartnershipAccounts.pdf` | 9 |
| `CA_L1_P01_C10_U3_AdmissionOfANewPartner.pdf` | 7 |
| `CA_L1_P01_C10_U4_RetirementOfAPartner.pdf` | 5 |
| `CA_L1_P01_C10_U5_DeathOfAPartner.pdf` | 3 |
| `CA_L1_P01_C11_U4_AccountingForBonusIssueAndRightIssue.pdf` | 5 |
| `CA_L1_P01_C1_U1_MeaningAndScopeOfAccounting.pdf` | 1 |
| `CA_L1_P01_C1_U2_AccountingConceptsPrinciplesAnd.pdf` | 4 |
| `CA_L1_P01_C2_U1_BasicAccountingProceduresJournalEntries.pdf` | 1 |
| `CA_L1_P01_C2_U6_RectificationOfErrors.pdf` | 5 |
| `CA_L1_P01_C3_U0_BankReconciliationStatement.pdf` | 8 |
| `CA_L1_P01_C5_U0_DepreciationAndAmortisation.pdf` | 1 |

**Total: 53 Examples**

## Stable audited retrieval counts

| Category | Count |
|---|---:|
| MCQs | 269 |
| Illustrations | 235 |
| Illustration solutions | 235 |
| Practical Questions | 79 |
| Theory retrieval blocks | 79 |
| True/False statements | 307 |
| Scenario/SBQ questions | 0 |

## Important source anomalies preserved rather than invented

- Rectification of Errors contains 10 True/False questions but no corresponding True/False answer section in the source; the tool does not fabricate answers.
- Rectification Theory Question 3 has no separately numbered source Answer 3; the relevant suspense-account discussion occurs within source Answer 2, so the relationship is stored explicitly.
- Only Examples with a safely separable source Question/Solution boundary expose a question-only derivative. The exhaustive `Examples` preset always returns all 53 full source Example items.

## Regression tests

The bundled unit tests check the 53-Example total, previously missed Example-heavy Units, 235/235 Illustration pairing, the BRS Illustration 1 boundary, Rectification shared-answer relation, MCQ count, source provenance and zero-error validation.
