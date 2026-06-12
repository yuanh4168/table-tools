"""
UI 通用组件 — 全新主题系统
圆角统一12px、毛玻璃效果、深浅色主题切换、动效过渡。
"""

import math
import os
import sys
import configparser
import tkinter as tk
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ---------- Windows DPI ----------
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

# ---------- Pillow ----------
try:
    from PIL import ImageTk  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ==================== 主题系统 ====================

RADIUS = 12  # 统一圆角


def _rgba_alpha(hex_color: str, alpha: float) -> str:
    """将 hex 颜色与 alpha 混合到白色背景上，模拟半透明效果。"""
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    a = max(0, min(1, alpha))
    # 混合到白色背景
    mr = int(r * a + 255 * (1 - a))
    mg = int(g * a + 255 * (1 - a))
    mb = int(b * a + 255 * (1 - a))
    return f"#{mr:02x}{mg:02x}{mb:02x}"


LIGHT_THEME = {
    # 页面背景渐变 #F5F7FA → #E4E8F0
    "bg": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F0F4FF",
    "bg_input": "#F0F2F5",
    "bg_disabled": "#E8EAED",
    "bg_button": "#2C83FD",
    "bg_button_hover": "#2369CA",
    "bg_secondary": "#E8EAED",
    "bg_secondary_hover": "#D0D4DA",
    "bg_accent": "#2C83FD",
    "bg_tag": "#2C83FD18",
    "sidebar": "#FFFFFF",
    "sidebar_hover": "#F0F4FF",
    "sidebar_active": "#E8F0FE",

    "fg": "#18181A",
    "fg_secondary": "#303133",
    "fg_muted": "#909399",
    "fg_inverse": "#FFFFFF",

    "border": "#E4E7ED",
    "border_focus": "#2C83FD",
    "border_light": "#EBEEF5",

    "primary": "#2C83FD",
    "primary_hover": "#2369CA",
    "success": "#61C758",
    "error": "#E34D4F",
    "warning": "#F5A623",
    "info": "#4D9EFF",

    "online": "#61C758",
    "offline": "#E34D4F",
    "motd": "#D4A017",
    "player": "#61C758",
    "version": "#2C83FD",

    "separator": "#E4E7ED",
    "scrollbar": "#D0D4DA",
    "scrollbar_hover": "#B0B4BA",
    "shadow": "#00000015",

    # 毛玻璃背景
    "glass_bg": "#FFFFFFE6",  # rgba(255,255,255,0.9) 混合到 #F5F7FA
    "glass_border": "#FFFFFF40",
}

DARK_THEME = {
    "bg": "#121212",
    "bg_card": "#1E1E1E",
    "bg_card_hover": "#2A2A2A",
    "bg_input": "#2A2A2A",
    "bg_disabled": "#333333",
    "bg_button": "#4D9EFF",
    "bg_button_hover": "#3A7FCC",
    "bg_secondary": "#333333",
    "bg_secondary_hover": "#404040",
    "bg_accent": "#4D9EFF",
    "bg_tag": "#4D9EFF22",
    "sidebar": "#1A1A1A",
    "sidebar_hover": "#252525",
    "sidebar_active": "#2C2C2C",

    "fg": "#EDEDED",
    "fg_secondary": "#B0B0B0",
    "fg_muted": "#707070",
    "fg_inverse": "#121212",

    "border": "#333333",
    "border_focus": "#4D9EFF",
    "border_light": "#2A2A2A",

    "primary": "#4D9EFF",
    "primary_hover": "#3A7FCC",
    "success": "#61C758",
    "error": "#E34D4F",
    "warning": "#F5A623",
    "info": "#4D9EFF",

    "online": "#61C758",
    "offline": "#E34D4F",
    "motd": "#FFD700",
    "player": "#61C758",
    "version": "#4D9EFF",

    "separator": "#333333",
    "scrollbar": "#404040",
    "scrollbar_hover": "#555555",
    "shadow": "#00000030",

    "glass_bg": "#1E1E1EE6",
    "glass_border": "#FFFFFF15",
}

