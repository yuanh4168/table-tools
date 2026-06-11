"""
UI 通用组件 — PCL-CE 风格主题系统
PCL-CE 风格（暗色适配）：卡片式布局、圆角控件、统一色彩体系。
"""

import os
import sys
import configparser
import tkinter as tk
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


# ---------- Windows DPI 感知 ----------
def enable_dpi_aware():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ---------- Pillow 可选导入 ----------
try:
    from PIL import ImageTk  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ==================== PCL-CE 风格色彩体系（暗色主题）====================
C = {
    "bg":             "#1a1b2e",   # 主背景
    "bg_card":        "#252640",   # 卡片表面
    "bg_card_hover":  "#2d2e48",   # 卡片悬浮
    "bg_input":       "#1e1f35",   # 输入框
    "bg_disabled":    "#2a2b42",   # 禁用状态
    "bg_button":      "#3b82f6",   # 主按钮
    "bg_button_hover":"#5b9cf6",   # 主按钮悬浮
    "bg_secondary":   "#353650",   # 次要按钮
    "bg_secondary_hover": "#40406a",
    "bg_accent":      "#3b82f6",   # 强调色/选中
    "bg_tag":         "#3b82f622", # 标签/标记

    "fg":             "#f0f0f0",   # 主要文字
    "fg_secondary":   "#9e9eb8",   # 次要文字
    "fg_muted":       "#6e6e8a",   # 弱化文字
    "fg_inverse":     "#1a1b2e",   # 反色文字

    "border":         "#3a3b5a",   # 边框
    "border_focus":   "#5b9cf6",   # 聚焦边框
    "border_light":   "#4a4b6a",   # 浅边框

    "primary":        "#3b82f6",   # 主色
    "primary_hover":  "#5b9cf6",
    "success":        "#4caf50",   # 成功
    "error":          "#f44336",   # 错误
    "warning":        "#ff9800",   # 警告
    "info":           "#29b6f6",   # 信息

    "online":         "#4caf50",   # 服务器在线
    "offline":        "#f44336",   # 服务器离线
    "motd":           "#ffff55",   # MOTD 颜色
    "player":         "#aaffaa",   # 玩家名
    "version":        "#96c0f9",   # 版本号

    "separator":      "#3a3b5a",   # 分隔线
    "scrollbar":      "#353650",   # 滚动条
    "scrollbar_hover":"#4a4b6a",
    "shadow":         "#00000044", # 阴影
}

FONT = "微软雅黑"
MONO = "Consolas"

F = {
    "h1":     (FONT, 20, "bold"),
    "h2":     (FONT, 14, "bold"),
    "h3":     (FONT, 12, "bold"),
    "body":   (FONT, 11),
    "body_bold": (FONT, 11, "bold"),
    "small":  (FONT, 9),
    "mono":   (MONO, 11),
    "mono_sm":(MONO, 10),
    "mono_bold": (MONO, 11, "bold"),
    "title":  ("微软雅黑", 26, "bold"),
    "subtitle": ("微软雅黑", 12),
    "emoji":  ("Segoe UI Emoji", 36),
}

# 模块图标映射
MODULE_ICONS = {
    "mc_ping":      "⛏",
    "chess":        "♚",
    "stone":        "🪨",
    "translate":    "🌐",
    "chat":         "💬",
    "news":         "📰",
    "document":     "📄",
    "prompt":       "⚡",
    "project-tree": "🌳",
}

MODULE_NAMES = {
    "mc_ping":      "Minecraft 服务器查询",
    "chess":        "中国象棋",
    "stone":        "石头艺术",
    "translate":    "翻译助手",
    "chat":         "AI 对话",
    "news":         "新闻简报",
    "document":     "公文生成",
    "prompt":       "提示词生成",
    "project-tree": "项目结构生成",
}


# ==================== 圆角卡片容器 ====================

