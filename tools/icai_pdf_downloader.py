#!/usr/bin/env python3
"""
icai_pdf_downloader.py
=======================

Scans one or more ICAI study-material pages (like https://icai.org/post/19142),
walks the MODULE -> Chapter -> Unit <ul>/<li> tree on the page, downloads every
linked PDF, and renames it to:

    M{module}_C{chapter}_U{unit}_ {Title}.pdf

Files are saved to:

    <output root>/<subject folder>/Module {module}/M{module}_C{chapter}_U{unit}_ {Title}.pdf

Naming rules (confirmed with Pranav, 2026-08-04):
  - Chapters that have no explicit "Unit" (a chapter that links straight to one
    PDF, e.g. "Chapter 1: Introduction to Accounting Standards") are numbered U0.
  - Loose items that sit directly under a MODULE and are not a numbered
    "Chapter" at all (e.g. a module's "Initial Pages" link) get chapter number 0
    (C0) and an incrementing unit number per module (U1, U2, ...), since they
    don't belong to any specific chapter. Rename these by hand afterwards if you
    want them folded into a neighbouring chapter's number instead.

Usage:
    Run this file directly for a Tkinter GUI:
        python icai_pdf_downloader.py

    Or use it headlessly from another script:
        from icai_pdf_downloader import run_batch
        run_batch(["https://icai.org/post/19142"], output_root="C:/.../downloaded_pdfs")

Dependencies: requests, beautifulsoup4  (pip install requests beautifulsoup4)
Tkinter ships with standard Windows/Mac Python installs; on some Linux distros
you may need to `sudo apt install python3-tk`.
"""

import os
import re
import sys
import queue
import threading
import traceback
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

MODULE_RE = re.compile(r"module\s*[-:]?\s*(\d+)", re.I)
CHAPTER_RE = re.compile(r"chapter\s*[-:]?\s*(\d+)\s*[:\-]?\s*(.*)", re.I)
UNIT_RE = re.compile(r"unit\s*[-:]?\s*(\d+)\s*[:\-]?\s*(.*)", re.I)

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _header_text(li: Tag) -> str:
    """Text of an <li> that belongs to it directly (its own strings plus any
    inline tags like <a>/<br>), stopping before any nested <ul> child. This is
    what lets us tell 'MODULE 1' / 'Chapter 4: ...' apart from the nested list
    of chapters/units that follows it."""
    parts = []
    for child in li.contents:
        if isinstance(child, Tag) and child.name == "ul":
            break
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            parts.append(child.get_text())
    text = " ".join(p.strip() for p in parts if p.strip())
    return re.sub(r"\s+", " ", text).strip()


def _direct_ul(li: Tag):
    """The <ul> that is a direct child of this <li>, if any."""
    for child in li.contents:
        if isinstance(child, Tag) and child.name == "ul":
            return child
    return None


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "subject"


def sanitize_title(text: str) -> str:
    text = INVALID_FILENAME_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.rstrip(" .")  # Windows disallows trailing space/dot
    return text or "Untitled"


def parse_page(html: str, base_url: str):
    """Returns a list of dicts: {module, chapter, unit, title, url, source_text}."""
    soup = BeautifulSoup(html, "html.parser")

    # Find the top-level <ul> whose first <li> header looks like "MODULE n".
    module_ul = None
    for ul in soup.find_all("ul"):
        top_lis = [c for c in ul.contents if isinstance(c, Tag) and c.name == "li"]
        if top_lis and MODULE_RE.search(_header_text(top_lis[0])):
            module_ul = ul
            break

    entries = []

    if module_ul is not None:
        for mod_li in module_ul.find_all("li", recursive=False):
            header = _header_text(mod_li)
            m = MODULE_RE.search(header)
            module_num = int(m.group(1)) if m else 1
            nested_ul = _direct_ul(mod_li)
            if nested_ul is not None:
                entries.extend(_parse_chapter_list(nested_ul, module_num, base_url))
    else:
        # No "MODULE n" wrapper found on this page -- fall back to treating the
        # first <ul> that contains a Chapter/Unit-looking link as one module.
        candidate_ul = None
        for ul in soup.find_all("ul"):
            if ul.find("a", string=CHAPTER_RE) or ul.find("a", string=UNIT_RE):
                candidate_ul = ul
                break
        if candidate_ul is not None:
            entries.extend(_parse_chapter_list(candidate_ul, 1, base_url))

    return entries