C = dict(LIGHT_THEME)  # 全局颜色字典，主题切换时更新


class ThemeManager:
    """主题管理器 — 管理深浅色主题切换。"""

    _instance: Optional["ThemeManager"] = None
    _listeners: list[Callable] = []
    _dark_mode: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._dark_mode = False
        return cls._instance

    @property
    def is_dark(self) -> bool:
        return self._dark_mode

    def toggle(self) -> bool:
        """切换主题，返回新模式 True=暗色 False=浅色。"""
        self._dark_mode = not self._dark_mode
        theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        C.clear()
        C.update(theme)
        self._notify()
        return self._dark_mode

    def set_light(self):
        if self._dark_mode:
            self._dark_mode = False
            C.clear()
            C.update(LIGHT_THEME)
            self._notify()

    def set_dark(self):
        if not self._dark_mode:
            self._dark_mode = True
            C.clear()
            C.update(DARK_THEME)
            self._notify()

    def add_listener(self, callback: Callable[[], None]):
        """添加主题变更监听器。"""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass


def get_theme_manager() -> ThemeManager:
    return ThemeManager()


# ==================== 字体 ====================

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
    "title":  (FONT, 26, "bold"),
    "subtitle": (FONT, 12),
    "emoji":  ("Segoe UI Emoji", 36),
    "sidebar": (FONT, 13),
    "sidebar_icon": (FONT, 18),
}

# ==================== 模块注册 ====================

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


# ==================== Canvas 圆角矩形工具 ====================

def _draw_rounded_rect(canvas: tk.Canvas, x0, y0, x1, y1, r=RADIUS,
                       fill="", outline="", width=0, **kw):
    """在 Canvas 上绘制圆角矩形。"""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    points = []
    # 顺时针: 左上→右上→右下→左下
    segments = 8  # 每角分段数
    for i in range(4):
        cx = x0 + r if i in (0, 3) else x1 - r
        cy = y0 + r if i in (0, 1) else y1 - r
        start_angle = 90 * i + 180
        for j in range(segments + 1):
            theta = math.radians(start_angle + 90 * j / segments)
            points.append(cx + r * math.cos(theta))
            points.append(cy + r * math.sin(theta))
    return canvas.create_polygon(points, fill=fill, outline=outline, width=width,
                                 smooth=True, **kw)


def _draw_shadow(canvas: tk.Canvas, x0, y0, x1, y1, r=RADIUS, spread=1, blur=15):
    """绘制阴影效果（多层半透明圆角矩形）。"""
    items = []
    layers = min(blur // 3, 8)
    for i in range(layers, 0, -1):
        alpha = 0.04 * (i / layers)
        offset = spread + (layers - i) * 1.5
        sx0, sy0 = x0 + offset, y0 + offset
        sx1, sy1 = x1 + offset, y1 + offset
        items.append(
            _draw_rounded_rect(canvas, sx0, sy0, sx1, sy1, r=r + (layers - i),
                               fill=f"#000000{int(alpha * 255):02x}",
                               outline="", width=0)
        )
    return items


# ==================== 圆角卡片容器 ====================

class RoundedCard(tk.Frame):
    """圆角卡片容器 — Canvas 绘制带阴影和圆角的卡片。"""

    def __init__(self, parent, title="", padding=14, radius=RADIUS,
                 with_shadow=True, glass=False, **kw):
        super().__init__(parent, bg=C["bg"], **kw)
        self._radius = radius
        self._with_shadow = with_shadow
        self._glass = glass
        self._padding = padding
        self._card_bg = C["glass_bg"] if glass else C["bg_card"]
        self._title = title
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0,
                                 bg=C["bg"])
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(self._canvas, bg=self._card_bg)

        # 绑定大小变化以重绘
        self._canvas.bind("<Configure>", self._redraw)
        self._bind_theme()

    def _bind_theme(self):
        mgr = get_theme_manager()
        self._theme_cb = self._on_theme_change
        mgr.add_listener(self._theme_cb)

    def _on_theme_change(self):
        self.config(bg=C["bg"])
        self._card_bg = C["glass_bg"] if self._glass else C["bg_card"]
        self.inner.config(bg=self._card_bg)
        self._canvas.config(bg=C["bg"])
        self._redraw()

    def _redraw(self, event=None):
        w = self._canvas.winfo_width() or 200
        h = self._canvas.winfo_height() or 100
        if w < 10 or h < 10:
            return
        self._canvas.delete("card_bg")
        pad = 2
        # 阴影
        if self._with_shadow:
            _draw_shadow(self._canvas, pad, pad, w - pad, h - pad,
                         r=self._radius, spread=1, blur=15)
        # 卡片背景
        _draw_rounded_rect(self._canvas, pad, pad, w - pad, h - pad,
                           r=self._radius, fill=self._card_bg,
                           outline=C["border"], width=1,
                           tags=("card_bg",))
        # 放置 inner frame
        ih = h - self._padding * 2
        if self._title:
            ih -= 28
        self._canvas.coords(self._canvas.create_window(
            w // 2, h // 2,
            window=self.inner,
            width=max(10, w - self._padding * 2 - 4),
            height=max(10, ih),
        ))
        # 标题
        if self._title:
            self._canvas.create_text(
                self._padding + 4, self._padding + 2,
                text=self._title, anchor="nw",
                font=F["h3"], fill=C["fg"],
                tags=("card_bg",)
            )

    def destroy(self):
        mgr = get_theme_manager()
        if hasattr(self, '_theme_cb'):
            mgr.remove_listener(self._theme_cb)
        super().destroy()


