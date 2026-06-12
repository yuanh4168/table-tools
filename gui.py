#!/usr/bin/env python3
"""
table-tools 桌面工具集 — 侧边栏 UI
左侧固定260px侧边栏，右侧自适应卡片区，支持深浅色主题、窗口模式配置。
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
    cfg_str, get_config,
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
            return cls
    return None


MODULES = [
    "mc_ping", "chess", "translate",
    "chat", "news", "document",
    "prompt", "project-tree",
]


# ---------- 窗口模式管理 ----------

def get_window_mode(key: str) -> str:
    """获取模块窗口模式: 'new' 或 'replace'。"""
    mode = cfg_str(key, "window_mode", "").strip().lower()
    if mode not in ("new", "replace"):
        return "new"
    return mode


def set_window_mode(key: str, mode: str):
    """保存模块窗口模式到配置。"""
    cfg = get_config()
    if key not in cfg:
        cfg[key] = {}
    cfg[key]["window_mode"] = mode
    try:
        ini_path = os.path.join(BASE_DIR, "config.ini")
        with open(ini_path, "w", encoding="utf-8") as f:
            cfg.write(f)
    except Exception:
        pass


# ---------- 模块启动 ----------

_launcher_instance: "LauncherWindow | None" = None


def _launch_module(key: str):
    """启动模块 — 支持新窗口/替换窗口模式。"""
    if key == "stone":
        messagebox.showinfo("CLI 模式",
            "石头艺术仅支持 CLI 模式\n请在终端运行: python cli.py stone")
        return

    cls = _get_ctor(key)
    if cls is None:
        name = MODULE_NAMES.get(key, key)
        messagebox.showinfo("CLI 模式",
            f"「{name}」仅支持 CLI 模式\n请在终端运行: python cli.py {key} --help")
        return

    mode = get_window_mode(key)
    try:
        if mode == "replace":
            # 隐藏启动器，在新窗口中打开模块
            global _launcher_instance
            if _launcher_instance:
                _launcher_instance.withdraw()
            win = cls()
            win.protocol("WM_DELETE_WINDOW", lambda w=win, k=key: _on_module_close(w, k))
        else:
            win = cls()
            win.focus_set()
    except Exception as e:
        messagebox.showerror("启动失败", str(e))


def _on_module_close(win, key):
    """模块窗口关闭时，恢复启动器。"""
    try:
        win.destroy()
    except Exception:
        pass
    global _launcher_instance
    if _launcher_instance and get_window_mode(key) == "replace":
        try:
            _launcher_instance.deiconify()
            _launcher_instance.focus_set()
            _launcher_instance.lift()
        except Exception:
            pass


# ---------- 主窗口 ----------

class LauncherWindow(tk.Tk, ImageBackgroundMixin):
    """侧边栏布局主窗口。"""

    MODULE_NAME = "launcher"
    WIN_W, WIN_H = 1100, 720
    SIDEBAR_W = 260

    def __init__(self):
        global _launcher_instance
        _launcher_instance = self

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

        get_theme_manager().add_listener(self._on_theme_change)

    def _build_layout(self):
        self._sidebar_frame = tk.Frame(self, bg=C["sidebar"], width=self.SIDEBAR_W)
        self._sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar_frame.pack_propagate(False)

        self._separator = tk.Frame(self, bg=C["border"], width=1)
        self._separator.pack(side=tk.LEFT, fill=tk.Y)

        self._main_frame = tk.Frame(self, bg=C["bg"])
        self._main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _clear_main(self):
        for w in self._main_frame.winfo_children():
            w.destroy()

    def _build_sidebar(self):
        sb = self._sidebar_frame

        # Logo
        logo_frame = tk.Frame(sb, bg=C["sidebar"])
        logo_frame.pack(fill=tk.X, pady=(24, 8))

        tk.Label(logo_frame, text="table-tools",
                 font=("微软雅黑", 18, "bold"),
                 fg=C["primary"], bg=C["sidebar"]).pack(padx=20, anchor="w")

        tk.Label(logo_frame, text="桌面工具集",
                 font=F["small"],
                 fg=C["fg_muted"], bg=C["sidebar"]).pack(padx=20, anchor="w")

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

        # 设置按钮
        make_separator(sb, bg=C["separator"]).pack(fill=tk.X, padx=16, pady=(4, 2))
        self._settings_btn = SidebarButton(
            nav_frame, "⚙", "设置", active=False,
            command=lambda: self._show_settings())
        self._settings_btn.pack(fill=tk.X, pady=1)

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
        """首页 — 模块卡片网格。"""
        self._clear_main()
        main = self._main_frame

        header = tk.Frame(main, bg=C["bg"])
        header.pack(fill=tk.X, padx=30, pady=(30, 10))

        tk.Label(header, text="选择功能模块",
                 font=F["h1"], fg=C["fg"], bg=C["bg"]).pack(anchor="w")
        tk.Label(header, text="点击卡片启动对应工具",
                 font=F["subtitle"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(anchor="w", pady=(2, 0))

        card_frame = tk.Frame(main, bg=C["bg"])
        card_frame.pack(expand=True, fill=tk.BOTH, padx=24, pady=10)

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

        tip_frame = tk.Frame(main, bg=C["bg"])
        tip_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        tk.Label(tip_frame,
                 text="提示: 也可在终端运行 python cli.py <命令> 查看 CLI 模式",
                 font=F["small"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(side=tk.LEFT)

    def _show_home(self):
        """显示首页。"""
        self._home_btn.set_active(True)
        self._settings_btn.set_active(False)
        for btn in self._nav_buttons.values():
            btn.set_active(False)
        self._build_main_area()

    def _show_settings(self):
        """显示设置页面。"""
        self._home_btn.set_active(False)
        self._settings_btn.set_active(True)
        for btn in self._nav_buttons.values():
            btn.set_active(False)
        self._clear_main()

        main = self._main_frame

        header = tk.Frame(main, bg=C["bg"])
        header.pack(fill=tk.X, padx=30, pady=(24, 10))

        tk.Label(header, text="设置",
                 font=F["h1"], fg=C["fg"], bg=C["bg"]).pack(anchor="w")
        tk.Label(header, text="配置各模块的启动方式",
                 font=F["subtitle"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(anchor="w", pady=(2, 0))

        # 窗口模式配置
        cfg_card = tk.Frame(main, bg=C["bg"])
        cfg_card.pack(fill=tk.X, padx=30, pady=10)

        tk.Label(cfg_card, text="窗口模式",
                 font=F["h2"], fg=C["fg"], bg=C["bg"]).pack(anchor="w", pady=(0, 8))

        tk.Label(cfg_card, text="每个模块可设为「新窗口」或「替换启动器窗口」(隐藏启动器，模块关闭后恢复)",
                 font=F["small"], fg=C["fg_muted"],
                 bg=C["bg"]).pack(anchor="w", pady=(0, 12))

        modes = [("new", "新窗口"), ("replace", "替换启动器")]
        self._mode_vars = {}

        for key in MODULES:
            name = MODULE_NAMES.get(key, key)
            row = tk.Frame(cfg_card, bg=C["bg"])
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=f"{MODULE_ICONS.get(key, '?')} {name}",
                     font=F["body"], fg=C["fg"], bg=C["bg"],
                     width=22, anchor="w").pack(side=tk.LEFT)

            current = get_window_mode(key)
            var = tk.StringVar(value=current)
            self._mode_vars[key] = var

            for val, lbl in modes:
                rb = tk.Radiobutton(
                    row, text=lbl, variable=var, value=val,
                    bg=C["bg"], fg=C["fg"], selectcolor=C["bg_card"],
                    font=F["small"], activebackground=C["bg"], activeforeground=C["fg"],
                    relief=tk.FLAT, highlightthickness=0,
                    command=lambda k=key, v=var: set_window_mode(k, v.get()),
                )
                rb.pack(side=tk.LEFT, padx=6)

    def _on_theme_change(self):
        self.configure(bg=C["bg"])
        self._sidebar_frame.config(bg=C["sidebar"])
        self._separator.config(bg=C["border"])
        self._main_frame.config(bg=C["bg"])

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

        # 只刷新首页，不刷新设置页（简化处理）
        self._build_main_area()


# ---------- 入口 ----------
def main():
    enable_dpi_aware()
    ensure_assets_dir()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
