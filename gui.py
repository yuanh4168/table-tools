#!/usr/bin/env python3
"""
table-tools 桌面工具集 — PCL-CE 风格 GUI 启动器
卡片式网格布局，统一视觉风格。
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from modules.ui_common import (  # noqa: E402
    ImageBackgroundMixin, C, F, MODULE_ICONS, MODULE_NAMES,
    ModuleButton, ensure_assets_dir, center_window, enable_dpi_aware,
)


# ---------- 模块注册（延迟导入）----------
def _import(module_path: str, class_name: str):
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls
    except Exception as e:
        print(f"[gui] 导入 {module_path}.{class_name} 失败: {e}", file=sys.stderr)
        return None


REGISTRY = [
    ("mc_ping",      "modules.ui_mc_ping",      "MCPingWindow"),
    ("chess",        "modules.ui_chess",        "ChessWindow"),
    ("translate",    "modules.ui_translate",    "TranslateWindow"),
    ("chat",         "modules.ui_chat",         "ChatWindow"),
    ("news",         "modules.ui_news",         "NewsWindow"),
    ("document",     "modules.ui_document",     "DocumentWindow"),
    ("prompt",       "modules.ui_prompt",       "PromptWindow"),
    ("project-tree", "modules.ui_project_tree", "ProjectTreeWindow"),
]


def _get_ctor(key: str):
    for k, mod_path, cls_name in REGISTRY:
        if k == key:
            cls = _import(mod_path, cls_name)
            if cls is None:
                messagebox.showerror("导入失败",
                    f"无法加载「{MODULE_NAMES.get(key, key)}」模块。\n\n"
                    "请检查终端输出的错误信息。")
                return None
            return lambda: cls()
    return None


def _launch(ctor):
    if ctor is None:
        return
    try:
        w = ctor()
        w.focus_set()
    except Exception as e:
        messagebox.showerror("启动失败", str(e))


# ---------- 模块列表 ----------
MODULES = [
    "mc_ping", "chess", "stone",
    "translate", "chat", "news",
    "document", "prompt", "project-tree",
]


# ---------- PCL-CE 风格启动器 ----------

class LauncherWindow(tk.Tk, ImageBackgroundMixin):
    """PCL-CE 风格主启动器"""

    MODULE_NAME = "launcher"
    WIN_W, WIN_H = 1000, 720

    def __init__(self):
        tk.Tk.__init__(self)
        ImageBackgroundMixin.__init__(self)
        self.title("table-tools 桌面工具集")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(800, 600)
        self.configure(bg=C["bg"])

        center_window(self, self.WIN_W, self.WIN_H)

        # 主容器
        main = tk.Frame(self, bg=C["bg"])
        main.pack(expand=True, fill=tk.BOTH, padx=40, pady=30)

        # 标题区域
        header = tk.Frame(main, bg=C["bg"])
        header.pack(fill=tk.X, pady=(0, 30))

        title_text = "table-tools"
        tk.Label(header, text=title_text, font=F["title"],
                 fg=C["fg"], bg=C["bg"]).pack(anchor="center")

        tk.Label(header, text="桌面工具集 — 点击卡片启动", font=F["subtitle"],
                 fg=C["fg_muted"], bg=C["bg"]).pack(anchor="center", pady=(2, 0))

        # 模块网格 (3 列)
        grid = tk.Frame(main, bg=C["bg"])
        grid.pack(expand=True, fill=tk.BOTH)

        for i, key in enumerate(MODULES):
            row, col = i // 3, i % 3
            icon = MODULE_ICONS.get(key, "?")
            name = MODULE_NAMES.get(key, key)

            btn = ModuleButton(grid, key, icon, name,
                               command=self._make_launch_fn(key))
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            grid.grid_rowconfigure(row, weight=1)
            grid.grid_columnconfigure(col, weight=1)

        # CLI 模式提示
        tip_frame = tk.Frame(main, bg=C["bg"])
        tip_frame.pack(fill=tk.X, pady=(20, 0))

        tip = tk.Label(tip_frame,
                       text="提示: 也可在终端运行 python cli.py <命令> 查看 CLI 模式",
                       font=F["small"], fg=C["fg_muted"], bg=C["bg"])
        tip.pack(side=tk.LEFT)

        exit_btn = tk.Button(tip_frame, text="退出", command=self.destroy,
                             bg=C["bg_secondary"], fg=C["fg_secondary"],
                             font=F["small"], relief=tk.FLAT,
                             padx=16, cursor="hand2",
                             activebackground=C["bg_secondary_hover"],
                             activeforeground=C["fg"],
                             borderwidth=0, highlightthickness=0)
        exit_btn.pack(side=tk.RIGHT)

        # 自定义背景
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _make_launch_fn(self, key):
        def fn():
            if key == "stone":
                msg = "石头艺术仅支持 CLI 模式\n请在终端运行: python cli.py stone"
                messagebox.showinfo("CLI 模式", msg)
                return
            ctor = _get_ctor(key)
            if ctor:
                _launch(ctor)
            else:
                name = MODULE_NAMES.get(key, key)
                msg = (f"「{name}」仅支持 CLI 模式\n"
                       f"请在终端运行: python cli.py {key} --help")
                messagebox.showinfo("CLI 模式", msg)
        return fn


# ---------- 入口 ----------
def main():
    enable_dpi_aware()
    ensure_assets_dir()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