class Card(RoundedCard):
    """兼容原 Card 类 — 直接使用 RoundedCard。"""
    pass


# ==================== 统一样式控件工厂 ====================

def make_label(parent, text="", **kw):
    """统一样式标签。"""
    defaults = {
        "bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame, tk.Canvas)) else C["bg"],
        "fg": C["fg_secondary"], "font": F["body"], "anchor": "w"
    }
    defaults.update(kw)
    return tk.Label(parent, text=text, **defaults)


def make_heading(parent, text="", **kw):
    """标题标签（带主色）。"""
    defaults = {
        "bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame, tk.Canvas)) else C["bg"],
        "fg": C["primary"], "font": F["h2"], "anchor": "w"
    }
    defaults.update(kw)
    return tk.Label(parent, text=text, **defaults)


def make_button(parent, text="", command=None, **kw):
    """主按钮 — 蓝色填充、12px圆角（模拟）、悬浮高亮。"""
    defaults = {
        "bg": C["bg_button"], "fg": C["fg_inverse"], "font": F["body"],
        "relief": tk.FLAT, "cursor": "hand2", "padx": 20, "pady": 6,
        "activebackground": C["bg_button_hover"], "activeforeground": C["fg_inverse"],
        "borderwidth": 0, "highlightthickness": 0,
    }
    defaults.update(kw)
    btn = tk.Button(parent, text=text, command=command, **defaults)

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
    """次要按钮 — 灰色填充、12px圆角（模拟）。"""
    defaults = {
        "bg": C["bg_secondary"], "fg": C["fg_secondary"], "font": F["body"],
        "relief": tk.FLAT, "cursor": "hand2", "padx": 14, "pady": 5,
        "activebackground": C["bg_secondary_hover"], "activeforeground": C["fg"],
        "borderwidth": 0, "highlightthickness": 0,
    }
    defaults.update(kw)
    btn = tk.Button(parent, text=text, command=command, **defaults)

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
    """输入框 — 浅色背景、聚焦高亮、圆角（模拟）。"""
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
        "bg": parent.cget("bg") if isinstance(parent, (tk.Frame, tk.LabelFrame, tk.Canvas)) else C["bg"],
        "fg": C["fg"], "selectcolor": C["bg_input"],
        "font": F["body"], "activebackground": C["bg_card"],
        "activeforeground": C["fg"], "relief": tk.FLAT,
        "highlightthickness": 0, "bd": 0,
    }
    defaults.update(kw)
    return tk.Checkbutton(parent, text=text, variable=variable, **defaults)


