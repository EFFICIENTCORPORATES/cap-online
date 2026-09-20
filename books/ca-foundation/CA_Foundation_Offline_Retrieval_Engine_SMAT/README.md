# CA Foundation Offline Retrieval Engine — Corrected V2

## Purpose

This is a deterministic, fully offline Python retrieval system for the structured CA Foundation Beautified Markdown corpus. The preparation layer may have used PDF comparison to classify the ICAI material, but routine retrieval in this package does **not** require AI.

The bundled corpus contains **37 Beautified Markdown files**. Retrieval is based on explicit `ICAI_BLOCK` metadata plus a source-verified semantic correction registry for Examples.

## What was corrected from V1

The earlier tool accurately counted what had been tagged, but the upstream Example classification was incomplete/broad. The corrected engine therefore does not trust legacy Example blocks. It replaces them at load time with a **PDF-derived 53-item Example registry**.

The following source-specific corrections are also included:

- Bank Reconciliation Statement Illustration 1 is now separated into an Illustration Question and an Illustration Solution; the later `(x) Errors` subsection is outside the Illustration.
- Illustration totals now reconcile to **235 questions + 235 solutions**.
- Rectification of Errors Theory Question 3 has its own question pair key and an explicit `answer_ref_pair_key` to source Answer 2 because ICAI does not print a separately numbered Answer 3 and the relevant discussion is contained in Answer 2.
- Result messages distinguish **source items** from returned question/answer blocks, so 269 MCQs + 269 answers is reported as 269 source MCQs, not 538 MCQs.

## Independently audited source-item counts used by the tool

| Category | Source-item count |
|---|---:|
| Examples | **53** |
| Illustrations | **235** |
| Illustration Solutions | **235** |
| MCQs | **269** |
| Practical Questions | **79** |
| Theory retrieval blocks | **79** |
| True/False statements | **307** |
| Scenario/SBQ questions | **0** |

`Theory retrieval blocks = 79` is deliberately described as a retrieval-block count. At least one ICAI parent theory question contains multiple separately retrievable subparts, and source answer numbering has anomalies in a few Units.

## Example source registry

The file `data/semantic_registry/example_registry.json` contains one authoritative record for every source Example found during the PDF audit. It preserves:

- Paper, Module, Chapter and Unit;
- source PDF;
- physical PDF page span;
- ICAI printed-page span;
- source Example number when one exists;
- internal deterministic sequence when ICAI leaves it unnumbered;
- full source Example content;
- source-emphasis/layout information;
- a safe Question/Solution derivative only when the source boundary can be separated without guessing.

The 53 Examples are distributed across 12 source files. See `CORRECTION_AUDIT_REPORT.md` for the complete breakdown.

## Supported requests

Examples include:

```text
Give me all Examples
Give me all Examples from Chapter 3
Give me all MCQs
Give me all MCQs from Chapter 3 with answers
Give me all theoretical questions
Give me all practical questions
Give me all Illustrations
Give me only Illustration questions
Give me Illustration questions with solutions
Give me all questions from Paper 1 Module 2
Give me everything from Unit 4
```

Hierarchy filters supported: Paper, Module, Chapter, Unit and Topic.

## Output structure

Generated Markdown is grouped by Paper → Chapter → Unit/Chapter Scope. Every item retains source PDF and page provenance. When answers/solutions are requested, the tool joins them using source-scoped pair keys, preventing `illustration:1` from one Unit from being matched to another Unit.

## Running the tool

### GUI

```text
run_gui.bat
```

### Interactive terminal

```text
run_tool.bat
```

### Direct CLI

```bat
python ca_retriever.py --query "Give me all Examples" -o outputs\all_examples.md
```

### Presets

```bat
python ca_retriever.py --preset examples -o outputs\examples.md
python ca_retriever.py --preset mcq --with-answers -o outputs\mcq_with_answers.md
python ca_retriever.py --preset illustration_questions --chapter 2 -o outputs\c2_illustration_questions.md
```

## Use another folder of Beautified MDs

You may point the CLI to a different folder:

```bat
python ca_retriever.py --data "D:\CA Foundation\parsed_md" --query "Give me all MCQs"
```

The corrected exhaustive Example registry is bundled relative to the default `data/parsed_md` folder. If you replace the dataset with a different corpus, regenerate/provide an appropriate semantic registry rather than assuming the bundled 53-item registry applies to unrelated files.

## Offline/privacy characteristics

- no network request;
- no API key;
- no cloud AI;
- no vector database;
- no third-party Python dependency;
- deterministic metadata filtering;
- plain Markdown/JSON outputs.

## Validation

Run:

```bat
python ca_retriever.py --validate-data
run_tests.bat
```

The corrected release has dedicated regression checks for the previously missed Example Units, Bank Reconciliation Illustration 1, source-item counts, pairing, hierarchy filtering and source provenance.
