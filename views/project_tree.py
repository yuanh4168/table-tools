"""项目结构生成 — 完全独立的实现，避免依赖导致的渲染问题"""

import os
import re
import flet as ft

IGNORE_DIRS = {
    "__pycache__", ".git", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", ".idea", ".vscode",
    "__pycache__", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "target", "bin", "obj",
}
IGNORE_FILES = {".pyc", ".pyo", ".DS_Store", ".gitkeep"}


class ProjectTreeView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        # 创建所有控件（显式设置背景色为白色，确保可见）
        self.gen_path = ft.TextField(
            label="项目路径", value=os.getcwd(), width=500,
            bgcolor="#FFFFFF", border_radius=8
        )
        self.gen_depth = ft.Dropdown(
            label="深度", options=[ft.dropdown.Option(str(i)) for i in range(1, 11)],
            value="5", width=100, bgcolor="#FFFFFF", border_radius=8
        )
        self.gen_show_files = ft.Switch(value=True, label="显示文件", active_color="#2C83FD")
        self.gen_btn = ft.ElevatedButton("生成结构", on_click=self._generate_tree,
                                         bgcolor="#2C83FD", color="white")
        self.gen_copy_btn = ft.OutlinedButton("复制", on_click=self._copy_tree,
                                              style=ft.ButtonStyle(color="#333"))
        self.gen_status = ft.Text("", size=12, color="#666666")
        self.gen_output = ft.TextField(
            multiline=True, min_lines=8, max_lines=15, read_only=True,
            label="生成的树结构", bgcolor="#FFFFFF", border_radius=8
        )

        card1 = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("生成项目结构树", size=16, weight="bold"),
                    ft.Row([self.gen_path, self.gen_depth], spacing=12, wrap=True),
                    ft.Row([self.gen_show_files, self.gen_btn, self.gen_copy_btn, self.gen_status],
                           spacing=12, wrap=True),
                    self.gen_output,
                ], spacing=12),
                padding=16, bgcolor="#FFFFFF"
            ),
            elevation=2,
        )

        # 第二个卡片
        self.tree_input = ft.TextField(
            label="粘贴树结构文本（如 tree /f 输出）", multiline=True,
            min_lines=6, max_lines=10, bgcolor="#FFFFFF", border_radius=8
        )
        self.create_target = ft.TextField(
            label="目标目录", value=os.getcwd(), width=400,
            bgcolor="#FFFFFF", border_radius=8
        )
        self.browse_btn = ft.OutlinedButton("浏览...", on_click=self._browse_target,
                                            style=ft.ButtonStyle(color="#333"))
        self.create_btn = ft.ElevatedButton("创建结构", on_click=self._create_from_tree,
                                            bgcolor="#2C83FD", color="white")
        self.create_status = ft.Text("", size=12, color="#666666")

        card2 = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("从树结构创建文件", size=16, weight="bold"),
                    self.tree_input,
                    ft.Row([self.create_target, self.browse_btn, self.create_btn, self.create_status],
                           spacing=12, wrap=True),
                ], spacing=12),
                padding=16, bgcolor="#FFFFFF"
            ),
            elevation=2,
        )

        # 主容器背景为浅灰色，与白色卡片区分
        main_content = ft.Container(
            content=ft.Column([
                ft.Text("项目结构生成", size=24, weight="bold", color="#111"),
                ft.Container(height=8),
                card1,
                ft.Container(height=12),
                card2,
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=24,
            bgcolor="#F5F7FA",  # 浅灰背景
        )
        return main_content

    # ---------- 生成树结构 ----------
    def _generate_tree(self, e):
        root = self.gen_path.value.strip()
        if not root or not os.path.isdir(root):
            self.gen_status.value = "路径无效"
            self.gen_status.color = "#E34D4F"
            self.gen_status.update()
            return

        try:
            max_depth = int(self.gen_depth.value)
        except ValueError:
            max_depth = 5
        show_files = self.gen_show_files.value

        self.gen_status.value = "生成中..."
        self.gen_status.update()

        lines = [f"{os.path.basename(root) or root}/"]
        self._walk(root, "", lines, max_depth, show_files)
        result = "\n".join(lines)

        self.gen_output.value = result
        self.gen_output.update()
        self.gen_status.value = f"完成 ({len(lines)} 行)"
        self.gen_status.color = "#61C758"
        self.gen_status.update()

    def _walk(self, path, prefix, lines, max_depth, show_files, depth=0):
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{prefix}  └── 无权限访问")
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in IGNORE_DIRS]
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

    def _copy_tree(self, e):
        if self.gen_output.value:
            try:
                import pyperclip
                pyperclip.copy(self.gen_output.value)
                self.gen_status.value = "已复制"
                self.gen_status.color = "#61C758"
            except ImportError:
                self.gen_status.value = "需要 pyperclip"
                self.gen_status.color = "#E34D4F"
            self.gen_status.update()

    # ---------- 从树文本创建文件 ----------
    def _browse_target(self, e):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title="选择目标目录")
        root.destroy()
        if path:
            self.create_target.value = path
            self.create_target.update()

    def _create_from_tree(self, e):
        text = self.tree_input.value
        if not text or not text.strip():
            self.create_status.value = "请先粘贴树结构文本"
            self.create_status.color = "#E34D4F"
            self.create_status.update()
            return

        target = self.create_target.value.strip()
        if not target:
            self.create_status.value = "请选择目标目录"
            self.create_status.color = "#E34D4F"
            self.create_status.update()
            return

        if not os.path.isdir(target):
            self.create_status.value = "目标目录不存在"
            self.create_status.color = "#E34D4F"
            self.create_status.update()
            return

        try:
            entries = self._parse_tree_text(text)
            if not entries:
                self.create_status.value = "无法解析树结构"
                self.create_status.color = "#E34D4F"
                self.create_status.update()
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
                        f.write("")
                    created_files += 1

            self.create_status.value = f"创建完成: {created_dirs} 个目录, {created_files} 个文件"
            self.create_status.color = "#61C758"
        except Exception as ex:
            self.create_status.value = f"创建失败: {ex}"
            self.create_status.color = "#E34D4F"
        self.create_status.update()

    @staticmethod
    def _parse_tree_text(text):
        lines = text.strip().split("\n")
        if not lines:
            return []

        root_name = lines[0].strip().rstrip("/")
        result = []
        stack = [(0, root_name)]

        for line in lines[1:]:
            if not line.strip():
                continue
            pos = -1
            for ch in ("├", "└"):
                p = line.find(ch)
                if p >= 0:
                    pos = p
                    break
            if pos < 0:
                continue

            depth = pos // 4 + 1
            clean = re.sub(r"[├└│─]", "", line).strip()
            if not clean:
                continue
            is_dir = clean.endswith("/")
            name = clean.rstrip("/")

            while stack and stack[-1][0] >= depth:
                stack.pop()
            parent = stack[-1][1] if stack else ""
            rel_path = os.path.join(parent, name).replace("\\", "/")
            result.append((rel_path, is_dir))
            if is_dir:
                stack.append((depth, rel_path))
        return result