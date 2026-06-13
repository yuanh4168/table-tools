"""翻译助手"""

import flet as ft
from modules import translate as mod_translate
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, section_title,
)


class TranslateView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate

    def build(self):
        self._src_input = text_input(label="原文", multiline=True, height=160)
        self._dst_output = text_input(label="译文", multiline=True, height=160)
        self._dst_output.read_only = True

        self._engine_dd = ft.Dropdown(
            label="引擎",
            options=[ft.dropdown.Option("mymemory", "MyMemory")],
            value="mymemory",
            width=160,
            border_radius=12,
        )

        self._translate_btn = primary_button("翻译", on_click=self._do_translate)
        self._paste_btn = secondary_button("从剪贴板读取", on_click=self._paste)
        self._copy_btn = secondary_button("复制译文", on_click=self._copy_result)
        self._clear_btn = secondary_button("清空", on_click=self._clear)
        self._status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        form = glass_card(
            content=ft.Column([
                self._src_input,
                ft.Row([self._engine_dd, self._paste_btn, self._translate_btn],
                       spacing=12, alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=8, color=ft.Colors.OUTLINE),
                self._dst_output,
                ft.Row([self._copy_btn, self._clear_btn, self._status],
                       spacing=12, alignment=ft.MainAxisAlignment.START),
            ], spacing=12),
            padding=20,
        )

        content = ft.Column([
            section_title("翻译助手"),
            ft.Container(height=4),
            form,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content, page=self.page)

    def _do_translate(self, e=None):
        text = self._src_input.value
        if not text or not text.strip():
            self._status.value = "请输入要翻译的文本"
            self._status.color = ft.Colors.ERROR
            self._status.update()
            return

        self._dst_output.value = "翻译中..."
        self._dst_output.read_only = False
        self._dst_output.update()
        self._translate_btn.disabled = True
        self._translate_btn.update()
        self._status.value = "翻译中..."
        self._status.color = ft.Colors.PRIMARY
        self._status.update()

        def worker():
            result = mod_translate.translate_mymemory(text.strip())
            self._dst_output.value = result
            self._dst_output.read_only = True
            self._status.value = "翻译完成" if not result.startswith("[错误]") else "翻译失败"
            self._status.color = ft.Colors.TERTIARY if not result.startswith("[错误]") else ft.Colors.ERROR
            self._translate_btn.disabled = False
            self.page.update()

        self.page.run_thread(worker)

    def _show_result(self, result):
        self._dst_output.value = result
        self._dst_output.read_only = True
        self._dst_output.update()
        self._translate_btn.disabled = False
        self._translate_btn.update()
        if result.startswith("[错误]"):
            self._status.value = "翻译失败"
            self._status.color = ft.Colors.ERROR
        else:
            self._status.value = "翻译完成"
            self._status.color = ft.Colors.TERTIARY
        self._status.update()
        return ft.Container()

    def _paste(self, e=None):
        try:
            import pyperclip
            text = pyperclip.paste().strip()
            if text:
                self._src_input.value = text
                self._src_input.update()
        except ImportError:
            self._status.value = "需要 pyperclip: pip install pyperclip"
            self._status.color = ft.Colors.ERROR
            self._status.update()

    def _copy_result(self, e=None):
        if self._dst_output.value and not self._dst_output.value.startswith("翻译中"):
            try:
                import pyperclip
                pyperclip.copy(self._dst_output.value)
                self._status.value = "已复制"
                self._status.color = ft.Colors.TERTIARY
                self._status.update()
            except ImportError:
                self._status.value = "需要 pyperclip"
                self._status.color = ft.Colors.ERROR
                self._status.update()

    def _clear(self, e=None):
        self._src_input.value = ""
        self._dst_output.value = ""
        self._status.value = ""
        self._src_input.update()
        self._dst_output.update()
        self._status.update()
