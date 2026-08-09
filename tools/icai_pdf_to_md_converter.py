#!/usr/bin/env python3
"""
icai_pdf_to_md_converter.py
============================

Recursively scans a folder for .pdf files (e.g. the output of
icai_pdf_downloader.py) and converts each one to Markdown using Microsoft's
MarkItDown engine, running entirely offline -- no Document Intelligence, no
Content Understanding, no cloud/LLM calls of any kind.

Per Pranav's instruction (2026-08-04): the .md file is written to the EXACT
SAME folder as its source PDF, with the EXACT SAME base filename -- only the
extension changes. Example:

    .../Module 1/M1_C4_U1_ Accounting Standard 1 Disclosure of Accounting Policies.pdf
 -> .../Module 1/M1_C4_U1_ Accounting Standard 1 Disclosure of Accounting Policies.md

Output is normalized to be Git-safe, matching the design goals already written
into MDUnix's own README.md:
    - UTF-8, no BOM
    - LF-only line endings
    - no stray NUL bytes

Give it one root folder. It walks every subfolder, any number of levels deep,
and converts every .pdf it finds -- there is no separate "recursive" toggle,
this is unconditional.

Usage:
    Run this file directly for a Tkinter GUI:
        python icai_pdf_to_md_converter.py

    Or use it headlessly from another script:
        from icai_pdf_to_md_converter import run_batch
        run_batch("C:/.../downloaded_pdfs")

Dependencies:
    pip install "markitdown[pdf]"
Tkinter ships with standard Windows/Mac Python installs; on some Linux
distros you may need `sudo apt install python3-tk`.

Note on MDUNIX/_markitdown.py and MDUNIX/__main__.py: those two files are an
incomplete, partial copy of the upstream MarkItDown source (they import from
sibling modules -- .__about__, .converters -- that aren't present in that
folder), so they can't run standalone. MDUnix's own README says its intended
design is to use the real `markitdown` package "as a dependency" rather than
reimplement it, so this script does exactly that: `pip install markitdown`
and `from markitdown import MarkItDown`.
"""

import os
import re
import sys
import queue
import threading
import traceback

# --------------------------------------------------------------------------
# Conversion
# --------------------------------------------------------------------------

def _get_markitdown():
    """Import MarkItDown lazily so the GUI can still start up (and show a
    clear error) even if the package isn't installed yet."""
    try:
        from markitdown import MarkItDown
    except ImportError as e:
        raise ImportError(
            "The 'markitdown' package isn't installed for this Python.\n"
            f"This script is running under: {sys.executable}\n"
            "Install it (once, offline afterwards) with:\n"
            f'    "{sys.executable}" -m pip install markitdown[pdf]'
        ) from e

    # markitdown[pdf]'s actual PDF engine is pdfminer.six. If the base
    # 'markitdown' package was installed WITHOUT the [pdf] extra, import
    # above succeeds but every .pdf conversion fails with a
    # MissingDependencyException. Check for it here so we fail once, with a
    # clear message, instead of once per file.
    try:
        import pdfminer.high_level  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "The 'markitdown' package is installed, but its PDF dependency "
            "(pdfminer.six) is missing -- this happens when it was installed "
            "as plain 'markitdown' instead of 'markitdown[pdf]'.\n"
            f"This script is running under: {sys.executable}\n"
            "Fix it by running:\n"
            f'    "{sys.executable}" -m pip install --upgrade markitdown[pdf]\n'
            "(Using \"<python> -m pip\" instead of a bare 'pip' avoids installing "
            "to a different Python than the one running this script -- the "
            "most common cause of this error.)"
        ) from e

    # No docintel_endpoint / cu_endpoint / plugins passed in => MarkItDown
    # only uses its local, offline converters (pdfminer.six for PDF text).
    return MarkItDown(enable_plugins=False)


def normalize_markdown_text(text: str) -> str:
    """Git-safe normalization: UTF-8/no-BOM (handled by write mode), LF-only
    line endings, no stray NUL bytes."""
    if text is None:
        text = ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def convert_one_pdf(md_engine, pdf_path: str) -> str:
    """Convert a single PDF to normalized markdown text (offline)."""
    result = md_engine.convert(pdf_path)
    return normalize_markdown_text(result.markdown)


