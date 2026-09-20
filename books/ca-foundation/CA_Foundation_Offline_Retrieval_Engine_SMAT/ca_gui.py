from __future__ import annotations
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ca_retrieval.engine import RetrievalEngine
from ca_retrieval.query import PRESETS, spec_from_preset

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "parsed_md"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CA Foundation Offline Retrieval Engine — Corrected V2")
        self.geometry("920x650")
        self.minsize(780, 560)
        self.engine = None

        frm = ttk.Frame(self, padding=14)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="CA Foundation Offline Retrieval Engine — Corrected V2", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(frm, text="100% offline • deterministic ICAI_BLOCK retrieval • no AI/API required").pack(anchor="w", pady=(2, 12))

        row = ttk.Frame(frm); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Beautified MD folder:", width=22).pack(side="left")
        self.data_var = tk.StringVar(value=str(DEFAULT_DATA))
        ttk.Entry(row, textvariable=self.data_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", command=self.browse_data).pack(side="left", padx=(6,0))
        ttk.Button(row, text="Load", command=self.load_data).pack(side="left", padx=(6,0))

        ttk.Separator(frm).pack(fill="x", pady=12)
        ttk.Label(frm, text="Simple request (deterministic parser):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.query = tk.Text(frm, height=3, wrap="word")
        self.query.pack(fill="x", pady=(4,8))
        self.query.insert("1.0", "Give me only Illustration questions from all Units of Chapter 2, without solutions")

        opts = ttk.Frame(frm); opts.pack(fill="x", pady=4)
        ttk.Label(opts, text="Or preset:").grid(row=0,column=0,sticky="w")
        self.preset = tk.StringVar(value="")
        ttk.Combobox(opts, textvariable=self.preset, values=[""]+sorted(list(PRESETS)+["everything"]), state="readonly", width=30).grid(row=0,column=1,padx=6)
        labels = [("Paper","paper"),("Module","module"),("Chapter","chapter"),("Unit","unit"),("Topic","topic")]
        self.filters={}
        col=2
        for label,key in labels:
            ttk.Label(opts,text=label).grid(row=0,column=col,padx=(9,2)); col+=1
            v=tk.StringVar(); self.filters[key]=v
            ttk.Entry(opts,textvariable=v,width=6).grid(row=0,column=col); col+=1

        outrow=ttk.Frame(frm); outrow.pack(fill="x", pady=(10,4))
        ttk.Label(outrow,text="Output MD:", width=22).pack(side="left")
        self.out_var=tk.StringVar(value=str(ROOT/"output.md"))
        ttk.Entry(outrow,textvariable=self.out_var).pack(side="left",fill="x",expand=True)
        ttk.Button(outrow,text="Browse",command=self.browse_output).pack(side="left",padx=(6,0))

        actions=ttk.Frame(frm); actions.pack(fill="x",pady=10)
        ttk.Button(actions,text="Generate Markdown",command=self.generate).pack(side="left")
        ttk.Button(actions,text="Corpus Stats",command=self.show_stats).pack(side="left",padx=6)
        ttk.Button(actions,text="Validate Data",command=self.validate_data).pack(side="left")

        ttk.Label(frm,text="Status / Preview:",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(6,2))
        self.status=tk.Text(frm,wrap="word")
        self.status.pack(fill="both",expand=True)
        self.load_data()

    def browse_data(self):
        p=filedialog.askdirectory(initialdir=self.data_var.get() or str(ROOT))
        if p: self.data_var.set(p)
    def browse_output(self):
        p=filedialog.asksaveasfilename(defaultextension=".md",filetypes=[("Markdown","*.md"),("All files","*.*")])
        if p: self.out_var.set(p)
    def set_status(self,text):
        self.status.delete("1.0","end"); self.status.insert("1.0",text)
    def load_data(self):
        try:
            self.engine=RetrievalEngine(self.data_var.get())
            s=self.engine.stats()
            self.set_status(f"Loaded {s['documents']} Markdown files and {s['blocks']} classified blocks.\nReady.")
        except Exception as e:
            self.engine=None; self.set_status(f"Load error: {e}")
    def _spec(self):
        q=self.query.get("1.0","end").strip()
        if self.preset.get(): spec=spec_from_preset(self.preset.get())
        else:
            from ca_retrieval.query import parse_natural_query
            spec=parse_natural_query(q)
        for key,v in self.filters.items():
            x=v.get().strip()
            if x:
                setattr(spec,key, int(x) if key in {"paper","module","chapter","unit"} else x)
        return spec
    def generate(self):
        if not self.engine: self.load_data()
        if not self.engine: return
        try:
            spec=self._spec(); blocks=self.engine.query(spec); md=self.engine.compile(spec)
            out=Path(self.out_var.get()); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(md,encoding="utf-8")
            rc=self.engine.result_counts(blocks,spec)
            self.set_status(f"Generated {rc['source_items']} source items ({rc['returned_blocks']} returned blocks).\nSaved: {out.resolve()}\n\nPreview:\n\n{md[:5000]}")
            messagebox.showinfo("Completed",f"Saved {rc['source_items']} source items ({rc['returned_blocks']} returned blocks) to:\n{out}")
        except Exception as e: messagebox.showerror("Error",str(e))
    def show_stats(self):
        if not self.engine: self.load_data()
        if self.engine:
            import json; self.set_status(json.dumps(self.engine.stats(),ensure_ascii=False,indent=2))
    def validate_data(self):
        if not self.engine: self.load_data()
        if self.engine:
            import json; r=self.engine.validate(); self.set_status(json.dumps(r,ensure_ascii=False,indent=2)); messagebox.showinfo("Validation",f"Errors: {r['errors']}\nWarnings: {r['warnings']}")

if __name__ == "__main__":
    App().mainloop()
