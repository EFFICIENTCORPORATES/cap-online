# Phase 0 — Batch 1 Prompts (Chapters 1–4, 10 units)

Ready-to-paste prompts for Gemini / GitHub Copilot / Blackbox AI in VS Code. Each prompt is
fully instantiated with the real source file path and the real topic scaffold pulled directly
from `books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json`
— no placeholders left for you to fill in.

**How to use each block:** open the named source file in VS Code first (so the tool has it in
context), then paste the prompt. Bring the JSON output back to me (Claude) for the Tier 3
review pass before it's merged into the master `topic-keyword-index.json`.

**Output schema every prompt should produce** (same for all 10 — not repeated per-unit below):
```json
{
  "M1-C1-U0-T1": {
    "chapter_id": "M1-C1-U0",
    "chapter_name": "Introduction to Accounting Standards",
    "topic_name": "Introduction",
    "keywords": ["...", "..."],
    "typical_question_signals": ["...", "..."],
    "notes": ""
  }
}
```

---

## Unit 1 of 10 — M1-C1-U0 — Introduction to Accounting Standards

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C1_U1_ Introduction to Accounting Standards.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C1-U0-T1 | Introduction | 1.2 |
| M1-C1-U0-T2 | Standards Setting Process | 1.6 |
| M1-C1-U0-T3 | How Many Accounting Standards? | 1.9 |
| M1-C1-U0-T4 | Status of Accounting Standards | 1.13 |
| M1-C1-U0-T5 | Need for Convergence towards Global Standards | 1.13 |
| M1-C1-U0-T6 | International Accounting Standard Board | 1.15 |
| M1-C1-U0-T7 | International Financial Reporting Standards as Global Standards | 1.16 |
| M1-C1-U0-T8 | Becoming IFRS Compliant | 1.17 |
| M1-C1-U0-T9 | What are Carve Outs/Ins in Ind AS? | 1.18 |
| M1-C1-U0-T10 | Convergence to IFRS in India | 1.20 |
| M1-C1-U0-T11 | What are Indian Accounting Standards (Ind AS)? | 1.21 |
| M1-C1-U0-T12 | History of IFRS Converged Indian Accounting Standards (Ind AS) | 1.22 |
| M1-C1-U0-T13 | List of Ind AS | 1.23 |
| M1-C1-U0-T14 | Roadmap for Implementation of Indian Accounting Standards (Ind AS): A Snapshot | 1.26 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C1_U1_ Introduction to Accounting Standards.md`
>
> This unit's known topic breakdown (topic ID → topic name → page) is:
> `M1-C1-U0-T1 Introduction (1.2); M1-C1-U0-T2 Standards Setting Process (1.6); M1-C1-U0-T3 How Many Accounting Standards? (1.9); M1-C1-U0-T4 Status of Accounting Standards (1.13); M1-C1-U0-T5 Need for Convergence towards Global Standards (1.13); M1-C1-U0-T6 International Accounting Standard Board (1.15); M1-C1-U0-T7 International Financial Reporting Standards as Global Standards (1.16); M1-C1-U0-T8 Becoming IFRS Compliant (1.17); M1-C1-U0-T9 What are Carve Outs/Ins in Ind AS? (1.18); M1-C1-U0-T10 Convergence to IFRS in India (1.20); M1-C1-U0-T11 What are Indian Accounting Standards (Ind AS)? (1.21); M1-C1-U0-T12 History of IFRS Converged Indian Accounting Standards (Ind AS) (1.22); M1-C1-U0-T13 List of Ind AS (1.23); M1-C1-U0-T14 Roadmap for Implementation of Indian Accounting Standards (Ind AS): A Snapshot (1.26)`
>
> For EACH topic ID listed above, extract:
> 1. 5–12 keywords/technical terms that a question testing *specifically this topic* would likely use. Be specific — avoid generic accounting terms that could apply to any chapter.
> 2. 2–4 "typical question signal" phrasings — short example phrasings showing how a real exam question testing this topic tends to be worded. Note: this chapter is mostly theory/definitional (CA Inter numerical questions rarely test "history of IFRS convergence" computationally) — say so explicitly for topics with no realistic computational angle rather than forcing a fake example.
> 3. If the unit's actual content extends beyond the last numbered topic listed above (i.e. there are unnumbered sections in the ICAI source text after the last numbered one), list these as additional topics with sequential IDs continuing from the last number, each suffixed with an asterisk (e.g. M1-C1-U0-T15*), and note `"unnumbered in ICAI source"`.
>
> Do NOT invent concepts not actually present in the attached file — only extract what's genuinely there.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 2 of 10 — M1-C2-U0 — Framework for Preparation & Presentation of Financial Statements

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C2_U1_ Framework for Preparation and Presentation of Financial Statements.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C2-U0-T1 | Introduction | 2.2 |
| M1-C2-U0-T2 | Purpose of the Framework | 2.3 |
| M1-C2-U0-T3 | Status and Scope of the Framework | 2.3 |
| M1-C2-U0-T4 | Components of Financial Statements | 2.4 |
| M1-C2-U0-T5 | Objectives and Users of Financial Statements | 2.5 |
| M1-C2-U0-T6 | Fundamental Accounting Assumptions | 2.6 |
| M1-C2-U0-T7 | Qualitative Characteristics of Financial Statements | 2.11 |
| M1-C2-U0-T8 | True and Fair View | 2.13 |
| M1-C2-U0-T9 | Elements of Financial Statements | 2.13 |
| M1-C2-U0-T10 | Measurement of Elements of Financial Statements | 2.21 |
| M1-C2-U0-T11 | Capital Maintenance | 2.25 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C2_U1_ Framework for Preparation and Presentation of Financial Statements.md`
>
> This unit's known topic breakdown (topic ID → topic name → page) is:
> `M1-C2-U0-T1 Introduction (2.2); M1-C2-U0-T2 Purpose of the Framework (2.3); M1-C2-U0-T3 Status and Scope of the Framework (2.3); M1-C2-U0-T4 Components of Financial Statements (2.4); M1-C2-U0-T5 Objectives and Users of Financial Statements (2.5); M1-C2-U0-T6 Fundamental Accounting Assumptions (2.6); M1-C2-U0-T7 Qualitative Characteristics of Financial Statements (2.11); M1-C2-U0-T8 True and Fair View (2.13); M1-C2-U0-T9 Elements of Financial Statements (2.13); M1-C2-U0-T10 Measurement of Elements of Financial Statements (2.21); M1-C2-U0-T11 Capital Maintenance (2.25)`
>
> For EACH topic ID listed above, extract:
> 1. 5–12 keywords/technical terms that a question testing *specifically this topic* would likely use. Be specific — avoid generic accounting terms that could apply to any chapter. Note: "Measurement of Elements" (T10) and "Capital Maintenance" (T11) are the two sub-topics most likely to appear in a numerical/scenario question (historical cost vs current cost vs realisable value vs present value; financial vs physical capital maintenance) — flag which topics in this unit are purely theoretical vs which have a realistic computational angle.
> 2. 2–4 "typical question signal" phrasings per topic.
> 3. If the unit's actual content extends beyond the last numbered topic listed above, list additional topics with sequential IDs continuing from the last number, suffixed with an asterisk, noted `"unnumbered in ICAI source"`.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 3 of 10 — M1-C3-U0 — Applicability of Accounting Standards

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C3_U1_ Applicability of Accounting Standards.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C3-U0-T1 | Status of Accounting Standards | 3.2 |
| M1-C3-U0-T2 | Applicability of Accounting Standards | 3.6 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C3_U1_ Applicability of Accounting Standards.md`
>
> This unit's known topic breakdown is:
> `M1-C3-U0-T1 Status of Accounting Standards (3.2); M1-C3-U0-T2 Applicability of Accounting Standards (3.6)`
>
> Note: this is a short, mostly-tabular unit (which AS applies to which entity level — I/II/III/IV non-company entities, exemptions/relaxations by level). This is exactly the kind of content that gets tested as a standalone theory/classification question ("is AS X applicable to a Level II non-company entity?") — extract keywords accordingly (entity level names, specific AS numbers with partial-exemption status, turnover/borrowing thresholds if present in the text).
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings. If content extends beyond T2, add sequential asterisked IDs as usual.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 4 of 10 — M1-C4-U1 — AS 1 Disclosure of Accounting Policies

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U1_ Accounting Standard 1 Disclosure of Accounting Policies.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U1-T1.1 | Introduction | 4.2 |
| M1-C4-U1-T1.2 | Fundamental Accounting Assumptions | 4.3 |
| M1-C4-U1-T1.3 | Accounting Policies | 4.4 |
| M1-C4-U1-T1.4 | Selection of Accounting Policy | 4.5 |
| M1-C4-U1-T1.5 | Disclosure of Changes in Accounting Policies | 4.7 |
| M1-C4-U1-T1.6 | Disclosure of Deviations From Fundamental Accounting Assumptions | 4.8 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U1_ Accounting Standard 1 Disclosure of Accounting Policies.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U1-T1.1 Introduction (4.2); M1-C4-U1-T1.2 Fundamental Accounting Assumptions (4.3); M1-C4-U1-T1.3 Accounting Policies (4.4); M1-C4-U1-T1.4 Selection of Accounting Policy (4.5); M1-C4-U1-T1.5 Disclosure of Changes in Accounting Policies (4.7); M1-C4-U1-T1.6 Disclosure of Deviations From Fundamental Accounting Assumptions (4.8)`
>
> **Important cross-referencing note:** T1.4 and T1.5 (selection of accounting policy; disclosure of a *change* in accounting policy) are the AS 1 concepts most likely to appear embedded *inside* questions primarily about other standards — e.g. an AS 2 question about switching inventory valuation methods, or an AS 10 question about switching depreciation methods, both ultimately hinge on the AS 1 "change in accounting policy vs change in accounting estimate" distinction. Extract keywords that would let a matcher catch these embedded/cross-chapter references too (e.g. "change in accounting policy", "change in accounting estimate", "retrospective application", "prospective application", "materiality of change").
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings. If content extends beyond T1.6, add sequential asterisked IDs as usual.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 5 of 10 — M1-C4-U2 — AS 3 Cash Flow Statement

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U2_ Accounting Standard 3 Cash Flow Statement.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U2-T2.1 | Introduction | 4.17 |
| M1-C4-U2-T2.2 | Objective | 4.18 |
| M1-C4-U2-T2.3 | Meaning of the Term Cash and Cash Equivalents for Cash Flow Statements | 4.19 |
| M1-C4-U2-T2.4 | Meaning of The Term Cash Flow | 4.19 |
| M1-C4-U2-T2.5 | Types of Cash Flow | 4.20 |
| M1-C4-U2-T2.6 | Identifying Type of Cash Flows | 4.21 |
| M1-C4-U2-T2.7 | Reporting Cash Flows from Operating Activities | 4.23 |
| M1-C4-U2-T2.8 | Reporting Cash Flows on Net Basis | 4.25 |
| M1-C4-U2-T2.9 | Business Purchase | 4.27 |
| M1-C4-U2-T2.10 | Exchange gains and losses | 4.27 |
| M1-C4-U2-T2.11 | Disclosures | 4.28 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U2_ Accounting Standard 3 Cash Flow Statement.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U2-T2.1 Introduction (4.17); M1-C4-U2-T2.2 Objective (4.18); M1-C4-U2-T2.3 Meaning of the Term Cash and Cash Equivalents for Cash Flow Statements (4.19); M1-C4-U2-T2.4 Meaning of The Term Cash Flow (4.19); M1-C4-U2-T2.5 Types of Cash Flow (4.20); M1-C4-U2-T2.6 Identifying Type of Cash Flows (4.21); M1-C4-U2-T2.7 Reporting Cash Flows from Operating Activities (4.23); M1-C4-U2-T2.8 Reporting Cash Flows on Net Basis (4.25); M1-C4-U2-T2.9 Business Purchase (4.27); M1-C4-U2-T2.10 Exchange gains and losses (4.27); M1-C4-U2-T2.11 Disclosures (4.28)`
>
> **Important false-positive warning (carry this into the keyword design, don't just list generic terms):** depreciation figures, PPE disposal gains/losses, and provision write-backs appear CONSTANTLY inside Cash Flow Statement questions purely as add-back/deduction line items in the indirect-method reconciliation — this does NOT mean the question is testing AS 10 or AS 29, it's testing AS 3's own operating-activities reconciliation mechanics. When you write keywords/signals for T2.6/T2.7 (identifying and reporting operating cash flows), make this "mechanical add-back, not a substantive test of the other standard" distinction explicit in the `notes` field, since a later automated tagger needs to know NOT to cross-tag every CFS question with AS 10/AS 29/etc. just because those terms appear.
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings. If content extends beyond T2.11, add sequential asterisked IDs as usual.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 6 of 10 — M1-C4-U3 — AS 17 Segment Reporting

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U3_ Accounting Standard 17 Segment Reporting.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U3-T3.1 | Introduction | 4.43 |
| M1-C4-U3-T3.2 | Objective | 4.44 |
| M1-C4-U3-T3.3 | Scope | 4.44 |
| M1-C4-U3-T3.4 | Definition of the terms used in the Accounting Standard | 4.45 |
| M1-C4-U3-T3.5 | Treatment of Interest for determining Segment Expense | 4.48 |
| M1-C4-U3-T3.6 | Allocation | 4.49 |
| M1-C4-U3-T3.7 | Primary and Secondary Segment Reporting Formats | 4.49 |
| M1-C4-U3-T3.8 | Business and Geographical Segments | 4.50 |
| M1-C4-U3-T3.9 | Identifying Reportable Segments (Quantitative Thresholds) | 4.51 |
| M1-C4-U3-T3.10 | Segment Accounting Policies | 4.53 |
| M1-C4-U3-T3.11 | Primary Reporting Format | 4.53 |
| M1-C4-U3-T3.12 | Secondary Segment Information | 4.54 |
| M1-C4-U3-T3.13 | Other Disclosures | 4.55 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U3_ Accounting Standard 17 Segment Reporting.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U3-T3.1 Introduction (4.43); M1-C4-U3-T3.2 Objective (4.44); M1-C4-U3-T3.3 Scope (4.44); M1-C4-U3-T3.4 Definition of the terms used in the Accounting Standard (4.45); M1-C4-U3-T3.5 Treatment of Interest for determining Segment Expense (4.48); M1-C4-U3-T3.6 Allocation (4.49); M1-C4-U3-T3.7 Primary and Secondary Segment Reporting Formats (4.49); M1-C4-U3-T3.8 Business and Geographical Segments (4.50); M1-C4-U3-T3.9 Identifying Reportable Segments (Quantitative Thresholds) (4.51); M1-C4-U3-T3.10 Segment Accounting Policies (4.53); M1-C4-U3-T3.11 Primary Reporting Format (4.53); M1-C4-U3-T3.12 Secondary Segment Information (4.54); M1-C4-U3-T3.13 Other Disclosures (4.55)`
>
> **Known cross-chapter link — already confirmed in a prior audit:** T3.5 (Treatment of Interest for determining Segment Expense) directly interacts with AS 2 (inventory) and AS 16 (borrowing costs) — a question asking "is interest capitalised into inventory cost under AS 2/AS 16 also a segment expense?" tests T3.5 specifically. Make sure T3.5's keywords capture this interaction explicitly (e.g. "interest as segment expense", "borrowing cost embedded in inventory", "AS 16 read with AS 2").
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings, paying special attention to T3.9 (Quantitative Thresholds — the 10% revenue/result/assets tests are a classic numerical MCQ pattern) since that's the most computation-heavy topic in this unit.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 7 of 10 — M1-C4-U4 — AS 18 Related Party Disclosures

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U4_ Accounting Standard 18 Related Party Disclosures.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U4-T4.1 | Introduction | 4.72 |
| M1-C4-U4-T4.2 | Related Party Issue – Why disclosure is needed? | 4.72 |
| M1-C4-U4-T4.3 | Related Party Relationships, as contemplated under AS 18 | 4.73 |
| M1-C4-U4-T4.4 | Who are NOT deemed to be Related Parties under AS 18? | 4.74 |
| M1-C4-U4-T4.5 | Exemption from Related Party Disclosure in certain situations | 4.75 |
| M1-C4-U4-T4.6 | Definitions of other Terms used in AS 18 | 4.76 |
| M1-C4-U4-T4.7 | Disclosure requirements under AS 18 | 4.86 |
| M1-C4-U4-T4.8 | List of Related Party Transactions, to be Disclosed | 4.87 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U4_ Accounting Standard 18 Related Party Disclosures.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U4-T4.1 Introduction (4.72); M1-C4-U4-T4.2 Related Party Issue – Why disclosure is needed? (4.72); M1-C4-U4-T4.3 Related Party Relationships, as contemplated under AS 18 (4.73); M1-C4-U4-T4.4 Who are NOT deemed to be Related Parties under AS 18? (4.74); M1-C4-U4-T4.5 Exemption from Related Party Disclosure in certain situations (4.75); M1-C4-U4-T4.6 Definitions of other Terms used in AS 18 (4.76); M1-C4-U4-T4.7 Disclosure requirements under AS 18 (4.86); M1-C4-U4-T4.8 List of Related Party Transactions, to be Disclosed (4.87)`
>
> **Important trap to encode:** T4.4 (who is NOT a related party) is a classic MCQ trap topic — questions frequently list several parties and ask which ONE is not a related party, testing exactly the exclusions (e.g. two co-venturers simply because they share a joint venture; a director's relative who has no significant influence; a normal-course lender/banker). Make sure this topic's keywords and signals specifically capture "which of the following is NOT a related party" style phrasing, since it's a very recognisable question pattern distinct from T4.3 (which tests who IS a related party).
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 8 of 10 — M1-C4-U5 — AS 20 Earnings Per Share

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U5_ Accounting Standard 20 Earnings Per Share.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U5-T5.1 | Introduction | 4.95 |
| M1-C4-U5-T5.2 | Definition of the terms used in AS 20 | 4.96 |
| M1-C4-U5-T5.3 | Earnings — Basic | 4.98 |
| M1-C4-U5-T5.4 | Per share — Basic | 4.99 |
| M1-C4-U5-T5.5 | Shares issued in a scheme of Amalgamation | 4.101 |
| M1-C4-U5-T5.6 | Diluted Earnings Per Share | 4.105 |
| M1-C4-U5-T5.7 | Earnings — Diluted | 4.106 |
| M1-C4-U5-T5.8 | Per share — Diluted | 4.107 |
| M1-C4-U5-T5.9 | Dilutive Potential Equity Shares | 4.110 |
| M1-C4-U5-T5.10 | Restatement | 4.112 |
| M1-C4-U5-T5.11 | Presentation | 4.112 |
| M1-C4-U5-T5.12 | Disclosure | 4.113 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U5_ Accounting Standard 20 Earnings Per Share.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U5-T5.1 Introduction (4.95); M1-C4-U5-T5.2 Definition of the terms used in AS 20 (4.96); M1-C4-U5-T5.3 Earnings – Basic (4.98); M1-C4-U5-T5.4 Per share – Basic (4.99); M1-C4-U5-T5.5 Shares issued in a scheme of Amalgamation (4.101); M1-C4-U5-T5.6 Diluted Earnings Per Share (4.105); M1-C4-U5-T5.7 Earnings – Diluted (4.106); M1-C4-U5-T5.8 Per share – Diluted (4.107); M1-C4-U5-T5.9 Dilutive Potential Equity Shares (4.110); M1-C4-U5-T5.10 Restatement (4.112); M1-C4-U5-T5.11 Presentation (4.112); M1-C4-U5-T5.12 Disclosure (4.113)`
>
> **Important false-positive warning:** "weighted average number of shares" appears in this unit (T5.4, T5.9) as the core EPS denominator computation, but the *identical phrase* also appears in completely unrelated contexts elsewhere in the syllabus — e.g. AS 2 questions about weighted-average *inventory cost formula* have nothing to do with EPS. Make T5.4's keywords specific enough to distinguish "weighted average number of *shares*" (this unit) from "weighted average *cost*" (AS 2, different unit) so a later automated tagger doesn't confuse the two just because both contain the words "weighted average."
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings, paying particular attention to T5.4 (bonus issue/rights issue adjustments to the weighted-average share count — a very common numerical trap) and T5.6–T5.9 (diluted EPS via convertible instruments/options — the highest-complexity computational topic in this unit).
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 9 of 10 — M1-C4-U6 — AS 24 Discontinuing Operations

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U6_ Accounting Standard 24 Discontinuing Operations.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U6-T6.1 | Introduction | 4.125 |
| M1-C4-U6-T6.2 | Discontinuing Operation | 4.126 |
| M1-C4-U6-T6.3 | Initial Disclosure Event | 4.129 |
| M1-C4-U6-T6.4 | Recognition and Measurement | 4.130 |
| M1-C4-U6-T6.5 | Presentation and Disclosure | 4.130 |
| M1-C4-U6-T6.6 | Updating the Disclosures | 4.131 |
| M1-C4-U6-T6.7 | Separate Disclosure for Each Discontinuing Operation | 4.132 |
| M1-C4-U6-T6.8 | Presentation of The Required Disclosures | 4.132 |
| M1-C4-U6-T6.9 | Restatement of Prior Periods | 4.133 |
| M1-C4-U6-T6.10 | Disclosure in Interim Financial Reports | 4.133 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U6_ Accounting Standard 24 Discontinuing Operations.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U6-T6.1 Introduction (4.125); M1-C4-U6-T6.2 Discontinuing Operation (4.126); M1-C4-U6-T6.3 Initial Disclosure Event (4.129); M1-C4-U6-T6.4 Recognition and Measurement (4.130); M1-C4-U6-T6.5 Presentation and Disclosure (4.130); M1-C4-U6-T6.6 Updating the Disclosures (4.131); M1-C4-U6-T6.7 Separate Disclosure for Each Discontinuing Operation (4.132); M1-C4-U6-T6.8 Presentation of The Required Disclosures (4.132); M1-C4-U6-T6.9 Restatement of Prior Periods (4.133); M1-C4-U6-T6.10 Disclosure in Interim Financial Reports (4.133)`
>
> **Cross-chapter link to flag:** T6.10 (Disclosure in Interim Financial Reports) directly overlaps with AS 25 (Interim Financial Reporting, the next unit in this batch) — a question could plausibly test both units' disclosure rules together. Note this explicitly in T6.10's `notes` field.
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings, paying attention to T6.2 (the specific quantitative/qualitative criteria distinguishing a genuine "discontinuing operation" from a mere restructuring) since that's the classic scenario-MCQ trap in this unit.
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## Unit 10 of 10 — M1-C4-U7 — AS 25 Interim Financial Reporting

**File to open:** `books/concept-book/raw_icai_study_materials/M1_C4_U7_ Accounting Standard 25 Interim Financial Reporting.md`

**Topic scaffold:**
| Topic ID | Topic Name | Page |
|---|---|---|
| M1-C4-U7-T7.1 | Introduction | 4.141 |
| M1-C4-U7-T7.2 | Definitions of the terms used under the Accounting Standard | 4.142 |
| M1-C4-U7-T7.3 | Content of an Interim Financial Report | 4.142 |
| M1-C4-U7-T7.4 | Form and Content of Interim Financial Statements | 4.143 |
| M1-C4-U7-T7.5 | Selected Explanatory Notes | 4.143 |
| M1-C4-U7-T7.6 | Periods for which Interim Financial Statements are required to be presented | 4.145 |
| M1-C4-U7-T7.7 | Materiality | 4.145 |
| M1-C4-U7-T7.8 | Disclosure in Annual Financial Statements | 4.148 |
| M1-C4-U7-T7.9 | Accounting Policies | 4.148 |
| M1-C4-U7-T7.10 | Revenue Received Seasonally or Occasionally | 4.150 |
| M1-C4-U7-T7.11 | Cost Incurred Unevenly During the Financial Year | 4.150 |
| M1-C4-U7-T7.12 | Use of Estimates | 4.150 |
| M1-C4-U7-T7.13 | Restatement of Previously Reported Interim Periods | 4.151 |
| M1-C4-U7-T7.14 | Transitional Provision | 4.151 |
| M1-C4-U7-T7.15 | Applicability of AS 25 to Interim Financial Results | 4.151 |

**Prompt:**
> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `books/concept-book/raw_icai_study_materials/M1_C4_U7_ Accounting Standard 25 Interim Financial Reporting.md`
>
> This unit's known topic breakdown is:
> `M1-C4-U7-T7.1 Introduction (4.141); M1-C4-U7-T7.2 Definitions of the terms used under the Accounting Standard (4.142); M1-C4-U7-T7.3 Content of an Interim Financial Report (4.142); M1-C4-U7-T7.4 Form and Content of Interim Financial Statements (4.143); M1-C4-U7-T7.5 Selected Explanatory Notes (4.143); M1-C4-U7-T7.6 Periods for which Interim Financial Statements are required to be presented (4.145); M1-C4-U7-T7.7 Materiality (4.145); M1-C4-U7-T7.8 Disclosure in Annual Financial Statements (4.148); M1-C4-U7-T7.9 Accounting Policies (4.148); M1-C4-U7-T7.10 Revenue Received Seasonally or Occasionally (4.150); M1-C4-U7-T7.11 Cost Incurred Unevenly During the Financial Year (4.150); M1-C4-U7-T7.12 Use of Estimates (4.150); M1-C4-U7-T7.13 Restatement of Previously Reported Interim Periods (4.151); M1-C4-U7-T7.14 Transitional Provision (4.151); M1-C4-U7-T7.15 Applicability of AS 25 to Interim Financial Results (4.151)`
>
> **Cross-chapter link already confirmed in a prior audit:** a real exam question was found treating "a change in depreciation method mid-year" as an AS 10/AS 5 issue embedded inside a broader AS 25 interim-reporting question — testing specifically whether such a change should be applied retrospectively or prospectively within the interim reporting context (T7.12 Use of Estimates / T7.9 Accounting Policies). Make sure these two topics' keywords capture "change in depreciation method", "change in accounting estimate mid-year", and "interim period restatement" so this kind of embedded cross-reference gets caught.
>
> For EACH topic ID, extract 5–12 specific keywords and 2–4 typical question-signal phrasings, paying attention to T7.10/T7.11 (seasonal revenue and unevenly-incurred costs — the classic numerical trap in this unit: should a cost incurred once a year be spread across interim periods or expensed when incurred?).
>
> Do NOT invent concepts not actually present in the attached file.
>
> Output as JSON matching the schema shown at the top of `books/question-bank/metadata-index/phase0-batch1-prompts.md`.

---

## After you run all 10

Bring back all 10 JSON outputs (as separate files or pasted inline) and I'll do the Tier 3 review pass — checking keyword specificity, catching anything too generic, adding any unnumbered-section topics the tool found, and merging everything into one `topic-keyword-index.json` before Batch 2 starts.
