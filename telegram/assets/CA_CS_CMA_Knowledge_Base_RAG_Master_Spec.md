# CA / CS / CMA Knowledge Base & RAG --- Master Processing Specification

## 0. Purpose

This document defines the complete processing architecture for
converting approximately 1,000 CA, CS and CMA study-material PDFs into a
structured, searchable and traceable knowledge base.

The system must support:

-   Chapter/topic/subtopic identification
-   Structure-aware PDF → Markdown conversion
-   Preservation of source pages and document identity
-   Semantic chunking
-   Embeddings and vector search
-   Hybrid RAG
-   MCQ generation
-   Descriptive-answer evaluation
-   Student answer checking
-   Source/page references
-   Future AI tutor and MCP access
-   Reproducible processing and re-processing
-   Different document structures across CA, CS and CMA

The central design principle is:

> **Do not treat the PDFs as one homogeneous corpus. Preserve the native
> structure of each course/institute while converting everything into
> one common internal knowledge model.**

------------------------------------------------------------------------

# 1. Overall Architecture

``` text
                         ORIGINAL PDFs
                              |
                              v
                  PDF metadata / registration
                              |
                              v
                    PDF → Markdown conversion
                              |
                              v
                    Structure-aware parser
                              |
              +---------------+---------------+
              |                               |
              v                               v
       Deterministic rules              AI-assisted analysis
       headings / numbering             structure interpretation
       TOC / pages / patterns            ambiguity resolution
              |                               |
              +---------------+---------------+
                              |
                              v
                    Canonical JSON / DB model
                              |
                              v
                    Semantic content chunks
                              |
                              v
                       Embedding model
                              |
                              v
                  PostgreSQL + pgvector
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
         Hybrid RAG       MCQ Engine      Answer Checker
             |                |                |
             +----------------+----------------+
                              |
                              v
                     AI / MCP / Applications
```

------------------------------------------------------------------------

# 2. Do NOT Make the PDF the Database

The original PDF must remain the **immutable source document**.

Do not modify it.

Maintain three distinct layers:

``` text
RAW SOURCE
    ↓
PROCESSED REPRESENTATION
    ↓
KNOWLEDGE DATABASE
```

### RAW SOURCE

Original PDFs exactly as received.

### PROCESSED REPRESENTATION

Markdown, extracted metadata, parsed structure and JSON.

### KNOWLEDGE DATABASE

PostgreSQL tables containing:

-   courses
-   institutes
-   levels
-   subjects
-   chapters
-   topics
-   subtopics
-   content blocks
-   source pages
-   embeddings
-   questions
-   answers
-   marking schemes
-   references

This separation allows the entire database to be rebuilt if the parsing
logic changes.

------------------------------------------------------------------------

# 3. Recommended Physical File Structure

Use a directory structure such as:

``` text
knowledge_base/
│
├── README.md
├── config/
│   ├── global.yaml
│   ├── ca.yaml
│   ├── cs.yaml
│   └── cma.yaml
│
├── raw/
│   ├── CA/
│   │   ├── Foundation/
│   │   ├── Intermediate/
│   │   └── Final/
│   │
│   ├── CS/
│   │   ├── CSEET/
│   │   ├── Executive/
│   │   └── Professional/
│   │
│   └── CMA/
│       ├── Foundation/
│       ├── Intermediate/
│       └── Final/
│
├── markdown/
│   ├── CA/
│   ├── CS/
│   └── CMA/
│
├── parsed/
│   ├── CA/
│   ├── CS/
│   └── CMA/
│
├── chunks/
│   ├── CA/
│   ├── CS/
│   └── CMA/
│
├── manifests/
│   ├── documents.json
│   ├── chapters.json
│   ├── topics.json
│   └── processing_log.json
│
├── questions/
│   ├── mcqs/
│   ├── descriptive/
│   └── marking_schemes/
│
└── logs/
    ├── parser/
    ├── OCR/
    └── validation/
```

------------------------------------------------------------------------

# 4. File Naming Convention

Do not depend on filenames alone for meaning.

A filename can contain useful hints, but metadata must be authoritative.

Recommended:

``` text
<course>_<level>_<subject>_<document-code>_<edition>.pdf
```

Example:

``` text
CA_Intermediate_Accounting_Module-04_2026.pdf
```

If the official filename must be retained, store it as
`original_filename` and create your own internal `document_id`.

Example:

``` text
document_id:
CA-INT-ACC-M04-2026-00017

original_filename:
Study Material Chapter 4.pdf
```

Never use a filename as the permanent primary key.

------------------------------------------------------------------------

# 5. Document Registration

Before parsing any PDF, create a document-registration record.

Minimum metadata:

``` text
document_id
course
institute
level
group/module
subject
paper_code
document_type
edition
academic_year
original_filename
source_path
file_hash
page_count
processing_status
```

Example:

``` json
{
  "document_id": "CA-INT-ACC-M04-2026-00017",
  "course": "CA",
  "institute": "ICAI",
  "level": "Intermediate",
  "subject": "Accounting",
  "paper_code": "P-1",
  "document_type": "Study Material",
  "edition": "2026",
  "academic_year": "2026-27",
  "original_filename": "Module 4.pdf",
  "file_hash": "...",
  "page_count": 184,
  "processing_status": "registered"
}
```

The `file_hash` is important for detecting duplicate files and changed
editions.

------------------------------------------------------------------------

# 6. PDF → Markdown Conversion

The existing Python PDF-to-Markdown converter should produce Markdown
that is as structurally faithful as possible.

The conversion stage should NOT try to solve every semantic problem.

Its primary responsibility is:

> **Preserve the information present in the PDF.**

It should try to preserve:

-   headings
-   subheadings
-   numbering
-   paragraphs
-   bullet lists
-   numbered lists
-   tables
-   formulas
-   examples
-   notes
-   illustrations
-   page boundaries
-   footnotes
-   captions
-   references
-   warnings / important notes

------------------------------------------------------------------------

# 7. Recommended Markdown Structure

The Markdown should contain explicit document metadata at the beginning.

Example:

``` yaml
---
document_id: CA-INT-ACC-M04-2026-00017
course: CA
institute: ICAI
level: Intermediate
subject: Accounting
paper_code: P-1
document_type: Study Material
edition: 2026
source_file: Module 4.pdf
---
```

Then:

``` markdown
# Chapter 4 — Title

## 4.1 Introduction

Content...

## 4.2 Topic Title

Content...

### 4.2.1 Subtopic Title

Content...
```

However, this structure is only a preferred representation.

The parser MUST NOT assume that every document follows it.

------------------------------------------------------------------------

# 8. Page Preservation Is Mandatory

Page information is critical because the final system must be able to
answer:

> Where exactly did this information come from?

Therefore the Markdown should preserve page boundaries.

Recommended notation:

``` markdown
<!-- PAGE: 42 -->

## 4.2 Determination of Residential Status

Content...

<!-- PAGE: 43 -->

Content continues...
```

If the PDF page number and printed textbook page number differ, preserve
both when possible:

``` markdown
<!-- PDF_PAGE: 43 | PRINTED_PAGE: 41 -->
```

Do not discard page information during Markdown conversion.

------------------------------------------------------------------------

# 9. The Parser Must NOT Assume One Universal Structure

This is one of the most important rules.

The corpus contains:

-   CA
-   CS
-   CMA

and their material can differ significantly.

Even within one course, different subjects and publications may use
different formatting conventions.

Therefore:

> **Use a common output schema, but allow course/document-specific
> parsing strategies.**

Think:

``` text
COMMON KNOWLEDGE MODEL
          ^
          |
    Course-specific
    parsing adapters
          ^
    +-----+-----+
    |     |     |
   CA    CS    CMA
```

------------------------------------------------------------------------

# 10. CA Parsing Expectations

CA study material often has relatively strong hierarchy and numbering.

Possible patterns:

``` text
Chapter 4
4.1
4.2
4.2.1
4.2.2
```

or:

``` text
CHAPTER 4
4.1 Introduction
4.2 ...
```

The parser should strongly consider:

-   chapter headings
-   numbered headings
-   table of contents
-   repeated heading styles
-   page headers
-   page footers
-   module boundaries