def make_combobox(parent, values=None, **kw):
    """下拉框。"""
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


def make_theme_toggle(parent, **kw):
    """主题切换按钮。"""
    mgr = get_theme_manager()
    text = "🌙 深色" if not mgr.is_dark else "☀️ 浅色"

    def toggle():
        mgr.toggle()
        btn.config(text="☀️ 浅色" if mgr.is_dark else "🌙 深色")

    btn = make_secondary_button(parent, text=text, command=toggle, **kw)
    return btn


# ==================== 侧边栏按钮 ====================

class SidebarButton(tk.Frame):
    """侧边栏导航按钮 — 图标 + 名称、悬浮高亮、选中状态。"""

    def __init__(self, parent, icon: str, text: str, active=False,
                 command=None, **kw):
        super().__init__(parent, bg=C["sidebar"], cursor="hand2", **kw)
        self._command = command
        self._active = active
        self._build(icon, text)
        self._bind_events()

        self._theme_cb = self._on_theme_change
        get_theme_manager().add_listener(self._theme_cb)

    def _build(self, icon, text):
        self._icon_label = tk.Label(self, text=icon, font=F["sidebar_icon"],
                                    bg=C["sidebar"], fg=C["primary"])
        self._icon_label.pack(side=tk.LEFT, padx=(18, 8), pady=10)

        self._text_label = tk.Label(self, text=text, font=F["sidebar"],
                                    bg=C["sidebar"], fg=C["fg"])
        self._text_label.pack(side=tk.LEFT, pady=10)

        self._update_active()

    def _update_active(self):
        bg = C["sidebar_active"] if self._active else C["sidebar"]
        fg = C["primary"] if self._active else C["fg"]
        self.config(bg=bg)
        self._icon_label.config(bg=bg, fg=C["primary"])
        self._text_label.config(bg=bg, fg=fg)

    def _bind_events(self):
        for w in (self, self._icon_label, self._text_label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, e=None):
        if not self._active:
            bg = C["sidebar_hover"]
            self.config(bg=bg)
            self._icon_label.config(bg=bg)
            self._text_label.config(bg=bg)

    def _on_leave(self, e=None):
        self._update_active()

    def _on_click(self, e=None):
        if self._command:
            self._command()

    def set_active(self, active: bool):
        self._active = active
        self._update_active()

    def _on_theme_change(self):
        self.config(bg=C["sidebar"])
        self._update_active()

    def destroy(self):
        get_theme_manager().remove_listener(self._theme_cb)
        super().destroy()


# ==================== 状态指示灯 ====================

class StatusDot(tk.Canvas):
    """状态指示灯 — 绿色(在线)/红色(离线)圆点。"""

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
        pad = 1
        self.create_oval(pad, pad, self._size - pad, self._size - pad,
                         fill=color, outline=color)

    def set_status(self, online: bool):
        self._online = online
        self._draw()


# ==================== 服务器信息卡片 ====================