def _parse_chapter_list(ul: Tag, module_num: int, base_url: str):
    entries = []
    loose_counter = 0

    for li in ul.find_all("li", recursive=False):
        nested_ul = _direct_ul(li)
        header = _header_text(li)

        if nested_ul is not None:
            # A chapter that expands into units.
            cm = CHAPTER_RE.search(header)
            chapter_num = int(cm.group(1)) if cm else 0
            for unit_li in nested_ul.find_all("li", recursive=False):
                a = unit_li.find("a")
                if not a or not a.get("href"):
                    continue
                unit_header = a.get_text().strip()
                um = UNIT_RE.search(unit_header)
                unit_num = int(um.group(1)) if um else 0
                unit_title = um.group(2).strip() if um else unit_header
                entries.append(
                    {
                        "module": module_num,
                        "chapter": chapter_num,
                        "unit": unit_num,
                        "title": sanitize_title(unit_title),
                        "url": urljoin(base_url, a["href"]),
                        "source_text": unit_header,
                    }
                )
        else:
            a = li.find("a")
            if not a or not a.get("href"):
                continue
            leaf_header = a.get_text().strip()
            cm = CHAPTER_RE.search(leaf_header)
            if cm:
                chapter_num = int(cm.group(1))
                unit_num = 0
                title = cm.group(2).strip() or leaf_header
            else:
                # A loose item directly under the module (e.g. "Initial Pages")
                # that isn't tied to a numbered chapter.
                chapter_num = 0
                loose_counter += 1
                unit_num = loose_counter
                title = leaf_header
            entries.append(
                {
                    "module": module_num,
                    "chapter": chapter_num,
                    "unit": unit_num,
                    "title": sanitize_title(title),
                    "url": urljoin(base_url, a["href"]),
                    "source_text": leaf_header,
                }
            )

    return entries


def build_filename(entry: dict, ext: str) -> str:
    return f"M{entry['module']}_C{entry['chapter']}_U{entry['unit']}_ {entry['title']}{ext}"


