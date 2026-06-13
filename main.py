"""table-tools Flet 桌面工具集 — 自绘标题栏（完整异步修复）"""

import flet as ft
import flet.controls.material.icons as _icons_mod

# 兼容旧版图标常量
for _key in dir(_icons_mod.Icons):
    if not _key.startswith("_"):
        setattr(_icons_mod, _key, getattr(_icons_mod.Icons, _key))

from config import MODULE_KEYS, MODULE_NAMES, MODULE_ICONS

# ---------- 主题 ----------
_BORDERLESS_BTN = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=12),
    side=None,
    animation_duration=200,
)
_BORDERLESS_TEXT_BTN = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=8),
    side=None,
    animation_duration=200,
)

THEME_LIGHT = ft.Theme(
    font_family="Microsoft YaHei",
    color_scheme=ft.ColorScheme(
        primary="#2C83FD",
        on_primary=ft.Colors.WHITE,
        primary_container="#E8F0FE",
        on_primary_container="#1A4B8C",
        secondary="#303133",
        on_secondary=ft.Colors.WHITE,
        surface=ft.Colors.WHITE,
        on_surface="#18181A",
        surface_container="#F5F7FA",
        on_surface_variant="#303133",
        error="#E34D4F",
        on_error=ft.Colors.WHITE,
        outline="#E4E7ED",
        shadow="#00000019",
        tertiary="#61C758",
        on_tertiary=ft.Colors.WHITE,
        inverse_surface="#121212",
        on_inverse_surface="#EDEDED",
    ),
    use_material3=True,
    button_theme=_BORDERLESS_BTN,
    filled_button_theme=ft.FilledButtonTheme(style=_BORDERLESS_BTN),
    outlined_button_theme=ft.OutlinedButtonTheme(style=_BORDERLESS_BTN),
    text_button_theme=ft.TextButtonTheme(style=_BORDERLESS_TEXT_BTN),
)

THEME_DARK = ft.Theme(
    font_family="Microsoft YaHei",
    color_scheme=ft.ColorScheme(
        primary="#4D9EFF",
        on_primary=ft.Colors.WHITE,
        primary_container="#1A3A6B",
        on_primary_container="#B8D4FF",
        secondary="#B0B0B0",
        on_secondary=ft.Colors.BLACK,
        surface="#1E1E1E",
        on_surface="#EDEDED",
        surface_container="#121212",
        on_surface_variant="#B0B0B0",
        error="#E34D4F",
        on_error=ft.Colors.WHITE,
        outline="#333333",
        shadow="#00000040",
        tertiary="#61C758",
        on_tertiary=ft.Colors.WHITE,
        inverse_surface="#F5F7FA",
        on_inverse_surface="#18181A",
    ),
    use_material3=True,
    button_theme=_BORDERLESS_BTN,
    filled_button_theme=ft.FilledButtonTheme(style=_BORDERLESS_BTN),
    outlined_button_theme=ft.OutlinedButtonTheme(style=_BORDERLESS_BTN),
    text_button_theme=ft.TextButtonTheme(style=_BORDERLESS_TEXT_BTN),
)

# ---------- 全局状态 ----------
_page_history = ["home"]


def build_rail(page, navigate):
    """构建 NavigationRail 侧边栏。"""
    destinations = [ft.NavigationRailDestination(
        icon=ft.icons.HOME_ROUNDED, selected_icon=ft.icons.HOME_ROUNDED, label="首页",
    )]
    for key in MODULE_KEYS:
        _ic = getattr(ft.icons, MODULE_ICONS.get(key, ""), None)
        if _ic:
            destinations.append(ft.NavigationRailDestination(
                icon=_ic, selected_icon=_ic, label=MODULE_NAMES.get(key, key),
            ))
        else:
            destinations.append(ft.NavigationRailDestination(
                icon=ft.Text(key[0].upper(), size=18), selected_icon=ft.Text(key[0].upper(), size=18),
                label=MODULE_NAMES.get(key, key),
            ))
    destinations.append(ft.NavigationRailDestination(
        icon=ft.icons.SETTINGS_ROUNDED, selected_icon=ft.icons.SETTINGS_ROUNDED, label="设置",
    ))

    def on_rail_change(e):
        global _page_history
        idx = e.control.selected_index
        _page_history.clear()
        _page_history.append("home")
        if idx == 0:
            navigate("home")
        elif idx == len(destinations) - 1:
            navigate("settings")
        else:
            navigate(MODULE_KEYS[idx - 1])

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()
        navigate(_page_history[-1] if _page_history else "home")

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        width=260,
        bgcolor=ft.Colors.SURFACE,
        indicator_color=ft.Colors.PRIMARY_CONTAINER,
        indicator_shape=ft.RoundedRectangleBorder(radius=8),
        leading=ft.Container(
            content=ft.Column([
                ft.Text("table-tools", size=20, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY),
                ft.Text("桌面工具集", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
            ]),
            padding=ft.Padding(20, 24, 20, 8),
        ),
        trailing=ft.Container(
            content=ft.Column([
                ft.IconButton(
                    icon=ft.icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT
                    else ft.icons.LIGHT_MODE,
                    icon_size=20, tooltip="切换主题", on_click=toggle_theme,
                ),
                ft.Container(height=8),
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.EXIT_TO_APP_ROUNDED, size=16),
                        ft.Text("退出", size=12),
                    ], tight=True),
                    on_click=lambda e: page.run_task(page.window.close),  # 修复退出
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(0, 0, 0, 12),
        ),
        destinations=destinations,
        on_change=on_rail_change,
    )
    return rail