class ServerInfoCard(tk.Frame):
    """Minecraft 服务器信息卡片。"""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg_card"], **kw)
        self._build()
        self._theme_cb = self._on_theme_change
        get_theme_manager().add_listener(self._theme_cb)

    def _build(self):
        self.config(highlightbackground=C["border"], highlightthickness=1, bd=0)
        inner = tk.Frame(self, bg=C["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=0)

        # 服务器图标
        icon_frame = tk.Frame(inner, bg=C["bg_card"], width=64, height=64)
        icon_frame.grid(row=0, column=0, padx=(0, 14))
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

        self._motd_label = tk.Label(info_frame, text="", font=(FONT, 14, "bold"),
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
        player_frame.grid(row=0, column=2, sticky="ne", padx=(14, 0))

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

    def _on_theme_change(self):
        self.config(bg=C["bg_card"])
        self.config(highlightbackground=C["border"])
        for child in self.winfo_children():
            try:
                child.config(bg=C["bg_card"])
            except Exception:
                pass
            for grandchild in child.winfo_children():
                try:
                    grandchild.config(bg=C["bg_card"])
                except Exception:
                    pass

    def set_result(self, result: dict):
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

    def destroy(self):
        get_theme_manager().remove_listener(self._theme_cb)
        super().destroy()


# ==================== 模块按钮（启动器用）=====================

class ModuleButton(tk.Frame):
    """模块启动按钮 — 卡片式、悬浮高亮。"""

    def __init__(self, parent, key: str, icon: str, name: str,
                 command=None, **kw):
        super().__init__(parent, bg=C["bg_card"], cursor="hand2", **kw)
        self._command = command
        self._build(icon, name)
        self._bind_events()
        self._theme_cb = self._on_theme_change
        get_theme_manager().add_listener(self._theme_cb)

    def _build(self, icon, name):
        self.config(highlightbackground=C["border"], highlightthickness=1, bd=0)
        inner = tk.Frame(self, bg=C["bg_card"])
        inner.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)

        self._icon_label = tk.Label(inner, text=icon, font=F["emoji"],
                                    fg=C["primary"], bg=C["bg_card"])
        self._icon_label.pack(pady=(8, 4))

        self._name_label = tk.Label(inner, text=name, font=F["h3"],
                                    fg=C["fg_secondary"], bg=C["bg_card"])
        self._name_label.pack(pady=(0, 8))

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

    def _on_theme_change(self):
        if str(self.cget("bg")) != C["bg_card_hover"]:
            self.config(bg=C["bg_card"], highlightbackground=C["border"])
            for w in self.winfo_children():
                w.config(bg=C["bg_card"])
                for c in w.winfo_children():
                    c.config(bg=C["bg_card"])

    def destroy(self):
        get_theme_manager().remove_listener(self._theme_cb)
        super().destroy()


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
            img = PILImage.open(path)
            if size:
                img = img.resize(size, PILImage.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            return photo, True
        except Exception:
            return None, False

    if size:
        return None, False
    try:
        photo = tk.PhotoImage(file=path)
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

    label = tk.Label(parent, image=photo, borderwidth=0, highlightthickness=0)
    label.image = photo
    return label, True


class ImageBackgroundMixin:
    """为窗口添加自定义 PNG 背景。"""

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


# ==================== Windows 气泡通知 ====================

_NOTIFY_DATA: Optional[dict] = None


def notify_windows(title: str, message: str, icon_type: int = 1):
    """使用 Windows 原生通知区域显示气泡提醒。

    Args:
        title: 通知标题
        message: 通知内容
        icon_type: 0=无图标, 1=信息, 2=警告, 3=错误
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        NIM_ADD = 0
        NIM_MODIFY = 1
        NIF_MESSAGE = 1
        NIF_ICON = 2
        NIF_INFO = 0x10
        WM_USER = 0x400

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HANDLE),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HANDLE),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", ctypes.c_byte * 16),
                ("hBalloonIcon", wintypes.HANDLE),
            ]

        global _NOTIFY_DATA
        shell32 = ctypes.windll.shell32

        # 创建隐藏窗口作为通知消息的接收者
        if _NOTIFY_DATA is None:
            hwnd = ctypes.windll.user32.CreateWindowExW(
                0, b"STATIC", b"TableToolsNotify",
                0, 0, 0, 0, 0,
                0, 0, 0, 0
            )
            _NOTIFY_DATA = {"hwnd": hwnd, "uid": 1, "added": False}
        else:
            hwnd = _NOTIFY_DATA["hwnd"]

        uid = 1
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = uid
        nid.uFlags = NIF_INFO | NIF_ICON | NIF_MESSAGE
        nid.dwInfoFlags = icon_type
        nid.hIcon = 0
        nid.szInfo = message[:255]
        nid.szInfoTitle = title[:63]
        nid.uCallbackMessage = WM_USER + 1

        if not _NOTIFY_DATA["added"]:
            shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
            _NOTIFY_DATA["added"] = True
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
    except Exception:
        pass


def notify(title: str, message: str, error: bool = False):
    """便捷通知函数。"""
    icon = 3 if error else 1
    notify_windows(title, message, icon)


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