But it must still validate the hierarchy.

------------------------------------------------------------------------

# 11. CS Parsing Expectations

CS material may have:

-   different module structures
-   units
-   lessons
-   parts
-   topics
-   subtopics
-   numbered sections
-   unnumbered headings

Therefore the parser must NOT insist on:

``` text
Chapter → Topic → Subtopic
```

if the source doesn't contain that structure.

It may instead detect:

``` text
Module → Lesson → Section → Subsection
```

and map this into the common knowledge model.

For example:

``` text
native_structure:
Module
  Lesson
    Section
      Subsection
```

can become:

``` text
canonical_structure:
Chapter-equivalent
  Topic
    Subtopic
      Content
```

while retaining the original labels:

``` text
native_level = "Lesson"
canonical_level = "chapter"
```

------------------------------------------------------------------------

# 12. CMA Parsing Expectations

CMA material may have another hierarchy.

It may contain:

``` text
Chapter
Unit
Topic
Illustration
Practice Question
Summary
```

or other combinations.

Again:

> Do not force CMA into the CA hierarchy.

Instead:

1.  Detect the native hierarchy.
2.  Preserve it.
3.  Map it to the common canonical model.
4.  Record the original/native label.

------------------------------------------------------------------------

# 13. What If There Is No Explicit Topic?

This is a critical parser rule.

Suppose the PDF has:

``` text
CHAPTER 4
RESIDENTIAL STATUS

[large block of content]

Conditions for determining residential status

[content]

Exceptions

[content]
```

There may be no `4.1`, `4.2`, etc.

The parser must NOT invent:

``` text
4.1
4.2
4.3
```

as if those numbers existed in the source.

Instead, create:

``` text
topic_number: null
topic_title: "Conditions for determining residential status"
topic_source: "inferred"
```

and retain the exact source heading.

------------------------------------------------------------------------

# 14. Three Types of Structural Labels

Every chapter/topic/subtopic should have a `source_type` or equivalent.

Recommended values:

``` text
explicit
inferred
generated
unknown
```

### explicit

Clearly present in the source.

Example:

``` text
4.2 Determination of Residential Status
```

### inferred

Not explicitly numbered, but strongly supported by formatting/content.

Example:

``` text
Conditions for determining residential status
```

is clearly a section heading even though it has no number.

### generated

Created by the system for organizational purposes.

Example:

``` text
Unclassified Content — Chapter 4
```

This must never be presented as an official textbook heading.

### unknown

The parser cannot confidently determine the structure.

------------------------------------------------------------------------

# 15. Never Allow the AI to Silently Invent Structure

If the parser is uncertain:

``` text
confidence < threshold
```

then it should create a validation item.

Example:

``` json
{
  "document_id": "CA-00123",
  "page": 67,
  "issue_type": "ambiguous_heading",
  "text": "Conditions applicable to certain individuals",
  "suggested_interpretation": "topic",
  "confidence": 0.61,
  "requires_human_review": true
}
```

The system should maintain a review queue.

------------------------------------------------------------------------

# 16. Human-in-the-Loop Is a Feature, Not a Failure

The parser should be allowed to ask for clarification.

Examples:

> "I found two possible chapter boundaries. Which one is correct?"

> "This heading appears to be a topic, but there is no numbering. Should
> it be treated as a topic?"

> "The table of contents says 4.2, but the body heading says 4.3. Which
> should be treated as authoritative?"

The workflow should support:

``` text
AUTO-PROCESS
    ↓
CONFIDENT → ACCEPT
    ↓
UNCERTAIN → REVIEW QUEUE
    ↓
USER DECISION
    ↓
STORE DECISION
    ↓
CONTINUE
```

Do not stop the entire 1,000-PDF processing job because of one
ambiguity.

------------------------------------------------------------------------

# 17. Parser Instruction / System Prompt

The structural parser should be given a persistent instruction similar
to the following:

``` text
You are a document-structure extraction and validation engine for
educational study material covering CA, CS and CMA.

Your task is NOT to rewrite the study material.

Your task is to identify and preserve the structure that exists in the
source document.

Rules:

1. Never invent an official chapter, topic, subtopic or numbering that
   is not supported by the source.

2. Prefer explicit headings and numbering over inferred structure.

3. Use the table of contents as supporting evidence, but validate it
   against the actual document body.

4. Preserve the original heading text exactly whenever possible.

5. Preserve the original numbering exactly whenever present.

6. Do not assume that CA, CS and CMA use the same hierarchy.

7. First identify the native structure of the document.

8. Then map the native structure into the canonical knowledge model.

9. Preserve the native label in addition to the canonical label.

10. If a heading is unnumbered but clearly functions as a section/topic
    heading, classify it as inferred rather than pretending that the
    source provided a number.

11. If the document has no clear topic/subtopic structure, do not
    fabricate one merely to make the hierarchy complete.

12. Content must always remain attached to its nearest reliable parent
    heading.

13. Preserve page references.

14. Do not merge content across unrelated sections.

15. Do not silently correct substantive textbook content.

16. If OCR or PDF extraction appears incorrect, flag it for review.

17. If two interpretations are plausible and neither is clearly
    superior, return an ambiguity record instead of guessing.

18. Use confidence scores for inferred classifications.

19. Ask for human clarification when the ambiguity materially affects
    the knowledge hierarchy.

20. Output machine-readable structured data in addition to human-readable
    explanations.

21. The source document remains authoritative. The AI is an interpreter,
    not the author of the study material.

22. Never use external knowledge to create missing textbook content
    during structural parsing.

23. Examples, illustrations, practice questions, summary boxes, notes,
    case studies and annexures must be separately classified when
    identifiable.

24. Preserve formulas, tables and lists as structured content whenever
    possible.

25. When uncertain, prefer preserving raw content over losing information.
```

------------------------------------------------------------------------

# 18. Parser Output Schema

The parser should produce structured JSON before database insertion.

Example:

``` json
{
  "document_id": "CA-INT-ACC-M04-2026-00017",
  "native_structure": {
    "top_level": "Chapter",
    "second_level": "Section",
    "third_level": "Subsection"
  },
  "chapters": [
    {
      "chapter_number": "4",
      "chapter_title": "Residential Status",
      "source_type": "explicit",
      "confidence": 0.99,
      "topics": [
        {
          "topic_number": "4.1",
          "topic_title": "Introduction",
          "source_type": "explicit",
          "confidence": 0.99
        },
        {
          "topic_number": null,
          "topic_title": "Conditions for determining residential status",
          "source_type": "inferred",
          "confidence": 0.87
        }
      ]
    }
  ]
}
```

------------------------------------------------------------------------

# 19. Canonical Knowledge Hierarchy

The common database model should be:

``` text
Course
  ↓
Institute
  ↓
Level
  ↓
Subject
  ↓
Chapter / Chapter-equivalent
  ↓
Topic / Topic-equivalent
  ↓
Subtopic / Subtopic-equivalent
  ↓
Content Block
  ↓
Source Location
```

Do not make every level mandatory.

For example:

``` text
Chapter
  ↓
Content
```

is valid if no topic exists.

Likewise:

``` text
Chapter
  ↓
Topic
  ↓
Content
```

is valid.

------------------------------------------------------------------------

# 20. Content Blocks

After structure extraction, divide content into semantic chunks.

Do NOT split text randomly.

Preferred order:

``` text
Heading boundary
    ↓
Subheading boundary
    ↓
Paragraph boundary
    ↓
Sentence boundary
    ↓
Token limit
```

A chunk should preferably represent one coherent idea.

Avoid splitting:

-   a definition from its qualification
-   a rule from its exception
-   a formula from its explanation
-   a question from its options
-   a table from its heading
-   a legal provision from its conditions

------------------------------------------------------------------------

# 21. Chunk Size

Do not hard-code one universal number initially.

Test approximately:

``` text
500–1,000 tokens
```

as a starting range, but use semantic boundaries.

A chunk may therefore be:

``` text
420 tokens
```

or:

``` text
780 tokens
```

or:

``` text
950 tokens
```

That is acceptable.