def find_pdfs(root: str):
    """Walk `root` and every subfolder beneath it, any number of levels deep,
    yielding the path of every .pdf file found. Unconditional -- always
    recursive, no depth limit (os.walk has none)."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                yield os.path.join(dirpath, fn)


def run_batch(
    root: str,
    skip_existing: bool = True,
    log=print,
    should_stop=None,
):
    """
    Converts every .pdf found anywhere under `root` (all nested subfolders,
    any depth) to a .md file in the SAME folder with the SAME base name.
    Returns (ok_count, fail_count, skipped_count).
    """
    ok = fail = skipped = 0

    try:
        md_engine = _get_markitdown()
    except ImportError as e:
        log(f"[FATAL] {e}")
        return ok, fail, skipped

    pdf_paths = sorted(find_pdfs(root))
    if not pdf_paths:
        log(f"No .pdf files found under: {root} (including subfolders)")
        return ok, fail, skipped

    log(f"Found {len(pdf_paths)} PDF file(s) under: {root}")

    for pdf_path in pdf_paths:
        if should_stop and should_stop():
            log("Stopped by user.")
            break

        md_path = os.path.splitext(pdf_path)[0] + ".md"
        rel = os.path.relpath(pdf_path, root)

        if os.path.exists(md_path) and skip_existing:
            log(f"[SKIP] {rel} (.md already exists)")
            skipped += 1
            continue

        log(f"[CONVERT] {rel}")
        try:
            markdown_text = convert_one_pdf(md_engine, pdf_path)
            # Write UTF-8 without BOM, LF-only (newline="" so \n isn't translated on Windows)
            with open(md_path, "w", encoding="utf-8", newline="") as f:
                f.write(markdown_text)
            ok += 1
        except Exception as e:
            log(f"  [ERROR] {rel} -> {e}")
            fail += 1

    log(f"\nDone. Converted: {ok}  Skipped: {skipped}  Failed: {fail}")
    return ok, fail, skipped


# --------------------------------------------------------------------------
# Tkinter GUI
# --------------------------------------------------------------------------

def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox

    root_win = tk.Tk()
    root_win.title("ICAI PDF -> Markdown Converter (offline, MarkItDown)")
    root_win.geometry("820x600")

    msg_queue = queue.Queue()
    stop_flag = {"stop": False}
    worker_state = {"running": False}

    frm = ttk.Frame(root_win, padding=10)
    frm.pack(fill="both", expand=True)

    ttk.Label(
        frm,
        text="Give the root folder path (e.g. the 'downloaded_pdfs' folder from\n"
        "the downloader script). Every subfolder underneath it, any number of\n"
        "levels deep, is scanned. Each PDF found gets an .md file written right\n"
        "next to it -- same name, same folder. Runs fully offline.",
        justify="left",
    ).pack(anchor="w")

    folder_frame = ttk.Frame(frm)
    folder_frame.pack(fill="x", pady=(8, 10))
    ttk.Label(folder_frame, text="Root folder path:").pack(side="left")
    folder_var = tk.StringVar(value="")
    folder_entry = ttk.Entry(folder_frame, textvariable=folder_var)
    folder_entry.pack(side="left", fill="x", expand=True, padx=6)

    def browse_folder():
        chosen = filedialog.askdirectory(initialdir=folder_var.get() or os.getcwd())
        if chosen:
            folder_var.set(chosen)

    ttk.Button(folder_frame, text="Browse...", command=browse_folder).pack(side="left")

    options_frame = ttk.Frame(frm)
    options_frame.pack(fill="x", pady=(0, 10))

    skip_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        options_frame,
        text="Skip files that already have a .md (uncheck to overwrite)",
        variable=skip_var,
    ).pack(side="left")

    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill="x", pady=4)

    log_box = tk.Text(frm, height=22, wrap="word", state="disabled", bg="#111", fg="#0f0")
    log_box.pack(fill="both", expand=True, pady=(6, 0))

    def append_log(text):
        log_box.configure(state="normal")
        log_box.insert("end", text + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def log_from_thread(text):
        msg_queue.put(text)

    def worker():
        try:
            run_batch(
                folder_var.get().strip(),
                skip_existing=skip_var.get(),
                log=log_from_thread,
                should_stop=lambda: stop_flag["stop"],
            )
        except Exception:
            log_from_thread("[FATAL ERROR]\n" + traceback.format_exc())
        finally:
            worker_state["running"] = False
            msg_queue.put("__DONE__")

    def start():
        if worker_state["running"]:
            return
        folder = folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("No folder", "Choose a valid folder to scan first.")
            return
        stop_flag["stop"] = False
        worker_state["running"] = True
        start_btn.configure(state="disabled")
        stop_btn.configure(state="normal")
        append_log("Starting (offline conversion, no network calls)...")
        threading.Thread(target=worker, daemon=True).start()

    def stop():
        stop_flag["stop"] = True
        append_log("Stopping after current file...")

    start_btn = ttk.Button(btn_frame, text="Start Conversion", command=start)
    start_btn.pack(side="left")
    stop_btn = ttk.Button(btn_frame, text="Stop", command=stop, state="disabled")
    stop_btn.pack(side="left", padx=6)

    def check_done():
        try:
            while True:
                item = msg_queue.get_nowait()
                if item == "__DONE__":
                    start_btn.configure(state="normal")
                    stop_btn.configure(state="disabled")
                else:
                    append_log(item)
        except queue.Empty:
            pass
        root_win.after(150, check_done)

    root_win.after(150, check_done)

    root_win.mainloop()


if __name__ == "__main__":
    launch_gui()