def guess_subject_name(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.get_text().strip():
        raw = soup.title.get_text().strip()
        raw = re.split(r"\s*[-|]\s*ICAI", raw, flags=re.I)[0]
        return slugify(raw)
    path = urlparse(url).path.strip("/").replace("/", "-")
    return slugify(path or "subject")


# --------------------------------------------------------------------------
# Downloading
# --------------------------------------------------------------------------

def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) icai-pdf-downloader/1.0"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def download_file(url: str, dest_path: str, timeout: int = 60, chunk_size: int = 65536, log=print):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) icai-pdf-downloader/1.0"}
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    tmp_path = dest_path + ".part"
    with requests.get(url, headers=headers, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    os.replace(tmp_path, dest_path)


def parse_url_line(line: str):
    """A line in the UI's URL box can be either just a URL, or
    'URL, custom-subject-folder-name'."""
    line = line.strip()
    if not line:
        return None, None
    if "," in line:
        url, name = line.split(",", 1)
        return url.strip(), slugify(name.strip()) if name.strip() else None
    return line, None


def run_batch(
    url_lines,
    output_root: str,
    skip_existing: bool = True,
    log=print,
    should_stop=None,
):
    """
    url_lines: iterable of raw lines from the UI (URL, or 'URL, subject-name')
    output_root: base folder that will contain one subfolder per subject
    Returns (ok_count, fail_count, skipped_count)
    """
    ok = fail = skipped = 0
    os.makedirs(output_root, exist_ok=True)

    for raw_line in url_lines:
        if should_stop and should_stop():
            log("Stopped by user.")
            break

        url, custom_name = parse_url_line(raw_line)
        if not url:
            continue

        log(f"\n=== Fetching page: {url} ===")
        try:
            html = fetch_html(url)
        except Exception as e:
            log(f"  [ERROR] Could not fetch page: {e}")
            fail += 1
            continue

        subject_name = custom_name or guess_subject_name(html, url)
        entries = parse_page(html, url)

        if not entries:
            log("  [WARN] No Module/Chapter/Unit PDF links found on this page.")
            continue

        log(f"  Subject folder: {subject_name}  ({len(entries)} PDF links found)")

        for entry in entries:
            if should_stop and should_stop():
                log("Stopped by user.")
                break

            ext = os.path.splitext(urlparse(entry["url"]).path)[1] or ".pdf"
            filename = build_filename(entry, ext)
            module_dir = os.path.join(output_root, subject_name, f"Module {entry['module']}")
            dest_path = os.path.join(module_dir, filename)

            if os.path.exists(dest_path) and skip_existing:
                log(f"  [SKIP] {filename} (already exists)")
                skipped += 1
                continue

            os.makedirs(module_dir, exist_ok=True)
            log(f"  [DOWNLOAD] {filename}")
            try:
                download_file(entry["url"], dest_path, log=log)
                ok += 1
            except Exception as e:
                log(f"    [ERROR] {entry['url']} -> {e}")
                fail += 1

    log(f"\nDone. Downloaded: {ok}  Skipped: {skipped}  Failed: {fail}")
    return ok, fail, skipped


# --------------------------------------------------------------------------
# Tkinter GUI
# --------------------------------------------------------------------------

def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox

    default_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_pdfs")

    root = tk.Tk()
    root.title("ICAI Study Material PDF Downloader")
    root.geometry("820x620")

    msg_queue = queue.Queue()
    stop_flag = {"stop": False}
    worker_state = {"running": False}

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill="both", expand=True)

    ttk.Label(
        frm,
        text="Paste one ICAI page URL per line.\n"
        "Optionally add a custom subject-folder name after a comma, e.g.:\n"
        "https://icai.org/post/19142, advanced-accounting\n"
        "(If you don't give a name, it's auto-derived from the page title.)",
        justify="left",
    ).pack(anchor="w")

    url_box = tk.Text(frm, height=8, wrap="word")
    url_box.pack(fill="x", pady=(4, 10))

    out_frame = ttk.Frame(frm)
    out_frame.pack(fill="x", pady=(0, 10))
    ttk.Label(out_frame, text="Output folder:").pack(side="left")
    out_var = tk.StringVar(value=default_output)
    out_entry = ttk.Entry(out_frame, textvariable=out_var)
    out_entry.pack(side="left", fill="x", expand=True, padx=6)

    def browse_output():
        chosen = filedialog.askdirectory(initialdir=out_var.get() or os.getcwd())
        if chosen:
            out_var.set(chosen)

    ttk.Button(out_frame, text="Browse...", command=browse_output).pack(side="left")

    skip_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        frm, text="Skip files that already exist (uncheck to re-download and overwrite)", variable=skip_var
    ).pack(anchor="w")

    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill="x", pady=8)

    log_box = tk.Text(frm, height=22, wrap="word", state="disabled", bg="#111", fg="#0f0")
    log_box.pack(fill="both", expand=True)

    def append_log(text):
        log_box.configure(state="normal")
        log_box.insert("end", text + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def log_from_thread(text):
        msg_queue.put(text)

    def worker():
        try:
            lines = url_box.get("1.0", "end").splitlines()
            run_batch(
                lines,
                out_var.get().strip(),
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
        if not url_box.get("1.0", "end").strip():
            messagebox.showwarning("No URLs", "Paste at least one URL first.")
            return
        if not out_var.get().strip():
            messagebox.showwarning("No output folder", "Choose an output folder first.")
            return
        stop_flag["stop"] = False
        worker_state["running"] = True
        start_btn.configure(state="disabled")
        stop_btn.configure(state="normal")
        append_log("Starting...")
        threading.Thread(target=worker, daemon=True).start()

    def stop():
        stop_flag["stop"] = True
        append_log("Stopping after current file...")

    start_btn = ttk.Button(btn_frame, text="Start Download", command=start)
    start_btn.pack(side="left")
    stop_btn = ttk.Button(btn_frame, text="Stop", command=stop, state="disabled")
    stop_btn.pack(side="left", padx=6)

    def check_done():
        # re-enable buttons once worker signals completion
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
        root.after(150, check_done)

    # Replace the simpler poll_queue with check_done (handles the __DONE__ sentinel too)
    root.after(150, check_done)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
