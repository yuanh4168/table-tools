"""
翻译助手 — PCL-CE 风格 UI
支持 MyMemory 免费 API，剪贴板读取，结果复制。
"""

import tkinter as tk
from tkinter import messagebox
import threading
from modules import translate as mod_translate
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, make_button, make_secondary_button,
    make_text, make_label, make_heading, flash_title,
)


class TranslateWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "translate"
    WIN_W, WIN_H = 720, 560

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("翻译助手")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(500, 400)
        self.configure(bg=C["bg"])
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _build_ui(self):
        # 原文区
        src_card = Card(self, padding=10)
        src_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=(12, 4))

        make_heading(src_card.inner, text="原文").pack(fill=tk.X, pady=(0, 4))
        self._src_text = make_text(src_card.inner, height=5, font=F["body"], wrap=tk.WORD)
        self._src_text.pack(fill=tk.BOTH, expand=True)
        self._src_text.bind("<Control-Return>", lambda e: self._do_translate())

        # 控制栏
        ctrl = tk.Frame(self, bg=C["bg"])
        ctrl.pack(fill=tk.X, padx=14, pady=6)

        make_label(ctrl, text="引擎:", bg=C["bg"], font=F["body"]).pack(side=tk.LEFT)
        self._engine_var = tk.StringVar(value=cfg_str("translate", "engine", "mymemory"))
        tk.Radiobutton(ctrl, text="MyMemory", variable=self._engine_var,
                       value="mymemory", bg=C["bg"], fg=C["fg"],
                       selectcolor=C["bg_input"], font=F["body"],
                       activebackground=C["bg"], activeforeground=C["fg"],
                       relief=tk.FLAT, highlightthickness=0).pack(side=tk.LEFT, padx=2)

        make_secondary_button(ctrl, text="从剪贴板读取",
                              command=self._paste_clipboard).pack(side=tk.LEFT, padx=10)
        make_button(ctrl, text="翻译 (Ctrl+Enter)",
                    command=self._do_translate).pack(side=tk.RIGHT)

        # 译文区
        dst_card = Card(self, padding=10)
        dst_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 4))

        make_heading(dst_card.inner, text="译文").pack(fill=tk.X, pady=(0, 4))

        self._dst_text = make_text(dst_card.inner, height=5, font=F["body"],
                                   fg=C["success"], state=tk.DISABLED, wrap=tk.WORD)
        self._dst_text.pack(fill=tk.BOTH, expand=True)

        # 操作栏
        action = tk.Frame(self, bg=C["bg"])
        action.pack(fill=tk.X, padx=14, pady=(2, 12))

        make_secondary_button(action, text="复制译文",
                              command=self._copy_result).pack(side=tk.LEFT)
        make_secondary_button(action, text="清空",
                              command=self._clear).pack(side=tk.LEFT, padx=8)

    def _paste_clipboard(self):
        try:
            text = self.clipboard_get().strip()
            if text:
                self._src_text.delete("1.0", tk.END)
                self._src_text.insert("1.0", text)
        except Exception:
            pass

    def _do_translate(self):
        text = self._src_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("提示", "请输入或粘贴要翻译的文本")
            return
        engine = self._engine_var.get()
        if engine == "ai":
            messagebox.showinfo("提示", "AI 引擎需在 config.ini 中配置 API 密钥后再用")
            return
        self._dst_text.config(state=tk.NORMAL, fg=C["fg_muted"])
        self._dst_text.delete("1.0", tk.END)
        self._dst_text.insert("1.0", "翻译中...")
        self._dst_text.config(state=tk.DISABLED)
        threading.Thread(target=self._do_query, args=(text,), daemon=True).start()

    def _do_query(self, text):
        try:
            result = mod_translate.translate_mymemory(text)
        except Exception as e:
            result = f"[错误] {e}"
        self.after(0, self._show_result, result)

    def _show_result(self, result):
        self._dst_text.config(state=tk.NORMAL)
        self._dst_text.delete("1.0", tk.END)
        if result.startswith("[错误]"):
            self._dst_text.config(fg=C["error"])
        else:
            self._dst_text.config(fg=C["success"])
        self._dst_text.insert("1.0", result)
        self._dst_text.config(state=tk.DISABLED)

    def _copy_result(self):
        text = self._dst_text.get("1.0", tk.END).strip()
        if text and not text.startswith("翻译中"):
            self.clipboard_clear()
            self.clipboard_append(text)
            flash_title(self, "✓ 已复制")

    def _clear(self):
        self._src_text.delete("1.0", tk.END)
        self._dst_text.config(state=tk.NORMAL)
        self._dst_text.delete("1.0", tk.END)
        self._dst_text.config(state=tk.DISABLED)
