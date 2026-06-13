"""项目结构生成"""

import os
import re
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

        self._gen_btn = primary_button("生成结构", on_click=self._generate)
        self._copy_btn = secondary_button("复制", on_click=self._copy)
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

        # ---------- 从树结构创建文件 ----------
        self._tree_input = text_input(
            label="粘贴树结构文本（如 tree 命令输出）", multiline=True, height=200,
        )
        self._target_path = text_input(label="目标目录", value=os.getcwd(), width=400)
        self._create_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        create_card = glass_card(
            content=ft.Column([
                ft.Text("从树结构创建文件", size=16, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE),
                ft.Container(height=4),
                self._tree_input,
                ft.Row([
                    self._target_path,
                    secondary_button("浏览...", on_click=self._browse_target),
                    primary_button("创建结构", on_click=self._create_from_tree),
                    self._create_status,
                ], spacing=12, wrap=True),
            ], spacing=8),
            padding=16,
        )

        c = ft.Column([
            section_title("项目结构生成"),
            ft.Container(height=4),
            form_card,
            result_card,
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            create_card,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(c, page=self.page)

    def _browse_target(self, e=None):
        """选择目标目录。"""
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title="选择目标目录")
        root.destroy()
        if path:
            self._target_path.value = path
            self._target_path.update()

    def _create_from_tree(self, e=None):
        """解析树结构文本并在目标目录下创建文件。"""
        text = self._tree_input.value
        if not text or not text.strip():
            self._create_status.value = "请先粘贴树结构文本"
            self._create_status.color = ft.Colors.ERROR
            self._create_status.update()
            return

        target = self._target_path.value.strip()
        if not target:
            self._create_status.value = "请选择目标目录"
            self._create_status.color = ft.Colors.ERROR
            self._create_status.update()
            return

        if not os.path.isdir(target):
            self._create_status.value = "目标目录不存在"
            self._create_status.color = ft.Colors.ERROR
            self._create_status.update()
            return

        try:
            entries = self._parse_tree_text(text)
            if not entries:
                self._create_status.value = "无法解析树结构"
                self._create_status.color = ft.Colors.ERROR
                self._create_status.update()
                return

            created_dirs = 0
            created_files = 0
            for rel_path, is_dir in entries:
                full_path = os.path.join(target, rel_path)
                if is_dir:
                    os.makedirs(full_path, exist_ok=True)
                    created_dirs += 1
                else:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        pass  # 创建空文件
                    created_files += 1

            self._create_status.value = f"创建完成: {created_dirs} 个目录, {created_files} 个文件"
            self._create_status.color = ft.Colors.TERTIARY
        except Exception as ex:
            self._create_status.value = f"创建失败: {ex}"
            self._create_status.color = ft.Colors.ERROR
        self._create_status.update()

    @staticmethod
    def _parse_tree_text(text):
        """解析 tree 命令输出的树结构文本，返回 (相对路径, 是否为目录) 列表。"""
        lines = text.strip().split("\n")
        if not lines:
            return []

        # 第一行是根目录名
        root_name = lines[0].strip().rstrip("/")
        result = []

        # 栈: [(depth, relative_path)]
        stack = [(0, root_name)]

        for line in lines[1:]:
            if not line.strip():
                continue

            # 找连接符位置确定深度
            connector_pos = -1
            for ch in ("├", "└"):
                pos = line.find(ch)
                if pos >= 0:
                    connector_pos = pos
                    break

            if connector_pos < 0:
                continue

            depth = connector_pos // 4 + 1  # tree 每级缩进 4 字符, +1 跳过根

            # 清除树连接字符
            clean = re.sub(r"[├└│─]", "", line).strip()
            if not clean:
                continue

            is_dir = clean.endswith("/")
            name = clean.rstrip("/")

            # 弹出同级或更深层级的栈元素
            while stack and stack[-1][0] >= depth:
                stack.pop()

            # 父级路径
            parent = stack[-1][1] if stack else ""
            rel_path = os.path.join(parent, name).replace("\\", "/")
            result.append((rel_path, is_dir))

            if is_dir:
                stack.append((depth, rel_path))

        return result

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

        lines = [f"{os.path.basename(root) or root}/"]
        self._walk(root, "", lines, max_depth, show_files)

        result = "\n".join(lines)
        self._result_output.value = result
        self._result_output.read_only = False
        self._result_output.update()
        self._result_output.read_only = True
        self._status.value = f"完成 ({len(lines)} 行)"
        self._status.color = ft.Colors.TERTIARY
        self._status.update()

    def _walk(self, path, prefix, lines, max_depth, show_files, depth=0):
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{prefix}  └── 无权限访问")
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
                lines.append(f"{prefix}{connector}{item}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                self._walk(full_path, next_prefix, lines, max_depth, show_files, depth + 1)
            elif show_files and os.path.isfile(full_path):
                lines.append(f"{prefix}{connector}{item}")

    def _copy(self, e=None):
        if self._result_output.value:
            try:
                import pyperclip
                pyperclip.copy(self._result_output.value)
                self._status.value = "已复制"
                self._status.color = ft.Colors.TERTIARY
            except ImportError:
                self._status.value = "需要 pyperclip"
                self._status.color = ft.Colors.ERROR
            self._status.update()
