"""设置页面 — 窗口模式配置"""

import flet as ft
from config import MODULE_KEYS, MODULE_NAMES, MODULE_ICONS, get_window_mode, set_window_mode
from views.common import page_wrapper, glass_card, section_title


class SettingsView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        mode_rows = []
        for key in MODULE_KEYS:
            icon = MODULE_ICONS.get(key, "?")
            name = MODULE_NAMES.get(key, key)
            current = get_window_mode(key)

            def make_on_change(k, rb_new, rb_replace):
                def on_change(e):
                    val = "new" if rb_new.value else "replace"
                    set_window_mode(k, val)
                    rb_new.update()
                    rb_replace.update()
                return on_change

            rb_new = ft.Radio(value="new", label="新窗口")
            rb_replace = ft.Radio(value="replace", label="替换启动器")
            rb_group = ft.RadioGroup(
                content=ft.Row([rb_new, rb_replace], spacing=12),
                value=current,
                on_change=lambda e, k=key: set_window_mode(k, e.control.value),
            )

            row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{icon} {name}", size=15, weight=ft.FontWeight.W_500,
                            color=ft.Colors.ON_SURFACE, width=200),
                    rb_group,
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.Padding(8, 4, 8, 4),
                border=ft.Border(bottom=ft.BorderSide(0.5, ft.Colors.OUTLINE)),
            )
            mode_rows.append(row)

        content = ft.Column([
            section_title("设置"),
            ft.Container(height=8),
            ft.Text("配置各模块的启动方式", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=12),
            glass_card(
                content=ft.Column([
                    ft.Text("窗口模式", size=16, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE),
                    ft.Container(height=4),
                    ft.Text("每个模块可设为「新窗口」或「替换启动器」（隐藏启动器，模块关闭后恢复）",
                            size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Divider(height=16, color=ft.Colors.OUTLINE),
                    ft.Column(mode_rows, spacing=2),
                ], spacing=4),
                padding=20,
            ),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content, page=self.page)