The goal is **coherent meaning**, not equal-sized chunks.

------------------------------------------------------------------------

# 22. Chunk Overlap

Use overlap only when useful.

Typical starting point:

``` text
10–20% overlap
```

But structure-aware chunking should reduce the need for aggressive
overlap.

Do not duplicate entire sections merely to increase retrieval
performance.

Evaluate this empirically.

------------------------------------------------------------------------

# 23. Content Block Metadata

Every content block should retain:

``` text
content_block_id
document_id
course_id
subject_id
chapter_id
topic_id
subtopic_id
native_section_type
native_section_number
native_section_title
content_type
text
page_start
page_end
source_reference
sequence
token_count
hash
embedding_model
embedding
```

Useful `content_type` values:

``` text
paragraph
definition
rule
formula
example
illustration
table
list
note
warning
case_study
practice_question
summary
reference
```

------------------------------------------------------------------------

# 24. Embeddings

An embedding converts each content block into a fixed-length numerical
vector representing its semantic characteristics.

Example:

``` text
Content block
    ↓
Embedding model
    ↓
[0.12, -0.42, 0.71, ...]
```

The number of values is determined by the selected embedding model.

If the model produces 1,024 dimensions:

``` text
Every vector = 1,024 numbers
```

Do not manually choose a different dimension for individual documents.

All vectors stored in the same vector index should use the same
embedding model/dimension.

------------------------------------------------------------------------

# 25. Embedding Strategy

Keep the embedding provider interchangeable.

Implement an abstraction such as:

``` text
EmbeddingService
    ├── LocalEmbeddingService
    ├── OpenAIEmbeddingService
    ├── OtherAPIEmbeddingService
```

This allows testing:

-   local model
-   cloud API model
-   different embedding models

without redesigning the database.

Do not train an embedding model from scratch initially.

Use a proven pre-trained embedding model.

------------------------------------------------------------------------

# 26. Local Embeddings

Local embeddings can be generated on your own PC.

Advantages:

-   Data remains local during embedding
-   No per-token embedding API cost
-   Good for processing large document collections
-   Repeatable

Potential disadvantages:

-   CPU processing may be slower
-   GPU can improve throughput
-   Model selection requires benchmarking
-   You are responsible for running the model

For 1,000 PDFs, local embedding generation is very practical if the
machine is reasonably capable.

Do not assume that a powerful GPU is mandatory.

------------------------------------------------------------------------

# 27. API Embeddings

With an embedding API:

``` text
Python
   ↓
Embedding provider
   ↓
Vector returned
   ↓
PostgreSQL
```

Advantages:

-   Easy implementation
-   No local model management
-   Usually fast
-   Good quality options

Disadvantages:

-   API cost
-   Source text is sent to an external provider
-   Network dependency

For confidential/custom material, local processing may be preferable
depending on the actual privacy requirements and provider terms.

------------------------------------------------------------------------

# 28. Database Architecture

Recommended initial architecture:

``` text
Neon
  ↓
PostgreSQL
  +
pgvector
```

These are not three unrelated databases.

### PostgreSQL

The actual relational database.

Stores:

-   courses
-   subjects
-   chapters
-   topics
-   questions
-   students
-   attempts
-   answers
-   metadata

### pgvector

A PostgreSQL extension that allows vector storage and similarity search.

### Neon

A managed/serverless PostgreSQL platform.

------------------------------------------------------------------------

# 29. Do Not Introduce Neo4j Initially

Neo4j is a graph database.

It may become useful later for advanced relationships such as:

``` text
Concept A
    ↓ prerequisite of
Concept B
    ↓ tested by
Question C
    ↓ appears in
Chapter D
```

But PostgreSQL is sufficient for the initial system.

Do not add Neo4j merely because the project is called a RAG system.

------------------------------------------------------------------------

# 30. Hybrid Retrieval

Do not rely exclusively on vector similarity.

Use:

``` text
Metadata filtering
        +
Full-text / keyword search
        +
Vector similarity
```

Example:

``` text
Student question:
"What is the treatment of capital introduced by a partner?"
```

First filter:

``` text
Course = CA
Subject = relevant subject
Chapter = relevant chapter
```

Then perform semantic search within the relevant corpus.

This is much safer than searching all 1,000 PDFs blindly.

------------------------------------------------------------------------

# 31. Source Traceability

Every answer generated by the AI should be traceable back to source
material.

A retrieved result should contain:

``` text
Course
Subject
Chapter
Topic
Subtopic
Document
Page
Content Block ID
```

Example:

``` text
Source:
CA Intermediate
Accounting
Chapter 4
Topic 4.2
Pages 42–43
Module 4
```

The final AI response should be able to cite this source.

------------------------------------------------------------------------

# 32. MCQ Generation

Do not ask an LLM:

``` text
Generate 100 MCQs from this PDF.
```

Instead:

``` text
User selects:
Course
Subject
Chapter
Topics
Number of questions
Difficulty
Question type
```

Python retrieves the relevant knowledge blocks.

Then the AI receives only the required context.

Each generated MCQ should store:

``` text
question_id
question
options
correct_answer
explanation
course
subject
chapter
topic
subtopic
difficulty
question_type
marks
estimated_time
source_content_block_ids
source_pages
generation_model
generation_timestamp
validation_status
```

------------------------------------------------------------------------

# 33. MCQ Validation

Generated MCQs should NOT automatically become trusted questions.

Use:

``` text
Generate
   ↓
Validate against source
   ↓
Check answer
   ↓
Check distractors
   ↓
Check ambiguity
   ↓
Check source reference
   ↓
Human review if required
   ↓
Publish
```

This is especially important for law, taxation and accounting.

------------------------------------------------------------------------

# 34. Descriptive Answer Checker

The student can upload:

``` text
Handwritten answer PDF
```

Pipeline:

``` text
Handwritten PDF
      ↓
OCR / handwriting recognition
      ↓
Extracted text
      ↓
Question identification
      ↓
Topic identification
      ↓
Retrieve model answer
      ↓
Retrieve marking scheme
      ↓
Retrieve authoritative source
      ↓
AI evaluation
      ↓
Marks + feedback + references
```

------------------------------------------------------------------------

# 35. Do Not Give the AI the Entire Textbook

For answer checking, the LLM should receive only:

``` text
Question
+
Student answer
+
Model answer
+
Marking scheme
+
Relevant source blocks
+
Relevant metadata
```

This reduces:

-   token usage
-   cost
-   latency
-   irrelevant context
-   hallucination risk

------------------------------------------------------------------------

# 36. Deterministic vs AI Responsibilities

Use Python/database logic whenever possible.

### Python / SQL

-   document identification
-   metadata
-   chapter IDs
-   topic IDs
-   page numbers
-   question IDs
-   marks
-   storage
-   retrieval filters
-   token counting
-   hashing
-   duplicate detection
-   basic keyword comparison
-   scoring calculations
-   audit logs

### AI

-   ambiguous structure interpretation
-   semantic classification
-   concept identification
-   answer quality assessment
-   nuanced marking
-   explanation generation
-   feedback generation

This division keeps the system cheaper and more reliable.

------------------------------------------------------------------------

# 37. MCP

MCP should be considered an interface layer, not the core database.

Later, expose tools such as:

``` text
search_knowledge()
get_chapter()
get_topic()
get_source()
get_question()
get_model_answer()
get_marking_scheme()
check_answer()
generate_mcqs()
```

Then an AI can request only the information it needs.

MCP itself does not reduce token costs automatically.

The savings come from **selective retrieval and tool-based access**.

------------------------------------------------------------------------

# 38. Suggested PostgreSQL Tables

Initial schema:

``` text
courses
institutes
levels
subjects
documents
document_versions
chapters
topics
subtopics
content_blocks
content_block_sources
processing_runs
processing_issues

questions
question_options
question_sources
marking_schemes
question_concepts

students
answer_submissions
answer_text
answer_evaluations
answer_evidence
```

Later:

``` text
concepts
concept_relationships
learning_paths
student_progress
```

------------------------------------------------------------------------

# 39. Processing Pipeline

The production pipeline should be:

