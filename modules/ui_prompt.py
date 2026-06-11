"""
AI 提示词模板生成器 — PCL-CE 风格 UI
输入项目描述，生成结构化提示词，复制/导出。
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    make_button, make_secondary_button,
    make_entry, make_text, make_label,
    flash_title,
)

DEFAULT_TEMPLATE = """# 项目：{project_name}

## 项目描述
{description}

## 技术栈要求
- 语言: Python 3.10+
- 框架: (按需选择)
- 数据库: (按需选择)

## 功能需求
1. (功能一)
2. (功能二)
3. (功能三)

## 输出要求
- 提供完整的可运行代码
- 包含必要的注释
- 遵循 PEP 8 规范

## 额外说明
{extra}
"""


class PromptWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "prompt"
    WIN_W, WIN_H = 860, 680

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("提示词生成")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(500, 400)
        self.configure(bg=C["bg"])
        self._template = DEFAULT_TEMPLATE
        self._template_path = None
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _build_ui(self):
        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # 左侧输入
        left_card = Card(main, padding=10)
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        make_label(left_card.inner, text="项目描述", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._desc_text = make_text(left_card.inner, height=12, font=F["body"])
        self._desc_text.pack(fill=tk.BOTH, expand=True)
        self._desc_text.insert("1.0", "一个待办事项管理应用，支持增删改查，数据持久化存储。")

        # 控制栏
        ctrl = tk.Frame(left_card.inner, bg=C["bg_card"])
        ctrl.pack(fill=tk.X, pady=6)

        make_label(ctrl, text="模板:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)
        self._template_var = tk.StringVar(value="默认模板")
        make_entry(ctrl, textvariable=self._template_var, width=20,
                   font=F["body"], state="readonly",
                   highlightthickness=0).pack(side=tk.LEFT, padx=4)
        make_secondary_button(ctrl, text="导入模板",
                              command=self._load_template).pack(side=tk.LEFT, padx=2)
        make_secondary_button(ctrl, text="重置默认",
                              command=self._reset_template).pack(side=tk.LEFT, padx=2)

        # 右侧结果
        right_card = Card(main, padding=10)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        make_label(right_card.inner, text="生成的提示词", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._result_text = make_text(right_card.inner, height=12, font=F["mono_sm"],
                                       fg=C["success"], state=tk.DISABLED, wrap=tk.WORD)
        self._result_text.pack(fill=tk.BOTH, expand=True)

        # 底部
        action = tk.Frame(self, bg=C["bg"])
        action.pack(fill=tk.X, padx=14, pady=(0, 10))

        make_button(action, text="生成", command=self._generate).pack(side=tk.LEFT)
        make_secondary_button(action, text="复制结果",
                              command=self._copy).pack(side=tk.LEFT, padx=8)
        make_secondary_button(action, text="导出文件",
                              command=self._export).pack(side=tk.LEFT)

        make_secondary_button(action, text="清空",
                              command=self._clear).pack(side=tk.RIGHT)

    def _load_template(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("所有文件", "*.*")],
            title="选择模板 JSON 文件")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._template = data.get("template", DEFAULT_TEMPLATE)
            self._template_path = path
            self._template_var.config(state="normal")
            self._template_var.set(os.path.basename(path))
            self._template_var.config(state="readonly")
            messagebox.showinfo("成功", f"已加载模板: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    def _reset_template(self):
        self._template = DEFAULT_TEMPLATE
        self._template_path = None
        self._template_var.config(state="normal")
        self._template_var.set("默认模板")
        self._template_var.config(state="readonly")

    def _generate(self):
        desc = self._desc_text.get("1.0", tk.END).strip()
        if not desc:
            messagebox.showinfo("提示", "请输入项目描述")
            return
        project_name = desc.split("\n")[0].strip()[:40]
        if len(project_name) > 30:
            project_name = project_name[:30] + "..."

        content = self._template.format(
            project_name=project_name,
            description=desc,
            extra="请根据上述需求实现完整代码。",
        )
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.insert("1.0", content)
        self._result_text.config(state=tk.DISABLED)

    def _copy(self):
        text = self._result_text.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            flash_title(self, "✓ 已复制")

    def _export(self):
        text = self._result_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("提示", "请先生成提示词")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("所有文件", "*.*")],
            title="导出提示词")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("成功", f"已导出至:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _clear(self):
        self._desc_text.delete("1.0", tk.END)
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.config(state=tk.DISABLED)
