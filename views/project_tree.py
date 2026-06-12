"""项目结构生成"""

import os
import flet as ft
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, section_title,
)


IGNORE_DIRS = {
    "__pycache__", ".git", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", ".idea", ".vscode",
    "__pycache__", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "target", "bin", "obj",
}

IGNORE_FILES = {
    ".pyc", ".pyo", ".DS_Store", ".gitkeep",
}


class ProjectTreeView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        self._path_input = text_input(label="项目路径", value=os.getcwd(), width=400)
        self._depth_input = ft.Dropdown(
            label="深度",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 11)],
            value="5",
            width=100,
            border_radius=12,
        )
        self._show_files_switch = ft.Switch(value=True, label="显示文件",
                                             active_color=ft.Colors.PRIMARY)

        self._gen_btn = primary_button("🌳 生成结构", on_click=self._generate)
        self._copy_btn = secondary_button("📋 复制", on_click=self._copy)
        self._status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        self._result_output = text_input(label="项目结构", multiline=True, height=400)
        self._result_output.read_only = True

        form_card = glass_card(
            content=ft.Column([
                ft.Row([self._path_input, self._depth_input], spacing=12),
                ft.Row([self._show_files_switch, self._gen_btn, self._copy_btn, self._status],
                       spacing=12),
            ], spacing=12),
            padding=20,
        )

        result_card = glass_card(
            content=self._result_output,
            padding=16,
        )

        c = ft.Column([
            section_title("项目结构生成"),
            ft.Container(height=4),
            form_card,
            result_card,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(c)

    def _generate(self, e=None):
        root = self._path_input.value.strip()
        if not root or not os.path.isdir(root):
            self._status.value = "路径无效"
            self._status.color = ft.Colors.ERROR
            self._status.update()
            return

        try:
            max_depth = int(self._depth_input.value or "5")
        except ValueError:
            max_depth = 5

        show_files = self._show_files_switch.value
        self._status.value = "生成中..."
        self._status.update()

        lines = [f"📁 {os.path.basename(root) or root}/"]
        self._walk(root, "", lines, max_depth, show_files)

        result = "\n".join(lines)
        self._result_output.value = result
        self._result_output.read_only = False
        self._result_output.update()
        self._result_output.read_only = True
        self._status.value = f"完成 ✓ ({len(lines)} 行)"
        self._status.color = ft.Colors.TERTIARY
        self._status.update()

    def _walk(self, path, prefix, lines, max_depth, show_files, depth=0):
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{prefix}  └── ⚠ 无权限访问")
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))
                and e not in IGNORE_DIRS]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))
                 and not any(e.endswith(ext) for ext in IGNORE_FILES)]

        all_items = dirs + (files if show_files else [])
        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            connector = "└── " if is_last else "├── "
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path) and item not in IGNORE_DIRS:
                lines.append(f"{prefix}{connector}📁 {item}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                self._walk(full_path, next_prefix, lines, max_depth, show_files, depth + 1)
            elif show_files and os.path.isfile(full_path):
                lines.append(f"{prefix}{connector}📄 {item}")

    def _copy(self, e=None):
        if self._result_output.value:
            try:
                import pyperclip
                pyperclip.copy(self._result_output.value)
                self._status.value = "已复制 ✓"
                self._status.color = ft.Colors.TERTIARY
            except ImportError:
                self._status.value = "需要 pyperclip"
                self._status.color = ft.Colors.ERROR
            self._status.update()