``` text
STEP 1
Register PDF

STEP 2
Calculate file hash

STEP 3
Extract PDF metadata

STEP 4
Convert PDF → Markdown

STEP 5
Preserve page boundaries

STEP 6
Detect native document structure

STEP 7
Extract chapter/topic/subtopic candidates

STEP 8
Validate structure with deterministic rules

STEP 9
Use AI for ambiguous cases

STEP 10
Create canonical hierarchy

STEP 11
Create content blocks

STEP 12
Attach metadata to every block

STEP 13
Generate embeddings

STEP 14
Store in PostgreSQL + pgvector

STEP 15
Run retrieval tests

STEP 16
Mark document as validated

STEP 17
Make it available to RAG
```

------------------------------------------------------------------------

# 40. Processing Status

Each document should have a state machine.

Example:

``` text
REGISTERED
    ↓
CONVERTED
    ↓
PARSED
    ↓
STRUCTURE_VALIDATED
    ↓
CHUNKED
    ↓
EMBEDDED
    ↓
INDEXED
    ↓
QA_VALIDATED
    ↓
PUBLISHED
```

If something fails:

``` text
PROCESSING_ERROR
STRUCTURE_REVIEW
OCR_REVIEW
SOURCE_REVIEW
```

This makes the 1,000-document process manageable.

------------------------------------------------------------------------

# 41. Human Review Dashboard

Create a simple Python web application later with:

``` text
Documents requiring review: 27

CA
  4 ambiguous structures

CS
  12 ambiguous structures

CMA
  11 ambiguous structures
```

For each:

``` text
PDF page
Original extracted Markdown
Parser interpretation
Confidence
Alternative interpretation
Approve
Reject
Edit
```

Every human correction should be saved.

------------------------------------------------------------------------

# 42. Store Human Decisions

If you correct:

``` text
"Conditions applicable to individuals"
```

from:

``` text
subtopic
```

to:

``` text
topic
```

store that decision.

Do not make the parser rediscover the same fact next time.

Possible table:

``` text
parser_corrections

document_id
page
source_text_hash
original_classification
corrected_classification
user_decision
timestamp
```

This will gradually improve the processing system.

------------------------------------------------------------------------

# 43. Important Principle for Different Courses

The system should have:

``` text
COMMON CANONICAL SCHEMA
```

but:

``` text
COURSE-SPECIFIC PARSING RULES
```

and potentially:

``` text
DOCUMENT-TYPE-SPECIFIC RULES
```

Example:

``` text
CA
 ├── ICAI Study Material Parser
 └── ICAI Revision Material Parser

CS
 ├── ICSI Study Material Parser
 └── ICSI Supplement Parser

CMA
 ├── ICMAI Study Material Parser
 └── ICMAI Practice Material Parser
```

This is far better than one giant parser full of assumptions.

------------------------------------------------------------------------

# 44. Recommended Configuration Files

Example:

``` yaml
course: CA

institute: ICAI

structure_patterns:
  chapter:
    - "^CHAPTER\\s+\\d+"
  topic:
    - "^\\d+\\.\\d+"
  subtopic:
    - "^\\d+\\.\\d+\\.\\d+"

confidence_thresholds:
  explicit: 0.95
  inferred: 0.80
  human_review: 0.70
```

CS and CMA can have different configuration.

The parser should load the appropriate configuration based on document
metadata.

------------------------------------------------------------------------

# 45. What the Parser Should Ask You

The parser should not interrupt for every tiny ambiguity.

Use three levels:

### High confidence

Automatically proceed.

### Medium confidence

Log the issue and continue if safe.

### Low confidence / materially important

Ask for human review.

Example:

``` text
Document: CS Executive – Company Law
Page: 84

I found an unnumbered heading:
"Doctrine of Indoor Management"

Possible classification:
A. Topic
B. Subtopic

Recommended: Topic
Confidence: 0.62

Please confirm.
```

Your answer is then stored as a reusable correction.

------------------------------------------------------------------------

# 46. Important Source Integrity Rule

Never let the AI silently "improve" the textbook.

For example, if the source says:

``` text
X
```

and the AI believes the legally correct answer is:

``` text
Y
```

the knowledge ingestion pipeline must preserve:

``` text
Source says X
```

and flag it for review.

Do not overwrite source material with AI knowledge.

This is critical for examination-oriented content.

------------------------------------------------------------------------

# 47. Versioning

CA/CS/CMA material changes.

Therefore, never overwrite an old edition without preserving history.

Use:

``` text
document
    ↓
document_version
```

Example:

``` text
Income Tax Module 3
   ├── 2025 edition
   └── 2026 edition
```

Questions should reference the appropriate version where necessary.

This prevents an old question from accidentally citing an updated rule.

------------------------------------------------------------------------

# 48. RAG Answer Generation

The final RAG pipeline should be:

``` text
User Question
      ↓
Question understanding
      ↓
Metadata identification
      ↓
Metadata filtering
      ↓
Keyword retrieval
      ↓
Vector retrieval
      ↓
Result ranking
      ↓
Source verification
      ↓
Small relevant context
      ↓
LLM
      ↓
Answer + citation
```

The LLM should be explicitly instructed:

``` text
Answer only from the supplied authoritative source material.

If the supplied material does not support the answer, say that
the available source does not establish the answer.

Do not invent a citation.

Do not fabricate page numbers.

Distinguish source text from inference.
```

------------------------------------------------------------------------

# 49. Anti-Hallucination Strategy

No RAG system can mathematically guarantee zero hallucinations.

Your goal should be:

``` text
Reduce unsupported generation
+
Force source grounding
+
Require citations
+
Detect unsupported claims
+
Keep authoritative source separate
```

For examination use, this is substantially more important than simply
increasing the vector dimension.

------------------------------------------------------------------------

# 50. Recommended Development Sequence

Do NOT process all 1,000 PDFs first.

Start with a pilot.

### Phase 1

Select:

``` text
5 CA PDFs
5 CS PDFs
5 CMA PDFs
```

Choose structurally different documents.

### Phase 2

Build:

``` text
PDF → Markdown
```

### Phase 3

Build:

``` text
Markdown → structure
```

### Phase 4

Build:

``` text
structure → canonical JSON
```

### Phase 5

Build:

``` text
JSON → PostgreSQL
```

### Phase 6

Build:

``` text
content blocks → embeddings → pgvector
```

### Phase 7

Test retrieval.

### Phase 8

Build MCQ generation.

### Phase 9

Build descriptive answer checking.

### Phase 10

Add MCP.

Only after this works should you process all 1,000 PDFs.

------------------------------------------------------------------------

# 51. Retrieval Evaluation

Create a test set of real questions.

For each question, manually identify the correct source passage.

Then measure:

``` text
Top-1 retrieval
Top-3 retrieval
Top-5 retrieval
Top-10 retrieval
```

For example:

``` text
Question 1 → correct source in Top 3 ✓
Question 2 → correct source in Top 5 ✓
Question 3 → correct source not retrieved ✗
```

This tells you whether the problem is:

-   chunking
-   metadata
-   embeddings
-   search
-   parser
-   source classification

rather than blindly changing the LLM.

------------------------------------------------------------------------

# 52. Final Recommended Stack

### Local processing

``` text
Python
PyMuPDF / PDF parser
Markdown
Pydantic
Regex / structural rules
Optional local LLM
```

### Database

``` text
PostgreSQL
pgvector
Neon
```

### Backend

``` text
FastAPI
Python
```

### AI

``` text
Embedding model
Small/cheap LLM
Powerful reasoning LLM
OCR/handwriting model
```

### Future

``` text
MCP
Student portal
Teacher dashboard
Question bank
AI tutor
```

------------------------------------------------------------------------

# 53. Final Mental Model

The entire system should be thought of as five layers:

``` text
LAYER 1 — SOURCE
Original PDFs

LAYER 2 — STRUCTURE
Course → Subject → Chapter → Topic → Subtopic

LAYER 3 — KNOWLEDGE
Content Blocks + Metadata + Sources

LAYER 4 — RETRIEVAL
Keyword + Vector + Metadata filtering

LAYER 5 — AI
MCQ generation
Answer evaluation
Explanation
Tutor
MCP
```

