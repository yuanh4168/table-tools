"""共享UI组件 — 圆角卡片、按钮、输入框等统一风格组件"""

import flet as ft

# Flet 0.85 兼容颜色
_C_SURFACE = ft.Colors.SURFACE
_C_ON_SURFACE = ft.Colors.ON_SURFACE
_C_ON_SURFACE_VARIANT = ft.Colors.ON_SURFACE_VARIANT
_C_PRIMARY = ft.Colors.PRIMARY
_C_ERROR = ft.Colors.ERROR
_C_TERTIARY = ft.Colors.TERTIARY
_C_OUTLINE = ft.Colors.OUTLINE
_C_SHADOW = ft.Colors.SHADOW
_C_WHITE = ft.Colors.WHITE


def glass_card(content, title="", padding=None, expand=False, width=None, height=None):
    """毛玻璃卡片 — 圆角12px + 阴影blur=15 + spread=1。"""
    pad = padding or ft.Padding(16, 16, 16, 16)
    children = []
    if title:
        children.append(ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=_C_ON_SURFACE))
    children.append(content if isinstance(content, ft.Control) else ft.Container())
    return ft.Container(
        content=ft.Column(children, tight=True, spacing=8),
        bgcolor=ft.Colors.with_opacity(0.9, _C_SURFACE),
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color=_C_SHADOW),
        padding=pad,
        expand=expand,
        width=width,
        height=height,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )


def primary_button(text, on_click=None, icon=None, disabled=False, expand=False):
    """主按钮 — 蓝色填充 #2C83FD，圆角12px。"""
    content = ft.Text(text)
    return ft.FilledButton(
        content=content, on_click=on_click,
        disabled=disabled, expand=expand,
        style=ft.ButtonStyle(
            color=_C_WHITE, bgcolor=_C_PRIMARY,
            overlay_color=ft.Colors.with_opacity(0.2, "#FFFFFF"),
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(20, 12, 20, 12),
            animation_duration=200,
        ),
    )


def secondary_button(text, on_click=None, icon=None, disabled=False):
    """次要按钮 — 描边，圆角12px。"""
    content = ft.Text(text)
    return ft.OutlinedButton(
        content=content, on_click=on_click, disabled=disabled,
        style=ft.ButtonStyle(
            color=_C_ON_SURFACE_VARIANT,
            shape=ft.RoundedRectangleBorder(radius=12),
            side=ft.BorderSide(1, _C_OUTLINE),
            padding=ft.Padding(16, 10, 16, 10),
            animation_duration=200,
        ),
    )


def text_input(label="", value="", multiline=False, height=120, width=None,
               on_change=None, password=False, read_only=False):
    """统一风格输入框 — 圆角12px。"""
    return ft.TextField(
        label=label, value=value,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        max_lines=10 if multiline else 1,
        height=height if multiline else None,
        width=width,
        password=password, can_reveal_password=password,
        read_only=read_only, on_change=on_change,
        border_radius=12,
        border_color=_C_OUTLINE, focused_border_color=_C_PRIMARY,
        text_size=14,
    )


def dropdown(label="", options=None, value=None, on_select=None, width=200):
    """统一下拉框 — 圆角12px。"""
    opts = [ft.dropdown.Option(o) for o in (options or [])]
    return ft.Dropdown(
        label=label, options=opts, value=value, on_select=on_select,
        width=width, border_radius=12,
        border_color=_C_OUTLINE, focused_border_color=_C_PRIMARY,
        text_size=14,
    )


def section_title(text):
    return ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=_C_ON_SURFACE)


def page_wrapper(content, scroll=True):
    """页面外层包装 — 渐变背景。"""
    items = content if isinstance(content, list) else [content]
    return ft.Container(
        content=ft.Column(items, scroll=ft.ScrollMode.AUTO if scroll else ft.ScrollMode.DISABLED, spacing=16),
        padding=ft.Padding(24, 24, 24, 24), expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            colors=["#F5F7FA", "#E4E8F0"],
        ),
        border_radius=ft.BorderRadius(12, 0, 0, 0),
    )


def info_row(label, value):
    return ft.Row([
        ft.Text(label, size=13, color=_C_ON_SURFACE_VARIANT, width=80),
        ft.Text(value, size=14, weight=ft.FontWeight.W_500, color=_C_ON_SURFACE),
    ], spacing=8)
