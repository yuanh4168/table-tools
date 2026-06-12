#!/usr/bin/env python3
"""
table-tools 桌面工具集 — 全新侧边栏 UI
左侧固定260px侧边栏，右侧自适应卡片区，支持深浅色主题。
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from modules.ui_common import (  # noqa: E402
    ImageBackgroundMixin, get_theme_manager, C, F,
    MODULE_ICONS, MODULE_NAMES, ModuleButton,
    SidebarButton, make_theme_toggle, make_separator,
    make_secondary_button,
    ensure_assets_dir, center_window, enable_dpi_aware,
)


# ---------- 模块注册 ----------
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
    ("translate",    "modules.ui_translate",     "TranslateWindow"),
    ("chat",         "modules.ui_chat",          "ChatWindow"),
    ("news",         "modules.ui_news",          "NewsWindow"),
    ("document",     "modules.ui_document",      "DocumentWindow"),
    ("prompt",       "modules.ui_prompt",        "PromptWindow"),
    ("project-tree", "modules.ui_project_tree",  "ProjectTreeWindow"),
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


def _launch_module(key: str):
    """启动模块。"""
    if key == "stone":
        messagebox.showinfo("CLI 模式",
            "石头艺术仅支持 CLI 模式\n请在终端运行: python cli.py stone")
        return
    ctor = _get_ctor(key)
    if ctor:
        ctor()
    else:
        name = MODULE_NAMES.get(key, key)
        messagebox.showinfo("CLI 模式",
            f"「{name}」仅支持 CLI 模式\n请在终端运行: python cli.py {key} --help")


MODULES = [
    "mc_ping", "chess", "translate",
    "chat", "news", "document",
    "prompt", "project-tree",
]


# ---------- 主窗口 ----------

class LauncherWindow(tk.Tk, ImageBackgroundMixin):
    """侧边栏布局主窗口。"""

    MODULE_NAME = "launcher"
    WIN_W, WIN_H = 1100, 720
    SIDEBAR_W = 260

    def __init__(self):
        tk.Tk.__init__(self)
        ImageBackgroundMixin.__init__(self)
        self.title("table-tools 桌面工具集")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])

        center_window(self, self.WIN_W, self.WIN_H)

        self._build_layout()
        self._build_sidebar()
        self._build_main_area()

        # 监听主题变化
        get_theme_manager().add_listener(self._on_theme_change)

    def _build_layout(self):
        """主布局：左侧侧边栏 + 右侧主区域。"""
        # 侧边栏阴影效果框
        self._sidebar_frame = tk.Frame(self, bg=C["sidebar"], width=self.SIDEBAR_W)
        self._sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar_frame.pack_propagate(False)

        # 分隔线
        self._separator = tk.Frame(self, bg=C["border"], width=1)
        self._separator.pack(side=tk.LEFT, fill=tk.Y)

        # 右侧主区域
        self._main_frame = tk.Frame(self, bg=C["bg"])
        self._main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _build_sidebar(self):
        """构建侧边栏内容。"""
        sb = self._sidebar_frame

        # Logo/标题
        logo_frame = tk.Frame(sb, bg=C["sidebar"])
        logo_frame.pack(fill=tk.X, pady=(24, 8))

        logo_text = tk.Label(logo_frame, text="table-tools",
                             font=("微软雅黑", 18, "bold"),
                             fg=C["primary"], bg=C["sidebar"])
        logo_text.pack(padx=20, anchor="w")

        subtitle = tk.Label(logo_frame, text="桌面工具集",
                            font=F["small"],
                            fg=C["fg_muted"], bg=C["sidebar"])
        subtitle.pack(padx=20, anchor="w")

        # 分隔
        make_separator(sb, bg=C["separator"]).pack(fill=tk.X, padx=16, pady=(8, 4))

        # 导航按钮
        nav_frame = tk.Frame(sb, bg=C["sidebar"])
        nav_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # "首页" 按钮
        self._home_btn = SidebarButton(
            nav_frame, "🏠", "首页", active=True,
            command=lambda: self._show_home())
        self._home_btn.pack(fill=tk.X, pady=1)

        # 模块导航按钮
        self._nav_buttons = {}
        for key in MODULES:
            icon = MODULE_ICONS.get(key, "?")
            name = MODULE_NAMES.get(key, key)
            btn = SidebarButton(
                nav_frame, icon, name, active=False,
                command=lambda k=key: _launch_module(k))
            btn.pack(fill=tk.X, pady=1)
            self._nav_buttons[key] = btn

        # 底部：主题切换 + 退出
        bottom_frame = tk.Frame(sb, bg=C["sidebar"])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=12)

        self._theme_btn = make_theme_toggle(bottom_frame)
        self._theme_btn.config(bg=C["bg_secondary"], fg=C["fg_secondary"])
        self._theme_btn.pack(fill=tk.X, pady=(0, 6))

        exit_btn = make_secondary_button(
            bottom_frame, text="退出", command=self.destroy)
        exit_btn.config(bg=C["bg_secondary"], fg=C["fg_secondary"])
        exit_btn.pack(fill=tk.X)

    def _build_main_area(self):
        """构建右侧主内容区 — 模块卡片网格。"""
        main = self._main_frame

        # 清空旧内容
        for w in main.winfo_children():
            w.destroy()

        # 标题
        header = tk.Frame(main, bg=C["bg"])
        header.pack(fill=tk.X, padx=30, pady=(30, 10))

        tk.Label(header, text="选择功能模块",
                 font=F["h1"], fg=C["fg"], bg=C["bg"]).pack(anchor="w")

        tk.Label(header, text="点击卡片启动对应工具",
                 font=F["subtitle"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(anchor="w", pady=(2, 0))

        # 模块卡片网格 (3列)
        card_frame = tk.Frame(main, bg=C["bg"])
        card_frame.pack(expand=True, fill=tk.BOTH, padx=24, pady=10)

        self._module_cards = {}
        cols = 3
        for i, key in enumerate(MODULES):
            row, col = i // cols, i % cols
            icon = MODULE_ICONS.get(key, "?")
            name = MODULE_NAMES.get(key, key)

            btn = ModuleButton(card_frame, key, icon, name,
                               command=lambda k=key: _launch_module(k))
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card_frame.grid_rowconfigure(row, weight=1)
            card_frame.grid_columnconfigure(col, weight=1)

        # CLI 提示
        tip_frame = tk.Frame(main, bg=C["bg"])
        tip_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        tk.Label(tip_frame,
                 text="提示: 也可在终端运行 python cli.py <命令> 查看 CLI 模式",
                 font=F["small"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(side=tk.LEFT)

    def _show_home(self):
        """显示首页（主内容区）。"""
        self._home_btn.set_active(True)
        for btn in self._nav_buttons.values():
            btn.set_active(False)
        self._build_main_area()

    def _on_theme_change(self):
        """主题变更时刷新 UI。"""
        self.configure(bg=C["bg"])

        # 侧边栏
        self._sidebar_frame.config(bg=C["sidebar"])
        self._separator.config(bg=C["border"])

        # 主区域
        self._main_frame.config(bg=C["bg"])

        # 刷新侧边栏内容
        for w in self._sidebar_frame.winfo_children():
            try:
                if isinstance(w, tk.Frame):
                    for child in w.winfo_children():
                        try:
                            child.config(bg=C["sidebar"])
                        except Exception:
                            pass
                w.config(bg=C["sidebar"])
            except Exception:
                pass

        # 刷新主区域
        self._build_main_area()


# ---------- 入口 ----------
def main():
    enable_dpi_aware()
    ensure_assets_dir()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