def build_page_view(page, name):
    """构建页面视图。"""
    from views.home import HomeView
    from views.settings import SettingsView
    from views.document import DocumentView
    from views.mc_ping import MCPingView
    from views.translate import TranslateView
    from views.chat import ChatView
    from views.news import NewsView
    from views.prompt import PromptView
    from views.project_tree import ProjectTreeView
    from views.chess import ChessView

    mapping = {
        "home": HomeView, "settings": SettingsView,
        "document": DocumentView, "mc_ping": MCPingView,
        "translate": TranslateView, "chat": ChatView,
        "news": NewsView, "prompt": PromptView,
        "project-tree": ProjectTreeView, "chess": ChessView,
    }
    cls = mapping.get(name)
    if cls is None:
        return _placeholder(name)

    navigate = getattr(page, "_navigate_fn", None)
    view = cls(page, navigate)
    return view.build()


def _placeholder(name):
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.CONSTRUCTION_ROUNDED, size=64, color=ft.Colors.PRIMARY),
            ft.Text(f"「{MODULE_NAMES.get(name, name)}」", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("模块正在开发中…", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0), expand=True,
    )


def main(page: ft.Page):
    # 窗口基础设置
    page.title = "table-tools 桌面工具集"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = THEME_LIGHT
    page.dark_theme = THEME_DARK
    page.padding = 0
    page.spacing = 0
    page.window.width = 1100
    page.window.height = 720
    page.window.min_width = 800
    page.window.min_height = 500
    # 彻底移除原生标题栏
    page.window.frameless = True
    page.window.title_bar_hidden = True
    page.run_task(page.window.center)

    # ---------- 自绘标题栏 ----------
    # 最大化/还原按钮（动态图标）
    maximize_btn = ft.IconButton(
        icon=ft.icons.CROP_SQUARE, icon_size=18,
        style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT)
    )

    def update_maximize_icon():
        if page.window.maximized:
            maximize_btn.icon = ft.icons.FILTER_NONE  # 还原图标
        else:
            maximize_btn.icon = ft.icons.CROP_SQUARE  # 最大化图标
        maximize_btn.update()

    def on_window_resize(e):
        update_maximize_icon()

    page.on_resize = on_window_resize

    def start_drag(e: ft.DragStartEvent):
        page.run_task(page.window.start_dragging)

    def minimize(e):
        page.window.minimized = True
        page.update()

    def toggle_maximize(e):
        page.window.maximized = not page.window.maximized
        update_maximize_icon()
        page.update()

    def close(e):
        page.run_task(page.window.close)

    maximize_btn.on_click = toggle_maximize

    # 加载图标（增大尺寸）
    try:
        icon_img = ft.Image(src="assets/icon_256.png", width=36, height=36)
    except:
        icon_img = ft.Icon(ft.icons.APP_REGISTRATION, size=36)

    title_bar = ft.GestureDetector(
        content=ft.Container(
            content=ft.Row(
                controls=[
                    icon_img,
                    ft.Text("table-tools 桌面工具集", size=16, weight=ft.FontWeight.W_500),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.icons.REMOVE, icon_size=18, on_click=minimize,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT)),
                    maximize_btn,
                    ft.IconButton(icon=ft.icons.CLOSE, icon_size=18, on_click=close,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT)),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(12, 8, 12, 8),
            bgcolor=ft.Colors.SURFACE,
        ),
        on_pan_start=start_drag,
    )

    # ---------- 内容区域 ----------
    content_area = ft.Container(expand=True, bgcolor="#F5F7FA", padding=0)

    def navigate(name):
        global _page_history
        if not _page_history or name != _page_history[-1]:
            _page_history.append(name)
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        content_area.bgcolor = "#121212" if is_dark else "#F5F7FA"
        content_area.content = build_page_view(page, name)
        content_area.update()

    page._navigate_fn = navigate

    rail = build_rail(page, navigate)

    # 主布局
    main_layout = ft.Column(
        controls=[
            title_bar,
            ft.Row(
                [rail, ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE), content_area],
                expand=True, spacing=0,
            ),
        ],
        spacing=0,
        expand=True,
    )

    page.add(main_layout)
    navigate("home")
    update_maximize_icon()  # 初始化图标状态
    page.update()


if __name__ == "__main__":
    ft.run(main)