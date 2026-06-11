"""
项目结构生成器 — PCL-CE 风格 UI
粘贴 tree /f 目录树文本，预览并创建文件结构。
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import re
import threading
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, make_button, make_secondary_button,
    make_entry, make_text, make_label,
    make_checkbutton,
)


class ProjectTreeWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "project_tree"
    WIN_W, WIN_H = 860, 680

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("项目结构生成")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(500, 400)
        self.configure(bg=C["bg"])
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _build_ui(self):
        # 顶部控制
        top_card = Card(self, padding=8)
        top_card.pack(fill=tk.X, padx=12, pady=8)

        row = top_card.inner
        make_label(row, text="目标目录:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)
        self._dir_var = tk.StringVar(value=cfg_str("project-tree", "output", os.getcwd()))
        make_entry(row, textvariable=self._dir_var, width=40,
                   font=F["mono_sm"], highlightthickness=0).pack(side=tk.LEFT, padx=4)
        make_secondary_button(row, text="浏览",
                              command=self._browse_dir).pack(side=tk.LEFT, padx=2)

        self._dry_run_var = tk.BooleanVar(value=True)
        make_checkbutton(row, text="仅预览", variable=self._dry_run_var,
                         bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT, padx=12)

        # 主区域
        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # 左侧输入
        left_card = Card(main, padding=8)
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        make_label(left_card.inner, text="粘贴目录树文本 (tree /f 格式)", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._input_text = make_text(left_card.inner, height=10, font=F["mono_sm"], wrap=tk.NONE)
        self._input_text.pack(fill=tk.BOTH, expand=True)

        h_scroll = tk.Scrollbar(left_card.inner, orient=tk.HORIZONTAL,
                                command=self._input_text.xview, bg=C["scrollbar"])
        self._input_text.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self._input_text.insert("1.0", (
            "project_root/\n"
            "├── src/\n"
            "│   ├── main.py\n"
            "│   └── utils.py\n"
            "├── README.md\n"
            "└── requirements.txt\n"
        ))

        # 右侧预览/日志
        right_card = Card(main, padding=8)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        make_label(right_card.inner, text="预览 / 日志", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._log_text = make_text(right_card.inner, height=10, font=F["mono_sm"],
                                    fg=C["success"], state=tk.DISABLED, wrap=tk.WORD)
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # 底部操作
        action = tk.Frame(self, bg=C["bg"])
        action.pack(fill=tk.X, padx=12, pady=(4, 10))

        self._gen_btn = make_button(action, text="生成 / 预览", command=self._generate)
        self._gen_btn.pack(side=tk.LEFT)
        make_secondary_button(action, text="清空日志",
                              command=self._clear_log).pack(side=tk.LEFT, padx=8)
        make_secondary_button(action, text="从文件导入",
                              command=self._load_file).pack(side=tk.LEFT)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="选择目标目录")
        if path:
            self._dir_var.set(path)

    def _load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="导入目录树文件")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._input_text.delete("1.0", tk.END)
                self._input_text.insert("1.0", f.read())
        except Exception as e:
            messagebox.showerror("读取失败", str(e))

    def _clear_log(self):
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _log(self, msg):
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, msg + "\n")
        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _parse_entries(self):
        text = self._input_text.get("1.0", tk.END)
        entries = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^[├└│]", stripped):
                clean = re.sub(r"[├─└│]", "", stripped).strip()
            else:
                clean = stripped
            if clean:
                entries.append(clean)
        return entries

    def _generate(self):
        entries = self._parse_entries()
        if not entries:
            messagebox.showinfo("提示", "未解析到任何条目，请粘贴 tree /f 格式的文本")
            return

        output_dir = self._dir_var.get().strip()
        dry_run = self._dry_run_var.get()
        self._gen_btn.config(state=tk.DISABLED, text="处理中...")

        if dry_run:
            self._clear_log()
            self._log("=== 预览模式 (--dry-run) ===")
            self._log(f"目标目录: {output_dir}")
            self._log(f"解析到 {len(entries)} 个条目\n")
            for entry in entries:
                marker = "[DIR]" if entry.endswith("/") else "[FILE]"
                self._log(f"  {marker} {entry}")
            self._gen_btn.config(state=tk.NORMAL, text="生成 / 预览")
            return

        threading.Thread(target=self._create_worker,
                         args=(entries, output_dir), daemon=True).start()

    def _create_worker(self, entries, output_dir):
        created_files = 0
        created_dirs = 0
        self.after(0, self._clear_log)
        self.after(0, self._log, "=== 创建结构 ===")
        self.after(0, self._log, f"目标目录: {output_dir}\n")

        for entry in entries:
            is_dir = entry.endswith("/")
            path = os.path.join(output_dir, entry.rstrip("/"))
            try:
                if is_dir:
                    os.makedirs(path, exist_ok=True)
                    created_dirs += 1
                    self.after(0, self._log, f"  [DIR]  {entry}")
                else:
                    dirname = os.path.dirname(path)
                    if dirname:
                        os.makedirs(dirname, exist_ok=True)
                    if not os.path.exists(path):
                        with open(path, "w", encoding="utf-8") as f:
                            f.write("")
                        created_files += 1
                        self.after(0, self._log, f"  [FILE] {entry}")
                    else:
                        self.after(0, self._log, f"  [已存在] {entry}")
            except Exception as e:
                self.after(0, self._log, f"  [错误] {entry}: {e}")

        self.after(0, self._log, f"\n完成: 创建 {created_dirs} 个目录, {created_files} 个文件")
        self.after(0, lambda: self._gen_btn.config(state=tk.NORMAL, text="生成 / 预览"))
