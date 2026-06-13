"""设置页面 — 直接编辑 config.ini 配置文件"""

import flet as ft
import os
from config import CONFIG_PATH
from views.common import page_wrapper, glass_card, primary_button, secondary_button, section_title


class SettingsView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._config_content = ""

    def build(self):
        # 读取当前配置文件内容
        self._load_config_content()

        # 多行文本框显示和编辑配置文件
        self._editor = ft.TextField(
            value=self._config_content,
            multiline=True,
            min_lines=20,
            max_lines=40,
            expand=True,
            label="config.ini 配置文件（直接编辑）",
        )

        # 按钮：保存、刷新
        save_btn = primary_button("保存", on_click=self._save_config)
        refresh_btn = secondary_button("刷新", on_click=self._refresh_config)

        # 状态提示
        self._status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        # 卡片布局
        content = ft.Column([
            section_title("设置"),
            ft.Container(height=4),
            glass_card(
                content=ft.Column([
                    ft.Row([save_btn, refresh_btn], spacing=12),
                    ft.Container(height=8),
                    self._editor,
                    self._status,
                ], spacing=8),
                padding=20,
                expand=True,
            ),
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

        return page_wrapper(content, page=self.page)

    def _load_config_content(self):
        """从磁盘读取 config.ini 内容"""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self._config_content = f.read()
        except FileNotFoundError:
            self._config_content = "; 配置文件不存在，将创建默认配置\n"
        except Exception as e:
            self._config_content = f"; 读取配置失败: {e}\n"

    def _refresh_config(self, e=None):
        """刷新编辑器内容（放弃修改）"""
        self._load_config_content()
        self._editor.value = self._config_content
        self._status.value = "已刷新，未保存的修改已丢失"
        self._status.color = ft.Colors.ON_SURFACE_VARIANT
        self._status.update()
        self._editor.update()

    def _save_config(self, e=None):
        """将编辑器内容保存到 config.ini"""
        new_content = self._editor.value
        try:
            # 写入文件
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
            # 更新内存中的配置缓存（可选，需要重新加载）
            self._status.value = "✓ 配置已保存，部分模块可能需要重启后生效"
            self._status.color = ft.Colors.TERTIARY
            self._status.update()
        except Exception as ex:
            self._status.value = f"保存失败: {ex}"
            self._status.color = ft.Colors.ERROR
            self._status.update()