class Card(tk.Frame):
    """PCL-CE 风格的卡片容器 — 圆角背景、内边距、可选标题。"""

    def __init__(self, parent, title="", padding=14, **kw):
        super().__init__(parent, bg=C["bg_card"], **kw)
        self._build(title, padding)

    def _build(self, title, padding):
        self.config(highlightbackground=C["border"], highlightthickness=1, bd=0)
        inner = tk.Frame(self, bg=C["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=padding - 2, pady=padding - 2)

        if title:
            hdr = tk.Frame(inner, bg=C["bg_card"])
            hdr.pack(fill=tk.X, pady=(0, 8))
            tk.Label(hdr, text=title, font=F["h3"], fg=C["fg"], bg=C["bg_card"],
                     anchor="w").pack(side=tk.LEFT)
            sep = tk.Frame(hdr, bg=C["border"], height=1)
            sep.pack(fill=tk.X, pady=(4, 0))

        self.inner = inner


# ==================== 统一样式的控件工厂 ====================

def make_label(parent, text="", **kw):
    """统一样式标签。"""
    defaults = {"bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame)) else C["bg"],
                "fg": C["fg_secondary"], "font": F["body"], "anchor": "w"}
    defaults.update(kw)
    return tk.Label(parent, text=text, **defaults)


def make_heading(parent, text="", **kw):
    """标题标签（带强调色）。"""
    defaults = {"bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame)) else C["bg"],
                "fg": C["primary"], "font": F["h2"], "anchor": "w"}
    defaults.update(kw)
    return tk.Label(parent, text=text, **defaults)


def make_button(parent, text="", command: Callable | None = None, **kw):
    """PCL-CE 风格主按钮 — 蓝色填充、圆角感、悬浮高亮。"""
    defaults = {
        "bg": C["bg_button"], "fg": C["fg"], "font": F["body"],
        "relief": tk.FLAT, "cursor": "hand2", "padx": 20, "pady": 4,
        "activebackground": C["bg_button_hover"], "activeforeground": C["fg"],
        "borderwidth": 0, "highlightthickness": 0,
    }
    defaults.update(kw)
    btn = tk.Button(parent, text=text, command=command, **defaults)  # type: ignore[arg-type]

    def on_enter(e=None):
        if btn.cget("state") != tk.DISABLED:
            btn.config(bg=C["bg_button_hover"])

    def on_leave(e=None):
        if btn.cget("state") != tk.DISABLED:
            btn.config(bg=C["bg_button"])

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def make_secondary_button(parent, text="", command=None, **kw):
    """次要按钮 — 暗色填充。"""
    defaults = {
        "bg": C["bg_secondary"], "fg": C["fg_secondary"], "font": F["small"],
        "relief": tk.FLAT, "cursor": "hand2", "padx": 14, "pady": 3,
        "activebackground": C["bg_secondary_hover"], "activeforeground": C["fg"],
        "borderwidth": 0, "highlightthickness": 0,
    }
    defaults.update(kw)
    btn = tk.Button(parent, text=text, command=command, **defaults)  # type: ignore[arg-type]

    def on_enter(e=None):
        if btn.cget("state") != tk.DISABLED:
            btn.config(bg=C["bg_secondary_hover"], fg=C["fg"])

    def on_leave(e=None):
        if btn.cget("state") != tk.DISABLED:
            btn.config(bg=C["bg_secondary"], fg=C["fg_secondary"])

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def make_entry(parent, width=20, **kw):
    """PCL-CE 风格输入框 — 暗色背景、聚焦高亮。"""
    defaults = {
        "bg": C["bg_input"], "fg": C["fg"], "insertbackground": C["fg"],
        "font": F["body"], "relief": tk.FLAT, "highlightthickness": 1.5,
        "highlightbackground": C["border"], "highlightcolor": C["border_focus"],
        "bd": 0,
    }
    defaults.update(kw)
    entry = tk.Entry(parent, width=width, **defaults)
    entry.bind("<FocusIn>", lambda e: entry.config(highlightbackground=C["border_focus"]))
    entry.bind("<FocusOut>", lambda e: entry.config(highlightbackground=C["border"]))
    return entry


def make_text(parent, height=5, **kw):
    """统一样式多行文本框。"""
    defaults = {
        "bg": C["bg_input"], "fg": C["fg"], "insertbackground": C["fg"],
        "font": F["body"], "relief": tk.FLAT, "highlightthickness": 1.5,
        "highlightbackground": C["border"], "highlightcolor": C["border_focus"],
        "bd": 0, "padx": 8, "pady": 6, "wrap": tk.WORD,
    }
    defaults.update(kw)
    txt = tk.Text(parent, height=height, **defaults)
    txt.bind("<FocusIn>", lambda e: txt.config(highlightbackground=C["border_focus"]))
    txt.bind("<FocusOut>", lambda e: txt.config(highlightbackground=C["border"]))
    return txt


def make_checkbutton(parent, text="", variable=None, **kw):
    """统一样式复选框。"""
    defaults = {
        "bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame)) else C["bg"],
        "fg": C["fg"], "selectcolor": C["bg_input"],
        "font": F["body"], "activebackground": C["bg_card"],
        "activeforeground": C["fg"], "relief": tk.FLAT,
        "highlightthickness": 0, "bd": 0,
    }
    defaults.update(kw)
    return tk.Checkbutton(parent, text=text, variable=variable, **defaults)


def make_combobox(parent, values=None, **kw):
    """PCL-CE 风格下拉框。"""
    try:
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("PCL.TCombobox",
                        fieldbackground=C["bg_input"], background=C["bg_card"],
                        foreground=C["fg"], arrowcolor=C["fg_secondary"],
                        selectbackground=C["bg_input"], selectforeground=C["fg"],
                        font=F["body"])
        style.map("PCL.TCombobox",
                  fieldbackground=[("readonly", C["bg_input"])],
                  background=[("readonly", C["bg_card"])])
    except Exception:
        pass
    defaults = {"state": "readonly", "width": 10, "font": F["body"], "style": "PCL.TCombobox"}
    defaults.update(kw)
    return ttk.Combobox(parent, values=values, **defaults)


def make_spinbox(parent, from_=1, to=60, **kw):
    """统一样式数字调节框。"""
    defaults = {
        "bg": C["bg_input"], "fg": C["fg"], "font": F["body"],
        "relief": tk.FLAT, "buttonbackground": C["bg_secondary"],
        "highlightthickness": 1.5, "highlightbackground": C["border"],
        "bd": 0, "width": 4,
    }
    defaults.update(kw)
    return tk.Spinbox(parent, from_=from_, to=to, **defaults)


def make_separator(parent, **kw):
    """分隔线。"""
    defaults = {"bg": C["separator"], "height": 1, "bd": 0}
    defaults.update(kw)
    return tk.Frame(parent, **defaults)


def make_scrollbar(parent, **kw):
    """统一样式滚动条。"""
    defaults = {
        "bg": C["scrollbar"], "activebackground": C["scrollbar_hover"],
        "troughcolor": C["bg"], "width": 10,
        "borderwidth": 0, "highlightthickness": 0,
    }
    defaults.update(kw)
    return tk.Scrollbar(parent, **defaults)


# ==================== 状态指示灯 ====================

class StatusDot(tk.Canvas):
    """PCL-CE 风格状态指示灯 — 绿色(在线)/红色(离线)圆点。"""

    def __init__(self, parent, online=True, size=10, **kw):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0, **kw)
        self._size = size
        self._online = online
        self._draw()

    def _draw(self):
        self.delete("all")
        self.config(bg=self.master.cget("bg"))
        color = C["online"] if self._online else C["offline"]
        self.create_oval(1, 1, self._size - 1, self._size - 1,
                         fill=color, outline=color)

    def set_status(self, online: bool):
        self._online = online
        self._draw()


# ==================== 服务器信息卡片（PCL-CE 风格）====================

class ServerInfoCard(tk.Frame):
    """
    PCL-CE 风格的 Minecraft 服务器信息卡片。
    参考 PCL-CE 的 MinecraftServer.xaml 布局：图标 | MOTD/版本 | 玩家信息。
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg_card"], **kw)
        self.config(highlightbackground=C["border"], highlightthickness=1, bd=0)
        self._build()

    def _build(self):
        inner = tk.Frame(self, bg=C["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=0)

        # 服务器图标
        icon_frame = tk.Frame(inner, bg=C["bg_card"], width=64, height=64)
        icon_frame.grid(row=0, column=0, padx=(0, 12))
        icon_frame.grid_propagate(False)
        self._icon_label = tk.Label(icon_frame, text="", bg=C["bg_card"],
                                    font=("Segoe UI Emoji", 32))
        self._icon_label.place(relx=0.5, rely=0.5, anchor="center")
        self._status_dot = StatusDot(icon_frame, online=True, size=12)
        self._status_dot.place(x=46, y=48)

        # 中间信息区
        info_frame = tk.Frame(inner, bg=C["bg_card"])
        info_frame.grid(row=0, column=1, sticky="w")
        info_frame.grid_columnconfigure(0, weight=1)

        self._motd_label = tk.Label(info_frame, text="", font=("微软雅黑", 14, "bold"),
                                    fg=C["motd"], bg=C["bg_card"], anchor="w")
        self._motd_label.grid(row=0, column=0, sticky="w")

        self._version_label = tk.Label(info_frame, text="", font=F["small"],
                                       fg=C["version"], bg=C["bg_card"], anchor="w")
        self._version_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self._host_label = tk.Label(info_frame, text="", font=F["small"],
                                    fg=C["fg_muted"], bg=C["bg_card"], anchor="w")
        self._host_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

        # 右侧信息
        player_frame = tk.Frame(inner, bg=C["bg_card"])
        player_frame.grid(row=0, column=2, sticky="ne", padx=(12, 0))

        self._online_label = tk.Label(player_frame, text="", font=F["h3"],
                                      fg=C["success"], bg=C["bg_card"], anchor="e")
        self._online_label.pack(anchor="e")

        self._latency_label = tk.Label(player_frame, text="", font=F["body"],
                                       fg=C["info"], bg=C["bg_card"], anchor="e")
        self._latency_label.pack(anchor="e", pady=(2, 0))

        self._player_list = tk.Label(player_frame, text="", font=F["small"],
                                     fg=C["player"], bg=C["bg_card"], anchor="e",
                                     justify=tk.RIGHT)
        self._player_list.pack(anchor="e", pady=(2, 0))

        # 错误信息
        self._error_label = tk.Label(inner, text="", font=F["body_bold"],
                                     fg=C["error"], bg=C["bg_card"], anchor="w")

    def set_result(self, result: dict):
        """填充服务器查询结果。"""
        if result.get("error"):
            self._icon_label.config(text="⚠")
            self._status_dot.set_status(False)
            self._motd_label.config(text="查询失败")
            self._version_label.config(text="")
            self._host_label.config(text="")
            self._online_label.config(text="")
            self._latency_label.config(text="")
            self._player_list.config(text="")
            self._error_label.config(text=result["error"])
            return

        self._error_label.pack_forget()
        self._icon_label.config(text="⛏")
        self._status_dot.set_status(True)
        self._motd_label.config(text=result.get("motd", "") or "Minecraft 服务器")
        self._version_label.config(text=f"版本: {result.get('version', '未知')}")
        self._host_label.config(text=f"{result.get('host', '')}:{result.get('port', '')}")
        self._online_label.config(text=f"{result.get('online', 0)} / {result.get('max', 0)} 在线")
        self._latency_label.config(text=f"{result.get('latency', '?')} ms")

        sample = result.get("players", [])
        if sample:
            names = [p.get("name", "?") for p in sample[:5]]
            text = "玩家: " + ", ".join(names)
            if len(sample) > 5:
                text += f" ... (+{len(sample) - 5})"
            self._player_list.config(text=text)
        else:
            self._player_list.config(text="")

    def set_error(self, msg: str):
        """显示错误信息。"""
        self._icon_label.config(text="⚠")
        self._status_dot.set_status(False)
        self._motd_label.config(text="错误")
        self._version_label.config(text="")
        self._host_label.config(text="")
        self._online_label.config(text="")
        self._latency_label.config(text="")
        self._player_list.config(text="")
        self._error_label.pack(fill=tk.X, pady=(6, 0))
        self._error_label.config(text=msg)


# ==================== 模块按钮（启动器用）====================

class ModuleButton(tk.Frame):
    """PCL-CE 风格的模块启动按钮 — 卡片式、悬浮高亮。"""

    def __init__(self, parent, key: str, icon: str, name: str,
                 command: Callable | None = None, **kw):
        super().__init__(parent, bg=C["bg_card"], cursor="hand2", **kw)
        self.config(highlightbackground=C["border"], highlightthickness=1, bd=0)
        self._command = command
        self._build(icon, name)
        self._bind_events()

    def _build(self, icon, name):
        inner = tk.Frame(self, bg=C["bg_card"])
        inner.pack(expand=True, fill=tk.BOTH, padx=4, pady=4)

        # 图标
        self._icon_label = tk.Label(inner, text=icon, font=F["emoji"],
                                    fg=C["primary"], bg=C["bg_card"])
        self._icon_label.pack(pady=(6, 2))

        # 名称
        self._name_label = tk.Label(inner, text=name, font=F["h3"],
                                    fg=C["fg_secondary"], bg=C["bg_card"])
        self._name_label.pack(pady=(0, 6))

    def _bind_events(self):
        for w in (self, self._icon_label, self._name_label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, e=None):
        self.config(bg=C["bg_card_hover"], highlightbackground=C["primary"])
        for w in self.winfo_children():
            w.config(bg=C["bg_card_hover"])
            for c in w.winfo_children():
                c.config(bg=C["bg_card_hover"])

    def _on_leave(self, e=None):
        self.config(bg=C["bg_card"], highlightbackground=C["border"])
        for w in self.winfo_children():
            w.config(bg=C["bg_card"])
            for c in w.winfo_children():
                c.config(bg=C["bg_card"])

    def _on_click(self, e=None):
        if self._command:
            self._command()


# ==================== 配置文件读取 ====================

_CONFIG_CACHE: configparser.ConfigParser | None = None


def get_config() -> configparser.ConfigParser:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    _CONFIG_CACHE = configparser.ConfigParser()
    _CONFIG_CACHE.read(os.path.join(BASE_DIR, "config.ini"), encoding="utf-8")
    return _CONFIG_CACHE


def cfg_str(section: str, key: str, fallback: str = "") -> str:
    try:
        return get_config().get(section, key, fallback=fallback)
    except Exception:
        return fallback


def cfg_int(section: str, key: str, fallback: int = 0) -> int:
    try:
        return get_config().getint(section, key, fallback=fallback)
    except Exception:
        return fallback


def cfg_bool(section: str, key: str, fallback: bool = False) -> bool:
    try:
        return get_config().getboolean(section, key, fallback=fallback)
    except Exception:
        return fallback


# ==================== 资源管理 ====================

def ensure_assets_dir() -> str:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    return ASSETS_DIR


def asset_path(*names: str) -> str:
    return os.path.join(ASSETS_DIR, *names)


def load_image(path: str, size: tuple[int, int] | None = None) -> tuple[object, bool]:
    if not os.path.isfile(path):
        return None, False

    if HAS_PIL:
        try:
            from PIL import Image as PILImage
            img = PILImage.open(path)  # type: ignore[assignment]
            if size:
                img = img.resize(size, PILImage.Resampling.LANCZOS)  # type: ignore[assignment]
            photo = ImageTk.PhotoImage(img)  # type: ignore[arg-type]
            return photo, True
        except Exception:
            return None, False

    if size:
        return None, False
    try:
        photo = tk.PhotoImage(file=path)  # type: ignore[assignment]
        return photo, False
    except Exception:
        return None, False


def create_bg_label(parent: tk.Widget, module_name: str,
                    width: int | None = None, height: int | None = None):
    ensure_assets_dir()
    path = asset_path(f"{module_name}.png")
    photo, ok = load_image(path, (width, height) if (width and height) else None)
    if photo is None:
        return None, False

    label = tk.Label(parent, image=photo, borderwidth=0, highlightthickness=0)  # type: ignore[arg-type]
    label.image = photo  # type: ignore[attr-defined]
    return label, True


class ImageBackgroundMixin:
    """为窗口添加自定义 PNG 背景支持。"""

    MODULE_NAME: str = ""

    def __init__(self):
        self._bg_label: Optional[tk.Label] = None
        self._has_custom_bg = False

    def setup_bg(self, parent: tk.Widget, width: int = 0, height: int = 0):
        w = width or parent.winfo_reqwidth() or 640
        h = height or parent.winfo_reqheight() or 480
        self._bg_label, self._has_custom_bg = create_bg_label(
            parent, self.MODULE_NAME, int(w), int(h)
        )
        if self._bg_label:
            self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    @property
    def using_custom_bg(self) -> bool:
        return self._has_custom_bg


# ==================== 工具函数 ====================

def center_window(win: tk.Toplevel, w: int, h: int):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def flash_title(win: tk.Toplevel, msg: str, duration_ms: int = 800):
    orig = win.title()
    win.title(msg)
    win.after(duration_ms, lambda: win.title(orig))
