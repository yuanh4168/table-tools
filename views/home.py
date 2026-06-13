"""首页 — 模块卡片网格（等高卡片）"""

import flet as ft
from config import MODULE_KEYS, MODULE_NAMES, MODULE_ICONS, MODULE_DESC
from views.common import page_wrapper


class HomeView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        cards = []
        for key in MODULE_KEYS:
            name = MODULE_NAMES.get(key, key)
            desc = MODULE_DESC.get(key, "")
            icon_const = getattr(ft.icons, MODULE_ICONS.get(key, ""), None)
            icon_widget = ft.Icon(icon_const, size=40) if icon_const else ft.Text(name[0], size=32)

            card = ft.Container(
                col={"sm": 12, "md": 6, "lg": 4},  # 响应式列
                height=240,  # 固定高度，保证所有卡片等高
                content=ft.Column([
                    ft.Container(
                        content=icon_widget,
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(0, 8, 0, 4),
                        expand=True,  # 垂直方向占满
                    ),
                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                    ft.Text(desc, size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER, no_wrap=False,
                            max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True),  # Column 占满 Container 高度
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE),
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color=ft.Colors.SHADOW),
                padding=ft.Padding(16, 16, 16, 16),
                ink=True,
                on_click=lambda _, k=key: self._navigate(k),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            )
            cards.append(card)

        header = ft.Column([
            ft.Text("选择功能模块", size=26, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ON_SURFACE),
            ft.Text("点击卡片启动对应工具", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
        ], spacing=4)

        return page_wrapper([header, ft.ResponsiveRow(cards, spacing=12, run_spacing=12)], page=self.page)

    def _navigate(self, key):
        nav = getattr(self.page, "_navigate_fn", None) or self.navigate
        if nav:
            nav(key)