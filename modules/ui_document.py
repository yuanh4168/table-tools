"""
公文/红头文件模板生成 — PCL-CE 风格 UI
表单 + 实时预览 + 导出。
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, make_button, make_secondary_button,
    make_entry, make_text, make_label,
    make_combobox, flash_title,
)


class DocumentWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "document"
    WIN_W, WIN_H = 860, 680

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("公文生成")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(600, 480)
        self.configure(bg=C["bg"])
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)
        self._preview()

    def _build_ui(self):
        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # 左侧表单
        form_card = Card(main, padding=12)
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        row_h = {"bg": C["bg_card"], "fg": C["fg"], "font": F["body"]}

        r = 0
        make_label(form_card.inner, text="发文单位:", **row_h).grid(row=r, column=0, sticky="e", padx=6, pady=6)
        self._org_var = tk.StringVar(value=cfg_str("document", "org", "厦门市教育局"))
        make_entry(form_card.inner, textvariable=self._org_var, width=24).grid(row=r, column=1, padx=6, pady=6)
        self._org_var.trace_add("write", lambda *_: self._preview())

        r = 1
        make_label(form_card.inner, text="文件类型:", **row_h).grid(row=r, column=0, sticky="e", padx=6, pady=6)
        self._type_var = tk.StringVar(value=cfg_str("document", "type", "通知"))
        type_cb = make_combobox(form_card.inner, values=["通知", "通报", "决定", "批复"],
                                textvariable=self._type_var, width=20)
        type_cb.grid(row=r, column=1, padx=6, pady=6)
        type_cb.bind("<<ComboboxSelected>>", lambda e: self._preview())

        r = 2
        make_label(form_card.inner, text="文件标题:", **row_h).grid(row=r, column=0, sticky="e", padx=6, pady=6)
        self._subject_var = tk.StringVar(value="关于...的通知")
        make_entry(form_card.inner, textvariable=self._subject_var, width=24).grid(row=r, column=1, padx=6, pady=6)
        self._subject_var.trace_add("write", lambda *_: self._preview())

        r = 3
        make_label(form_card.inner, text="正文内容:", **row_h).grid(row=r, column=0, sticky="ne", padx=6, pady=6)
        self._content_text = make_text(form_card.inner, width=30, height=10, font=F["body"])
        self._content_text.grid(row=r, column=1, padx=6, pady=6)
        self._content_text.bind("<KeyRelease>", lambda e: self._preview())

        r = 4
        btn_frame = tk.Frame(form_card.inner, bg=C["bg_card"])
        btn_frame.grid(row=r, column=0, columnspan=2, pady=10)

        make_button(btn_frame, text="导出文件", command=self._export).pack(side=tk.LEFT)
        make_secondary_button(btn_frame, text="复制内容",
                              command=self._copy).pack(side=tk.LEFT, padx=6)

        # 右侧预览
        preview_card = Card(main, padding=10)
        preview_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        make_label(preview_card.inner, text="预览", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._preview_text = make_text(preview_card.inner, height=15, font=F["mono"],
                                        fg=C["fg"], state=tk.DISABLED, wrap=tk.WORD)
        self._preview_text.pack(fill=tk.BOTH, expand=True)

    def _generate(self) -> str:
        org = self._org_var.get().strip()
        doc_type = self._type_var.get()
        subject = self._subject_var.get().strip()
        content = self._content_text.get("1.0", tk.END).strip()
        now = datetime.datetime.now()
        doc_number = f"〔{now.year}〕第{now.month}{now.day}号"

        lines = [
            f"# {org}\n",
            f"## {'文' if doc_type == '通知' else ''}{doc_type}\n",
            f"**{org}文件**\n",
            f"**{org}** · {doc_number}\n",
            "---\n",
            f"# {subject}\n",
        ]
        if content:
            lines.append(content)
        else:
            lines.extend([
                "各省、自治区、直辖市有关部门：\n",
                "为贯彻落实党中央、国务院决策部署，现就有关事项通知如下：\n",
                "一、提高思想认识，充分领会工作重要性。\n",
                "二、加强组织领导，确保各项措施落实到位。\n",
                "三、强化监督检查，建立健全长效机制。\n",
                "各地区、各部门要认真贯彻执行，遇到重要情况及时报告。\n",
            ])
        lines.extend([
            "\n---\n",
            f"**{org}**",
            f"{now.year}年{now.month}月{now.day}日",
        ])
        return "\n".join(lines)

    def _preview(self):
        result = self._generate()
        self._preview_text.config(state=tk.NORMAL)
        self._preview_text.delete("1.0", tk.END)
        self._preview_text.insert("1.0", result)
        self._preview_text.config(state=tk.DISABLED)

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("所有文件", "*.*")],
            title="导出公文")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._generate())
            messagebox.showinfo("成功", f"已导出至:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self._generate())
        flash_title(self, "✓ 已复制")