The most important rule is:

> **AI should sit on top of a well-structured knowledge base. It should
> not BE the knowledge base.**

That approach will give you much better control over accuracy, token
cost, citations, versioning and future expansion.

------------------------------------------------------------------------

# 54. Project-Specific Operating Addendum

**Status:** authoritative implementation addendum

**Added:** 2026-08-10

This section records the current repository state and the decisions made
after examining the real CA, CS and CMA files. Future agents and bots must
read this section together with the earlier conceptual specification.

Where this addendum is more specific than an earlier generic example, this
addendum takes precedence.

## 54.1 The Actual Goal

The goal is to build one reusable knowledge and question-generation
foundation for:

- CA Foundation, Intermediate and Final;
- CS CSEET, Executive and Professional;
- CMA Foundation, Intermediate and Final;
- official study material;
- faculty-owned study and revision content;
- MTP, RTP and PYQ exam material;
- faculty-created questions;
- MCQ generation and practice;
- descriptive answer evaluation;
- AI tutoring and future MCP access;
- the Question Bank Engine;
- the three Telegram bots and future white-label faculty bots.

This is not merely a PDF search system. It is a traceable academic content
system in which every generated question, answer, explanation, evaluation and
AI response can be connected back to the relevant source document, source page,
native heading, canonical topic and content block.

The governing principle is:

> Preserve the source faithfully, understand its native structure, map it into
> a common model without flattening meaningful differences, and let AI operate
> only on retrieved and traceable evidence.

## 54.2 Current Corpus State

The current Telegram Study Hub contains the first physical corpus that this
pipeline must register:

| Corpus | Current count | Notes |
|---|---:|---|
| CA Study Material | 380 | ICAI, chapter/unit-oriented files |
| CS/CMA Study Material | 646 | ICSI and ICMAI material, split from consolidated PDFs |
| Study Material total | 1,026 | Served from `telegram/assets/study_bot/Study Materials/` |
| Exam Material | 58 | Currently CA Intermediate Advanced Accounting MTP/PYQ/RTP files |
| Revision Material | 0 | Category exists but is not populated yet |
| Registered knowledge-base documents | 1,084 | Current generated manifest total |

The full source catalog is not currently a single hand-maintained Excel file.
The source artifacts are:

1. `telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx` for CA;
2. `telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx` for ICSI/ICMAI;
3. `telegram/source-docs/StudyHub_Master_Catalog.xlsx` for the current Study
   Hub delivery view.

These source catalogs must remain available because they contain different
publisher-specific facts. A generated unified JSON manifest is the machine
processing layer; it does not replace the source catalogs.

The first manifest builder is:

`telegram/tools/build_knowledge_base_catalog.py`

Its generated output is:

`telegram/source-docs/knowledge_base_documents.json`

The builder currently:

- reads the CA and CS/CMA catalogs;
- reads Exam Materials from the master catalog;
- preserves native metadata;
- creates physical-file-specific document IDs;
- calculates SHA-256 hashes;
- records PDF page counts;
- marks every document as `registered`;
- excludes the known ICSI merged lesson that has no standalone PDF;
- verifies catalog-to-disk and disk-to-catalog coverage.

The manifest is generated. It must never be hand-edited.

## 54.3 Catalog Authority and Conversion Rules

Use this authority order:

```text
Original PDF
    = content authority

Course/publisher source catalog
    = source metadata authority

knowledge_base_documents.json
    = generated registration and processing authority

Parsed structure JSON
    = interpreted structure, subject to review

Database and embeddings
    = derived searchable representations
```

The Excel catalogs remain useful for human inspection and source-specific
metadata. Python scripts are responsible for converting them into JSON. JSON
is preferred for all subsequent processing because it is deterministic,
diffable, nested, versionable and easy to validate.

Do not manually maintain a second flattened catalog. If metadata changes:

1. correct the real source catalog or its generating script;
2. rerun the relevant source-catalog builder;
3. rerun `build_knowledge_base_catalog.py`;
4. validate that every PDF has exactly one registration record;
5. continue downstream processing only after the manifest is clean.

## 54.4 Native Structures Observed in the Corpus

The courses must share a canonical model but must not share one universal
parser.

### CA native structure

CA is generally the most strongly numbered corpus:

```text
Course
  -> Level
    -> Subject
      -> Module
        -> Chapter
          -> Unit
            -> Topic
              -> Subtopic
                -> Content block
```

CA examples show learning outcomes, chapter overviews, numbered sections,
examples, illustrations, practical situations, tables, summaries and test
sections interspersed with the main explanatory text.

The existing CA topic index is a governed syllabus taxonomy, not a complete
copy of every heading in every PDF. It contains stable identifiers such as:

```text
M1-C1-U0-T1
M2-C5-U2-T7
```

The CA parser should map detected headings to this taxonomy where supported,
while retaining additional document material that is not represented in the
index.

### CS native structure

CS material commonly uses:

```text
Course
  -> Level
    -> Subject
      -> Lesson
        -> Section
          -> Subsection
            -> Content block
```

CS documents frequently include Key Concepts, Learning Objectives, Lesson
Outline, Regulatory Framework, Lesson Round-Up, Test Yourself and Further
Readings. These are meaningful content types and must not be discarded as
boilerplate.

### CMA native structure

CMA material commonly uses:

```text
Course
  -> Level
    -> Subject
      -> Module
        -> Numbered section
          -> Subsection
            -> Content block
```

Some CMA files use nested numbering such as `1.1`, `1.1.1` and `1.1.1.1`.
Others include module learning objectives, SLOB mappings, examples, legal
provisions and practical material. The parser must preserve this native depth.

### Canonical mapping

Native structures map into a flexible canonical model:

```text
course
  -> level
    -> subject
      -> chapter_equivalent
        -> topic_equivalent
          -> subtopic_equivalent
            -> content_block
```

The canonical level is optional. A document can validly contain a
chapter-equivalent directly followed by content blocks. Every mapped node must
retain its original `native_type`, `native_number` and `native_title`.

## 54.5 Three Structures Must Stay Separate

Do not merge these concepts into one table or one guessed hierarchy:

### Document structure

What the publisher physically printed:

```text
Module -> Chapter -> Unit -> Section -> Example
```

### Syllabus taxonomy

The governed academic index used for teaching, tagging and question-bank
aggregation:

```text
CA -> Intermediate -> Advanced Accounting -> M2-C5-U1 -> Topic
```

### Retrieval structure

The searchable evidence unit:

```text
Content block -> source page -> native node -> taxonomy mapping -> embedding
```

A content block can belong to one native node and map to one or more syllabus
topics. A syllabus topic can contain many content blocks across multiple
documents and editions.

## 54.6 Required JSON Layers

The knowledge base should be built in layers, not as one enormous JSON file.

### Layer 1: document manifest

One record per physical source document:

```json
{
  "document_id": "CA-INTER-ADVANCED-ACCOUNTING-M2-C5-U1-...",
  "course": "CA",
  "institute": "ICAI",
  "level": "Intermediate",
  "subject": "Advanced Accounting",
  "document_type": "Study Material",
  "native_structure": "CA_MODULE_CHAPTER_UNIT",
  "native_code": "M2-C5-U1",
  "native_title": "Valuation of Inventories",
  "file_name": "...pdf",
  "source_path": "...pdf",
  "file_hash": "sha256...",
  "page_count": 30,
  "processing_status": "registered"
}
```

### Layer 2: page-preserving Markdown

Markdown is a processed representation, never the source of truth. It must
retain document metadata, page boundaries, headings, numbering, tables,
formulas, examples, illustrations, notes, questions and warnings.

Use markers such as:

```markdown
<!-- PDF_PAGE: 43 | PRINTED_PAGE: 41 -->
```

### Layer 3: native structure JSON

This records what the parser believes the document contains:

```json
{
  "document_id": "...",
  "native_structure": {
    "top_level": "Lesson",
    "levels": ["Lesson", "Section", "Subsection"]
  },
  "nodes": [
    {
      "node_id": "...",
      "native_type": "Section",
      "native_number": "1.1",
      "native_title": "Introduction",
      "parent_node_id": "...",
      "source_type": "explicit",
      "confidence": 0.99,
      "page_start": 3,
      "page_end": 7
    }
  ]
}
```

