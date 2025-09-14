# ruff: noqa: I001  # import sorting in this GUI file is intentionally grouped
from __future__ import annotations

from contextlib import suppress
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from ttkthemes import ThemedStyle  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ThemedStyle = None  # type: ignore

from .core import SortOptions, format_exception, gather_files, sort_files

APP_TITLE = "FolderChronicle"


class App(tk.Tk):
    def __init__(self) -> None:  # noqa: PLR0915 - GUI setup is naturally verbose
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(720, 520)
        with suppress(Exception):
            self.iconbitmap(default="")  # no icon file; ignore

        style = ttk.Style(self)
        if ThemedStyle is not None:
            try:
                themed_style = ThemedStyle(self)
                if "adapta" in themed_style.theme_names():
                    themed_style.theme_use("adapta")
                    style = themed_style
                else:
                    style.theme_use("clam")
            except Exception:
                with suppress(Exception):
                    style.theme_use("clam")
        else:
            with suppress(Exception):
                style.theme_use("clam")

        top = ttk.Frame(self, padding=(12, 12, 12, 0))
        top.pack(fill="x")

        ttk.Label(top, text="Target folder:").pack(anchor="w")

        row = ttk.Frame(top)
        row.pack(fill="x", pady=(4, 0))

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(row, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...", command=self.browse).pack(side="left", padx=(8, 0))

        opts = ttk.Frame(top)
        opts.pack(fill="x", pady=(8, 0))
        self.include_subdirs_var = tk.BooleanVar(value=False)
        self.use_ctime_var = tk.BooleanVar(value=False)
        self.copy_no_backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Include subfolders", variable=self.include_subdirs_var).pack(
            side="left"
        )
        ttk.Checkbutton(opts, text="Use creation time", variable=self.use_ctime_var).pack(
            side="left", padx=(16, 0)
        )
        ttk.Checkbutton(
            opts, text="Copy instead of move (no backup)", variable=self.copy_no_backup_var
        ).pack(side="left", padx=(16, 0))

        stat_frame = ttk.Frame(self, padding=12)
        stat_frame.pack(fill="x")
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(stat_frame, textvariable=self.status_var)
        self.status_label.pack(anchor="w")

        prog_frame = ttk.Frame(self, padding=(12, 0))
        prog_frame.pack(fill="x")
        self.progress = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")

        log_frame = ttk.LabelFrame(self, text="Activity log", padding=8)
        log_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.log_text = tk.Text(log_frame, wrap="word", height=16, state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        btn_row = ttk.Frame(self, padding=(12, 0, 12, 12))
        btn_row.pack(fill="x")
        self.sort_btn = ttk.Button(btn_row, text="Sort", command=self.start_sort)
        self.sort_btn.pack(side="right")

        self._working = False

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def set_progress(self, total: int, value: int) -> None:
        self.progress.configure(maximum=max(total, 1))
        self.progress["value"] = value

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def browse(self) -> None:
        initial = self.path_var.get() or os.getcwd()
        path = filedialog.askdirectory(title="Select folder", initialdir=initial)
        if path:
            self.path_var.set(path)

    def start_sort(self) -> None:
        if self._working:
            return
        base = Path(self.path_var.get()).expanduser()
        if not base.exists() or not base.is_dir():
            messagebox.showerror(APP_TITLE, "Please select a valid folder.")
            return

        self._working = True
        self.sort_btn.state(["disabled"])
        self.path_entry.state(["disabled"])
        self.set_status("Scanning files...")
        self.set_progress(1, 0)
        self.clear_log()

        include_subdirs = self.include_subdirs_var.get()
        use_ctime = self.use_ctime_var.get()
        copy_no_backup = self.copy_no_backup_var.get()

        t = threading.Thread(
            target=self._worker_sort,
            args=(base, include_subdirs, use_ctime, copy_no_backup),
            daemon=True,
        )
        t.start()

    def _post(self, func, *args, **kwargs) -> None:
        self.after(0, lambda: func(*args, **kwargs))

    def _worker_sort(
        self,
        base_dir: Path,
        include_subdirs: bool,
        use_ctime: bool,
        copy_no_backup: bool,
    ) -> None:
        try:
            opts = SortOptions(
                base_dir=base_dir,
                include_subdirs=include_subdirs,
                use_ctime=use_ctime,
                copy_no_backup=copy_no_backup,
            )

            files = []
            try:
                files = gather_files(base_dir, include_subdirs)
            except Exception as e:
                self._post(self.set_status, "Idle")
                self._post(messagebox.showerror, APP_TITLE, (
                    f"Failed to read directory: {format_exception(e)}"
                ))
                return

            total = len(files)
            if total == 0:
                self._post(self.set_status, "No files to sort")
                self._post(messagebox.showinfo, APP_TITLE, "No files found in the selected folder.")
                return

            # Backup progress
            if not copy_no_backup:
                self._post(self.set_status, f"Creating backup ({total} file(s))...")
                self._post(self.set_progress, total, 0)

            # Sorting
            self._post(self.set_status, f"Sorting {total} file(s)...")
            self._post(self.set_progress, total, 0)

            moved = 0
            errors = 0
            for idx, _ in enumerate(files, start=1):
                # We purposely invoke sort in one go and then just update progress incrementally
                self._post(self.set_progress, total, idx)
                self._post(self.set_status, f"Processed {idx}/{total}")

            moved, errors, logs = sort_files(opts)
            for line in logs:
                self._post(self.log, line)

            summary_action = "Copied" if copy_no_backup else "Moved"
            summary = f"Done. {summary_action} {moved} file(s). Errors: {errors}."
            self._post(self.log, summary)
            self._post(self.set_status, "Done")
            if errors:
                self._post(messagebox.showwarning, APP_TITLE, summary)
            else:
                self._post(messagebox.showinfo, APP_TITLE, summary)
        finally:
            self._post(self.sort_btn.state, ["!disabled"])
            self._post(self.path_entry.state, ["!disabled"])
            self._post(self.set_progress, 1, 0)
            self._post(setattr, self, "_working", False)


def main() -> None:
    app = App()
    app.mainloop()
