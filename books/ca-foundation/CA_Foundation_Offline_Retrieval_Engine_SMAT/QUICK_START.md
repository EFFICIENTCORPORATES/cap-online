# Quick Start — CA Foundation Offline Retrieval Engine Corrected V2

This tool retrieves already-classified CA Foundation content **fully offline**. It uses Python's standard library only; it does not call ChatGPT, Gemini, Claude, an API, embeddings, or the internet.

## Windows

Double-click `run_gui.bat` for the graphical interface, or `run_tool.bat` for the terminal interface.

### Verified on this computer — 11 September 2026

1. Open this folder in File Explorer.
2. Double-click **`run_gui.bat`**.
3. Wait for the status box to say that 37 Markdown files and 2,757 classified blocks are loaded.
4. Type a request, or choose a preset such as `examples`, `mcq_with_answers`, or `illustrations`.
5. Confirm the output file location, then click **Generate Markdown**.
6. The result is saved as a Markdown file; the default is `output.md` in this folder.

If the window does not open, run `run_tests.bat`. This computer has Python 3.11 installed and the engine needs no third-party package, internet connection, API key, or AI service.

To close the GUI, use the normal **X** button. To exit the terminal interface, type `exit`.

## Command line

```bat
python ca_retriever.py --query "Give me all Examples" -o outputs\all_examples.md
python ca_retriever.py --query "Give me all MCQs from Chapter 3 with answers" -o outputs\chapter3_mcqs.md
python ca_retriever.py --query "Give me only Illustration questions from Chapter 2 without solutions" -o outputs\chapter2_illustration_questions.md
python ca_retriever.py --query "Give me Illustration questions with solutions from Chapter 10 Unit 3" -o outputs\c10u3_illustrations.md
python ca_retriever.py --query "Give me all practical questions from Paper 1 Module 2" -o outputs\module2_practical.md
```

## Corrected Example behaviour

`Give me all Examples` returns **53 source Examples**, one item per ICAI source Example. These are read from the source-verified Example registry, not from the older broad Example block boundaries.

For the subset where the PDF provides a safely separable Question/Solution boundary, `Give me only Example questions` can return the question-only derivative. The full `Examples` preset remains the authoritative exhaustive view.

## Validation

```bat
python ca_retriever.py --validate-data
python -m unittest discover -s tests -v
```

The bundled validation requires 53 Examples, 235 Illustration Questions, 235 Illustration Solutions, 269 MCQs, 79 Practical Questions, and 307 True/False statements.