### Layer 4: content blocks JSON

Content blocks are the unit of retrieval and evidence. They should be
semantically coherent and page-traceable.

### Layer 5: question and answer records

Questions must reference content blocks and source locations. The existing
Question Bank Engine and Telegram Exam Hub exports remain downstream products,
not the authoritative knowledge representation.

## 54.7 Content Types

Classify content blocks whenever identifiable:

```text
paragraph
definition
rule
exception
formula
example
illustration
case_study
table
list
note
warning
learning_objective
lesson_outline
regulatory_framework
summary
practice_question
answer
marking_scheme
reference
annexure
```

Examples, illustrations, questions, answer keys and summaries must not be
stored as ordinary undifferentiated paragraphs. This classification is needed
for retrieval requests such as:

- generate examples for a topic;
- generate MCQs from theory only;
- retrieve practical illustrations;
- show all test-yourself questions;
- evaluate an answer against a marking scheme.

## 54.8 Stable Identity Rules

Every physical document receives a stable `document_id`. The current builder
uses course, level, subject, native code where available, and the physical
filename stem. A native code alone is not sufficient because one CA chapter
can contain multiple physical files such as appendices, illustrations or test
sections.

Every document also receives a SHA-256 hash. The hash detects replacement,
duplicate content and edition changes.

IDs for derived records should be deterministic:

```text
document_id
native_node_id
content_block_id
question_id
answer_id
processing_run_id
```

Never use a mutable filename as the only primary key.

## 54.9 Complete Implementation Plan

This is the step-by-step plan. Each phase must produce a testable artifact
before the next phase expands the scope.

### Phase 0: freeze decisions and repository contracts

1. Keep original PDFs immutable.
2. Define raw, processed, parsed, chunk, question and output locations.
3. Define the course and level vocabulary.
4. Define document types: Study, Revision, Exam, Faculty, Question and
   Reference.
5. Define the processing state machine.
6. Define source authority and versioning rules.

Deliverable: this specification plus a configuration contract.

### Phase 1: unified document registration

1. Read all source catalogs.
2. Normalize fields without losing source-specific metadata.
3. Register every physical PDF.
4. Calculate file hash and page count.
5. Record course, institute, level, subject, native code and source path.
6. Validate both directions: catalog-to-disk and disk-to-catalog.
7. Emit `knowledge_base_documents.json`.

Status: implemented and validated for 1,084 current documents.

### Phase 2: controlled PDF-to-Markdown conversion

1. Read the manifest rather than scanning blindly.
2. Convert one document at a time.
3. Preserve page boundaries and printed page numbers when detectable.
4. Preserve tables, formulas, lists, examples and illustrations.
5. Write UTF-8 Markdown without NUL bytes.
6. Store converter version and processing run ID.
7. Never overwrite an existing representation without recording a new run.

Deliverable: one Markdown file and conversion record per registered document.

### Phase 3: deterministic native-structure parsing

1. Select parser by course, institute, level and document type.
2. Detect table of contents and body headings.
3. Detect numbering and heading boundaries.
4. Detect content labels such as Example, Illustration, Summary and Test
   Yourself.
5. Attach every paragraph to the nearest reliable parent node.
6. Preserve page start and end for every node.
7. Output explicit, inferred, generated or unknown source classification.

Deliverable: native structure JSON and parser issue JSON.

### Phase 4: CA taxonomy mapping

1. Load the governed CA syllabus/topic index.
2. Match explicit module, chapter, unit, topic and subtopic identifiers.
3. Preserve official taxonomy IDs and page references.
4. Map additional examples and illustrations to their nearest topic.
5. Flag headings that cannot be matched.
6. Never manufacture an official topic ID.

Deliverable: CA structure plus taxonomy mapping with confidence and review
issues.

### Phase 5: CS and CMA native mapping

1. Preserve CS Lesson/Section/Subsection structure.
2. Preserve CMA Module/Section/Subsection structure.
3. Create canonical chapter/topic-equivalent mappings only where useful.
4. Retain native labels and numbering alongside canonical labels.
5. Keep publisher-specific page ranges and source files.
6. Create separate parser configurations for ICSI and ICMAI.

Deliverable: CS/CMA structure JSON without forcing CA hierarchy.

### Phase 6: human review and correction memory

1. Auto-accept high-confidence explicit structure.
2. Continue processing medium-confidence structure while logging issues.
3. Send materially ambiguous cases to review.
4. Show source page, extracted text, interpretation and alternatives.
5. Store every correction by document, page and source-text hash.
6. Reuse stored corrections on future runs.

Deliverable: review queue and persistent parser-corrections records.

### Phase 7: semantic content-block generation

1. Split at reliable heading boundaries first.
2. Keep definitions with qualifications and exceptions.
3. Keep formulas with their explanations.
4. Keep question stems with options and answers.
5. Keep table headings with tables.
6. Keep illustrations with their facts and solution where appropriate.
7. Apply token limits only after semantic boundaries.
8. Store content type, sequence, page range and parent mappings.

Deliverable: validated content-block JSON.

### Phase 8: question-bank integration

1. Import existing PYQ, MTP, RTP and faculty-question records.
2. Link every question to source documents and content blocks.
3. Preserve original question text and answer text.
4. Store course, level, subject, chapter/topic and edition.
5. Store question type, marks, difficulty and source provenance.
6. Keep generated MCQs separate from official/extracted MCQs.
7. Validate answer keys and distractors before publication.
8. Export tenant/course-specific bot JSON only after validation.

The current `mcq_questions_extracted.json` is a bot-ready CA Intermediate
Advanced Accounting export. It is not the master question database. The larger
`mcq_questions.json` is closer to a future database record model because it
contains faculty ownership, live status, replacement and source fields.

### Phase 9: retrieval index

1. Store relational metadata first.
2. Add PostgreSQL full-text or keyword search.
3. Generate embeddings from validated content blocks.
4. Store model name and dimension for every embedding run.
5. Apply metadata filters before vector search.
6. Combine keyword, metadata and vector ranking.
7. Return source pages and content-block IDs with every result.

### Phase 10: RAG answer service

1. Classify the user request.
2. Identify likely course, level, subject and edition.
3. Retrieve a small evidence set.
4. Verify source compatibility.
5. Ask the model to answer only from supplied evidence.
6. Require citations and page references where available.
7. Return uncertainty when evidence is insufficient.
8. Log query, retrieved blocks, model and response metadata.

### Phase 11: MCQ generation service

1. Accept filters for course, level, subject, chapter, topic and content type.
2. Retrieve only relevant validated blocks.
3. Generate the requested question type and difficulty.
4. Validate answer, options, ambiguity and source support.
5. Store source block IDs and source pages.
6. Send uncertain questions to human review.
7. Publish only approved questions.

### Phase 12: descriptive answer checker

1. Identify the question and edition.
2. Extract or OCR the student's answer.
3. Retrieve model answer, marking scheme and authoritative source blocks.
4. Evaluate content, method, format and marks separately.
5. Distinguish source-backed assessment from AI inference.
6. Return marks, feedback, omissions and citations.
7. Store evidence used for the evaluation.

### Phase 13: applications and MCP

Expose the same knowledge services to:

- Study Hub;
- Revision Hub;
- Exam Hub;
- MyFiles Hub where relevant;
- faculty dashboards;
- AI tutor;
- MCP tools.

MCP is an interface layer. It must not become a second database or bypass
source permissions.

## 54.10 Processing State Machine

Every document and derived artifact must expose a state:

```text
REGISTERED
  -> CONVERTED
  -> PARSED
  -> STRUCTURE_VALIDATED
  -> TAXONOMY_MAPPED
  -> CHUNKED
  -> EMBEDDED
  -> INDEXED
  -> QA_VALIDATED
  -> PUBLISHED
```

Failure or review states include:

```text
PROCESSING_ERROR
OCR_REVIEW
STRUCTURE_REVIEW
TAXONOMY_REVIEW
SOURCE_REVIEW
CONTENT_REVIEW
```

