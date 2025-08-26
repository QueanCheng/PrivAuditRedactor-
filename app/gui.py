"""
Tkinter-based GUI for the PrivAuditRedactor tool.

This UI is intentionally minimal — built for reviewers and non-technical users.
Comments and labels are a bit more verbose than usual because reviewers often
prefer clear UI wording.
"""

# TODO: Consider replacing with a web UI for better UX in future.


import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from par_core.service import process_file
from par_core.db import export_chain_html

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PrivAuditRedactor - 隐私脱敏与审计")
        self.geometry("1000x680")
        self.strategy = tk.StringVar(value="smart")
        self.user = tk.StringVar(value="user")
        self.input_path = None
        self._build()

    def _build(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="用户：").pack(side="left")
        ttk.Entry(top, textvariable=self.user, width=15).pack(side="left", padx=5)
        ttk.Label(top, text="策略：").pack(side="left", padx=(15,0))
        ttk.Combobox(top, values=["smart","full"], textvariable=self.strategy, width=10, state="readonly").pack(side="left", padx=5)
        ttk.Button(top, text="选择文件", command=self.pick_file).pack(side="left", padx=10)
        ttk.Button(top, text="批量处理文件夹", command=self.batch_folder).pack(side="left")
        ttk.Button(top, text="导出审计报告", command=self.export_report).pack(side="right")

        mid = ttk.Frame(self); mid.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_before = tk.Text(mid, wrap="word")
        self.text_after = tk.Text(mid, wrap="word")
        self.text_diff = tk.Text(self, wrap="none", height=12)
        ttk.Label(mid, text="原文").grid(row=0, column=0, sticky="w")
        ttk.Label(mid, text="脱敏后").grid(row=0, column=1, sticky="w")
        self.text_before.grid(row=1, column=0, sticky="nsew", padx=(0,5))
        self.text_after.grid(row=1, column=1, sticky="nsew", padx=(5,0))
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)
        mid.rowconfigure(1, weight=1)
        ttk.Label(self, text="差异（Unified Diff）").pack(anchor="w", padx=10)
        self.text_diff.pack(fill="both", expand=False, padx=10, pady=(0,10))

    def pick_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Text", "*.txt *.md *.csv *.log *.json"), ("All files","*.*")])
        if not fp: return
        self.input_path = Path(fp)
        try:
            res = process_file(self.input_path, user=self.user.get(), strategy=self.strategy.get())
        except Exception as e:
            messagebox.showerror("错误", str(e)); return
        self.text_before.delete("1.0","end"); self.text_after.delete("1.0","end"); self.text_diff.delete("1.0","end")
        self.text_before.insert("1.0", self.input_path.read_text(encoding="utf-8", errors="ignore"))
        self.text_after.insert("1.0", res["redacted"])
        self.text_diff.insert("1.0", res["diff"])
        messagebox.showinfo("完成", f"发现敏感片段：{len(res['findings'])}；审计ID：{res['op_id']}")

    def batch_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        out = Path(folder) / "sanitized"
        out.mkdir(exist_ok=True)
        count = 0
        for p in Path(folder).glob("**/*"):
            if p.is_file() and p.suffix.lower() in {".txt",".md",".csv",".log",".json"}:
                try:
                    res = process_file(p, user=self.user.get(), strategy=self.strategy.get())
                    (out / p.name).write_text(res["redacted"], encoding="utf-8")
                    count += 1
                except Exception as e:
                    print(f"[BatchError] {p}: {e}")
        messagebox.showinfo("批量完成", f"共处理 {count} 个文件；输出：{out}")

    def export_report(self):
        fp = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML","*.html")])
        if not fp: return
        try:
            export_chain_html(fp)
            messagebox.showinfo("成功", f"报告已导出：{fp}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()


# Minor change: add a brief 'About' menu and version string for manual inspection.
try:
    __version__ = '0.9.3-review'
except Exception:
    __version__ = '0.9.x'
