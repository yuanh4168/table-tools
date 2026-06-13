"""提示词生成"""

import flet as ft
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, dropdown, section_title,
)


class PromptView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        self._type_dd = dropdown(
            label="类型",
            options=["代码审查", "需求分析", "架构设计", "测试用例", "文档编写", "自定义"],
            value="代码审查",
            width=200,
        )
        self._lang_dd = dropdown(
            label="语言",
            options=["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "其他"],
            value="Python",
            width=160,
        )
        self._topic_input = text_input(label="主题/需求描述", multiline=True, height=120)
        self._extra_input = text_input(label="额外要求（可选）", multiline=True, height=80)

        self._gen_btn = primary_button("生成提示词", on_click=self._generate)
        self._copy_btn = secondary_button("复制", on_click=self._copy)
        self._status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        self._result_output = text_input(label="生成的提示词", multiline=True, height=250)
        self._result_output.read_only = True

        form_card = glass_card(
            content=ft.Column([
                ft.Row([self._type_dd, self._lang_dd], spacing=12),
                self._topic_input,
                self._extra_input,
                ft.Row([self._gen_btn, self._copy_btn, self._status], spacing=12),
            ], spacing=12),
            padding=20,
        )

        result_card = glass_card(
            content=self._result_output,
            padding=16,
        )

        c = ft.Column([
            section_title("提示词生成"),
            ft.Container(height=4),
            form_card,
            result_card,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(c, page=self.page)

    def _generate(self, e=None):
        ptype = self._type_dd.value or "通用"
        lang = self._lang_dd.value or ""
        topic = self._topic_input.value or ""
        extra = self._extra_input.value or ""

        if ptype == "自定义" and not topic:
            self._status.value = "请输入主题描述"
            self._status.color = ft.Colors.ERROR
            self._status.update()
            return

        prompt = f"""你是一个{ptype}专家。

## 任务
{'请根据以下需求提供详细方案。' if not topic else topic}

## 上下文
- 类型：{ptype}
{f'- 编程语言：{lang}' if lang else ''}
{f'- 额外要求：{extra}' if extra else ''}

## 输出要求
1. 清晰的结构和逻辑
2. 具体的步骤或方案
3. 可执行的建议
4. 潜在风险和注意事项
{'- 包含代码示例' if ptype in ('代码审查', '测试用例') else ''}
"""

        self._result_output.value = prompt
        self._result_output.read_only = False
        self._result_output.update()
        self._result_output.read_only = True
        self._status.value = "提示词已生成"
        self._status.color = ft.Colors.TERTIARY
        self._status.update()

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