No unpublished or review-blocked material should be used for authoritative
student answers without an explicit policy decision.

## 54.11 Question Bank Engine Contract

The Question Bank Engine must consume structured evidence, not reread random
PDFs for every chapter.

The intended flow is:

```text
Registered source documents
  -> parsed native structure
    -> canonical topic mapping
      -> content blocks
        -> question source links
          -> generated chapter/question-bank outputs
```

Question records should carry at least:

```text
question_id
course
level
subject
native_node_id
canonical_topic_ids
document_id
source_pages
question_type
question_html_or_text
answer_html_or_text
marks
difficulty
source_kind
provenance
validation_status
edition
```

The existing per-chapter Question Bank Book remains a derived presentation
layer. It must be possible to regenerate it from structured question records
and source links.

## 54.12 White-Label and Faculty Content Rules

The same knowledge foundation must support:

```text
Global platform content
Faculty-owned content
Faculty-specific questions
Student-private files
```

Every document, question, content block and embedding must eventually support
ownership and visibility metadata:

```text
tenant_id
owner_type
owner_id
visibility
licence_status
publication_status
```

The retrieval layer must filter by tenant before returning evidence. A faculty
bot must never retrieve another faculty's private notes or questions.

Official institute material and exam material also require a rights and
licensing decision before commercial white-label distribution.

## 54.13 Source Integrity and AI Rules

The AI is an interpreter and generator, not the source author.

It must:

- preserve source wording when extraction is the task;
- never silently correct a textbook or legal provision;
- flag apparent source errors;
- distinguish source fact, inference and generated explanation;
- never invent a page number or citation;
- refuse to claim support when retrieved evidence is insufficient;
- keep old editions available for historical questions;
- record the model, prompt version and evidence used.

## 54.14 Update Protocol For This Specification

This Markdown file is the living contract for the knowledge-base project.
Whenever any of the following changes, update this file in the same work
session:

- source folder or catalog layout;
- JSON schema or ID rules;
- CA topic taxonomy;
- CS or CMA native structure rules;
- parser behavior;
- processing status definitions;
- chunking or embedding strategy;
- question-bank schema or provenance;
- RAG retrieval behavior;
- white-label ownership or permissions;
- a major bug, correction or validation lesson;
- a phase being completed or re-scoped.

Each update must record:

```text
date
decision or change
files/scripts affected
reason
validation performed
remaining risk or next action
```

Add dated entries below rather than silently rewriting history.

## 54.15 Current Status and Next Actions

Completed:

- course and level corpus inventory;
- representative CA, CS and CMA structure review;
- unified physical-document catalog design;
- `build_knowledge_base_catalog.py` implementation;
- `knowledge_base_documents.json` generation;
- SHA-256 and page-count registration;
- disk/catalog cross-validation.

Next, in order:

1. Define the knowledge-base directory layout and configuration files.
2. Build a manifest-driven PDF-to-Markdown conversion runner.
3. Add page markers and conversion metadata.
4. Create one native parser adapter for CA, CS and CMA.
5. Run a nine-document vertical pilot: one Foundation, Intermediate and Final
   or Professional sample for each course.
6. Review the resulting structure JSON manually.
7. Add taxonomy mapping and content-block generation.
8. Connect the first content blocks to the Question Bank Engine.
9. Benchmark hybrid retrieval before scaling to all documents.

Do not embed all 1,084 documents before the pilot proves that structure,
citations, content types and question links are correct.

## 54.16 Decision Log

### 2026-08-09/10: Unified catalog

Decision: use one generated JSON manifest for all courses and document types,
while retaining CA and CS/CMA source catalogs as authoritative source
metadata.

Reason: one machine-readable contract is needed for downstream processing,
but publisher-specific catalog facts must not be destroyed by flattening.

Validation: 1,084 physical documents registered and cross-checked against
disk; one known merged ICSI lesson excluded because it has no standalone PDF.

### 2026-08-10: Native structures remain distinct

Decision: CA, CS and CMA receive separate parsing adapters and configurations.

Reason: CA uses module/chapter/unit/topic patterns; CS commonly uses
lesson/section patterns; CMA commonly uses module/section patterns with
different nesting.

### 2026-08-10: Syllabus taxonomy is separate from document structure

Decision: CA's topic index is used for governed taxonomy mapping, not as a
replacement for the complete PDF structure.

Reason: examples, illustrations, summaries, learning outcomes and practice
material exist in the PDFs but not necessarily in the syllabus index.

### 2026-08-10: Question records are derived, not the source of knowledge

Decision: question-bank records and Telegram exports link back to content
blocks and source pages.

Reason: the same evidence must support chapter books, MCQs, answer checking,
RAG answers and future faculty-specific outputs.

### 2026-08-10: Faculty descriptive PDF ingestion

Built a source-aware extractor for `descp-companies-act.pdf` under CS Arun
Chouhan's CMA Intermediate Law faculty content. It produced 47 descriptive
question records using the same core shape as `book_questions_extracted.json`,
with additional faculty provenance, source hash, PDF page range, publication
status and validation fields. The generated source copy lives beside the PDF;
the bot input is published at the path already configured for the Arun tenant:
`telegram/assets/exam_bot/faculty/csarunchouhan/book_questions_extracted.json`.

The PDF has an irregular scanned/column layout: 47 prompt headings were
detected but only 46 literal `Ans.` markers were found. The extractor retains
all 47 prompt-to-following-passage segments and reports this discrepancy for
human review rather than silently discarding one question. These records are
marked `FACULTY_PRACTICE`, `faculty_created`, and `draft`/`extracted_needs_review`
until the faculty or reviewer approves them.

### 2026-08-10: Faculty Intermediate Law MCQ ingestion

Built `convert_inter_law_mcqs.py` under CS Arun Chouhan's CMA Intermediate Law
faculty folder. It deterministically converts the 14 actual MCQ DOCX papers,
excluding the three non-MCQ reference sheets, into the same plain-list record
shape used by the Exam Hub MCQ input. It cross-checks inline marked answers
against each document's answer-key table and writes a separate validation
report.

Result: 650/650 MCQs extracted, 650 unique IDs, four valid options per record,
zero answer-key mismatches, zero excluded questions, and no missing explicit
topic labels. The catalog mapping is exact at the native module level:
`M7`, `M8`, `M9`, `M10`, `M11` and `M12`, with the exact module titles from
`knowledge_base_documents.json`. The DOCX bracket labels are retained as
`topic_text`; they are source-provided topic descriptions, not invented CMA
topic IDs, because the current master catalog does not yet define a separate
CMA topic-ID taxonomy.

The generated source bank is:
`telegram/assets/faculty/csarunchouhan-cma-inter-law/cma_inter_law_faculty_mcqs.json`

The bot input is:
`telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json`

The validation report is:
`telegram/assets/faculty/csarunchouhan-cma-inter-law/cma_inter_law_faculty_mcqs.validation.json`

------------------------------------------------------------------------

# 55. Final Handoff Summary

Any new bot or AI joining this project should understand the following:

1. The original PDFs are immutable evidence.
2. The first machine layer is the generated unified document manifest.
3. CA, CS and CMA do not share one native academic structure.
4. A common canonical model is required for search, but native labels must be
   retained.
5. CA's syllabus topic index is a governed taxonomy, not the entire document.
6. Examples, illustrations, questions, answers, summaries and tables are
   meaningful typed content blocks.
7. Page and edition traceability are mandatory.
8. Deterministic code handles identity, metadata, storage, filtering and
   validation; AI handles ambiguity, semantic interpretation and generation.
9. MCQs and descriptive questions are derived from validated evidence and must
   retain provenance.
10. RAG uses metadata filtering plus keyword and vector retrieval.
11. Human review is part of the design, not an exception.
12. Faculty white-labeling requires tenant ownership and permission filters.
13. This file must be updated whenever the implementation or understanding
   changes.
14. Parser adapters are config profiles resolved by (course, level,
   document_type) at runtime, not hardcoded per course — see section 56.
15. Content applicability for law/tax/audit/ethics is filtered by the
   student's declared exam attempt, not by publish date — see section 57.

The final mental model is:

