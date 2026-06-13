"""UI 通用组件 — 全新主题系统（支持打包后 exe 同目录）"""

import math
import os
import sys
import configparser
import tkinter as tk
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ---------- 资源路径函数（打包后 exe 同目录）----------
def resource_path(relative_path: str) -> str:
    """返回资源文件的绝对路径，支持打包后的 exe 同目录查找"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境：exe 所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：当前文件所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 对于 ui_common.py，需要向上两级才能到项目根目录，但配置文件在根目录，所以特殊处理
        # 更简单：统一从 exe 目录或当前工作目录查找
        base_dir = os.path.dirname(BASE_DIR)  # 回到项目根目录
    return os.path.join(base_dir, relative_path)


def ensure_config():
    """确保 config.ini 存在（与 config.py 中的逻辑一致）"""
    cfg_path = resource_path("config.ini")
    if not os.path.exists(cfg_path):
        template = """[AI]
api_url = https://integrate.api.nvidia.com/v1/chat/completions
api_key = 
model = meta/llama-3.1-70b-instruct

[chat]
api_url = 
api_key = 
model = 
window_mode = new

[news]
window_mode = new
source = 原版

[translate]
engine = mymemory
window_mode = new

[stone]
width = 60
height = 30
count = 120

[document]
org = 厦门市教育局
type = 通知
window_mode = new

[mc-ping]
host = fm.rainplay.cn
port = 25065
notify_threshold = 5
window_mode = new

[chess]
ai = false
window_mode = new

[prompt]
template = 
window_mode = new

[project-tree]
output = .
window_mode = new

[mc_ping]
window_mode = new
"""
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(template)


_CONFIG_CACHE: configparser.ConfigParser | None = None


def get_config() -> configparser.ConfigParser:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    _CONFIG_CACHE = configparser.ConfigParser()
    ensure_config()  # 确保配置文件存在
    cfg_path = resource_path("config.ini")
    _CONFIG_CACHE.read(cfg_path, encoding="utf-8")
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


# 其余代码（主题、控件等）保持不变 ...
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