```text
Immutable PDFs
  -> unified registration JSON
    -> page-preserving Markdown
      -> native course-specific structure
        -> canonical taxonomy mappings
          -> typed content blocks
            -> question bank and answer evidence
              -> hybrid retrieval
                -> RAG, MCQ engine, answer checker, MCP and bots
```

------------------------------------------------------------------------

# 56. Parser Configuration Model — One Engine, N Config Profiles

**Status:** authoritative implementation addendum

**Added:** 2026-08-16 (from architecture discussion with Pranav)

## 56.1 Decision

Do not hardcode one parser per course (3) or one parser per course-level (9)
in advance. Build ONE parsing engine plus N configuration profiles, resolved
at runtime by `(course, level, document_type)`.

```text
one parser engine
    -> resolves at runtime by (course, level, document_type)
    ->
config profile: regex patterns, heading keywords, confidence thresholds
```

Reason: the correct number of profiles is an empirical question, not an
upfront design decision. A course/level boundary only deserves its own
profile if the 9-document pilot (section 54.9, Phase 2/3) actually shows a
different heading/numbering convention there. Splitting before that evidence
exists risks the same ID/scheme-proliferation mistake already rejected once
for the Question Bank Book (see the external-AI-review rejection recorded in
`CLAUDE.md` section 6, 2026-07-24 entry — a parallel topic-ID namespace was
rejected for the same reason).

A new course, level or document type becomes a new config file, never new
parser code. If the pilot shows CA Foundation needs different patterns than
CA Final, that is a second CA profile (`CA_FOUNDATION_STUDY_MATERIAL`), not a
rewrite.

## 56.2 Config Profile Shape

```yaml
profile_id: CA_INTERMEDIATE_STUDY_MATERIAL

identity:
  course: CA
  institute: ICAI
  level: Intermediate
  document_type: Study Material

native_levels: [Module, Chapter, Unit, Topic, Subtopic]

structure_patterns:
  chapter:
    - "^CHAPTER\\s+\\d+"
    - "^Module\\s+\\d+"
  unit:
    - "^UNIT\\s+[IVX]+"
  topic:
    - "^\\d+\\.\\d+\\s"
  subtopic:
    - "^\\d+\\.\\d+\\.\\d+\\s"

strip_patterns:
  - "^ICAI\\s*-\\s*Study Material$"
  - "^\\d+$"

content_labels:
  example: ["Example", "Illustration"]
  summary: ["Summary", "Let Us Recapitulate"]
  practice_question: ["Test Your Knowledge", "Exercise"]
  note: ["Note:", "Important:"]

toc_authority: supporting_evidence

confidence_thresholds:
  explicit: 0.95
  inferred: 0.80
  human_review_below: 0.70

canonical_mapping:
  Module: chapter_group
  Chapter: chapter
  Unit: chapter
  Topic: topic
  Subtopic: subtopic
```

`identity` decides which profile the engine loads for a given document (via
the document manifest's course/level/document_type fields). Everything else
is data the shared engine consumes, never document-specific code.

## 56.3 Next Action

During pilot review (Phase B, step 6 of the crisp step list — see the
project chat log or re-derive from section 54.9), explicitly record whether
each course's Foundation/Intermediate/Final documents needed different
`structure_patterns`/`content_labels`, or shared one profile. That answer,
not a guess, sets the real profile count going forward.

------------------------------------------------------------------------

# 57. Edition, Amendment and Attempt-Applicability Model

**Status:** authoritative implementation addendum

**Added:** 2026-08-16 (from architecture discussion with Pranav)

## 57.1 Core Principle

For law, tax, audit and ethics subjects, "attempt-applicable" is a different
and more authoritative axis than "current as of today." ICAI/ICSI/ICMAI apply
a cutoff rule: amendments notified after a fixed date before an exam are not
examinable for the immediately following attempt. A change can be legally in
force and still not be the syllabus for the next exam. The platform must
filter content by the **declared applicable attempt**, sourced from the
institute's own applicability circular, never inferred from a notification or
publish date.

This is especially critical where an Act is wholly replaced, not merely
amended — e.g. a new Income Tax Act replacing the old one. Section numbers
and provisions can change so completely that old MTP/RTP/PYQ material becomes
actively misleading if served without correction, not just outdated.

## 57.2 Metadata Additions

Document edition and governing law/standard version are separate axes:

```text
document_edition: "2026"
governing_law_version: "Income-tax Act, 2026"
```

Law/standard versions carry an applicability window:

```text
effective_from: 2026-04-01
effective_to: null
supersedes: "Income-tax Act, 1961"
```

Amendments (Finance Act/Bill, revised Standards on Auditing, revised Code of
Ethics) are tracked as their own entity. Applicability is sourced from the
real institute circular, never computed from the notification date:

```text
amendment_id: "Finance Act 2026"
amends: "Income-tax Act, 2026"
notified_date: 2026-02-01
icai_applicability_circular: "<link/reference to the real notification>"
applicable_from_attempt: "Nov 2026"
```

Every document, provision and question carries:

```text
attempt_applicability: ["May 2026", "Nov 2026"]
exam_relevance: "current" | "law_updated_annotated" | "excluded_obsolete"
```

## 57.3 Reuse the Existing Student Attempt Field

`student_profiles.exam_attempt` (Year -> Month picker, already built as part
of the profile system — see `telegram/PROFILE-SYSTEM.md`) is the default
filter for RAG retrieval, MCQ pool selection, descriptive-question pool
selection, and MTP/RTP/PYQ pool selection. Do not build a second
attempt-collection mechanism; read the stored value, re-confirm once per
session if needed, and reuse it everywhere content is served.

## 57.4 Three Relevance Tiers (Not a Blanket Exclude)

```text
current               -> provision unchanged in substance, serve as-is
law_updated_annotated -> pattern still valuable, numbering/provision changed,
                          must be served WITH a correction note attached
excluded_obsolete     -> substantively wrong if served even annotated;
                          kept in the archive, never served in practice pools
```

Decide the tier per subject, not platform-wide. Tax/Company Law after a
wholesale Act replacement will lean toward aggressive `excluded_obsolete`;
subjects with mostly cosmetic changes (e.g. some Accounting Standards) can
stay `law_updated_annotated` longer. This decision needs subject-specific
input from Pranav or the relevant faculty — it is not a default to apply
uniformly, and it is not yet made.

## 57.5 Old/New Referencing at Scale — Reuse the Existing Provenance Pattern

Extend the Question Bank Book's existing Examiner's-Comment-vs-Author's-Note
labeled-box pattern with a third note type, rather than inventing a new
mechanism:

```json
{
  "note_type": "law_update",
  "old_ref": "Income-tax Act 1961, Sec 80C",
  "new_ref": "Income-tax Act 2026, Sec 142",
  "delta_description": "Provision retained in substance; renumbered; deduction cap unchanged.",
  "source": "Synthesized per law-update-writing-skill — not ICAI-sourced | ICAI applicability circular, verbatim",
  "review_status": "approved | pending"
}
```

Rendered the same visibly-labeled way the existing provenance boxes are.
Never blended silently into the original question/answer text; the original
verbatim text is never edited.

Pipeline, same shape as MCQ validation (section 33):

```text
detect affected content
  (keyword / section-number scan, scoped to subjects known to have had
   a wholesale change)
    -> AI drafts old-to-new mapping note
      -> human/faculty review and approval
        -> publish (attached to the question record)
```

Built once per subject that had a wholesale change, driven by a detection
scan across that subject's existing questions — not hand-written per
question, and not run against subjects that never had this kind of change.

## 57.6 Open Decisions / Next Actions

- Which subjects get aggressive `excluded_obsolete` treatment vs staying
  `law_updated_annotated` — needs a subject-by-subject call, not a platform
  default. Ask before building.
- Real ICAI/ICSI/ICMAI applicability circulars need to be sourced per
  amendment when this is actually built — `applicable_from_attempt` must
  never be guessed from a notification date.
- The Finance Act/Bill and amendment-tracking table itself is not yet built.
  This section records the design; implementation is future work, after the
  9-document pilot proves the base parsing/taxonomy pipeline.
