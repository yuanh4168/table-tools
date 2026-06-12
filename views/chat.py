"""AI 对话"""

import threading
import flet as ft
from config import cfg_str
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, section_title,
)


class ChatView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._messages = [
            {"role": "system", "content": "你是一个有用的助手。用中文回答，简洁直接。"}
        ]
        self._thinking = False

    def build(self):
        default_api = cfg_str("chat", "api_url") or cfg_str("AI", "api_url",
                         "https://integrate.api.nvidia.com/v1/chat/completions")
        default_key = cfg_str("chat", "api_key") or cfg_str("AI", "api_key", "")
        default_model = cfg_str("chat", "model") or cfg_str("AI", "model",
                         "qwen/qwen3-coder-480b-a35b-instruct")

        self._api_input = text_input(label="API 地址", value=default_api)
        self._key_input = text_input(label="API Key", value=default_key, password=True, width=250)
        self._model_input = text_input(label="模型", value=default_model)
        self._msg_input = text_input(label="输入消息...", multiline=True, height=80)

        self._send_btn = primary_button("发送", on_click=self._send)
        self._clear_btn = secondary_button("清空历史", on_click=self._clear_history)

        self._chat_display = ft.ListView(
            spacing=8,
            padding=8,
            expand=True,
            height=400,
        )

        self._chat_display.controls.append(
            ft.Container(
                content=ft.Text("开始对话...", italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                padding=10,
            )
        )

        config_card = glass_card(
            content=ft.Column([
                ft.Row([self._api_input, ft.Container(width=12),
                        self._key_input], spacing=0),
                ft.Row([self._model_input], spacing=12),
            ], spacing=10),
            padding=16,
        )

        chat_card = glass_card(
            content=ft.Column([
                ft.Container(
                    content=self._chat_display,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=12,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    height=400,
                ),
                self._msg_input,
                ft.Row([self._send_btn, self._clear_btn], spacing=12),
            ], spacing=10),
            padding=16,
            expand=True,
        )

        content = ft.Column([
            section_title("AI 对话"),
            ft.Container(height=4),
            config_card,
            chat_card,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content)

    def _send(self, e=None):
        text = self._msg_input.value
        if not text or not text.strip():
            return
        if self._thinking:
            return

        self._msg_input.value = ""

        # 添加用户消息
        self._add_msg("user", text)
        self._messages.append({"role": "user", "content": text})
        self._add_msg("system", "思考中...")
        self._thinking = True
        self._send_btn.disabled = True
        self._send_btn.update()

        def worker():
            import requests
            try:
                api_url = self._api_input.value.strip()
                api_key = self._key_input.value.strip()
                model = self._model_input.value.strip()

                if not api_key:
                    self.page.add(self._handle_error("请输入 API 密钥"))
                    self.page.update()
                    return

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": self._messages,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                }
                resp = requests.post(api_url, json=payload, headers=headers, timeout=120)
                data = resp.json()
                if resp.status_code != 200:
                    err = data.get("error", {}).get("message", str(data))
                    self.page.add(self._handle_error(f"API 错误 ({resp.status_code}): {err}"))
                    self.page.update()
                    return
                content = data["choices"][0]["message"]["content"]
                self._messages.append({"role": "assistant", "content": content})
                self.page.add(self._remove_thinking())
                self.page.add(self._add_msg("assistant", content))
            except Exception as ex:
                self.page.add(self._handle_error(str(ex)))
            finally:
                self._thinking = False
                self.page.add(self._re_enable_send())
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _add_msg(self, role, content):
        colors = {"user": ft.Colors.PRIMARY, "assistant": ft.Colors.TERTIARY, "system": ft.Colors.ERROR}
        labels = {"user": "🧑 你", "assistant": "🤖 AI", "system": "⚙ 系统"}
        label = labels.get(role, role)

        if role == "system" and content == "思考中...":
            self._chat_display.controls.append(
                ft.Container(
                    content=ft.Text("思考中...", italic=True, color=ft.Colors.ERROR),
                    padding=ft.Padding(8, 0, 0, 4),
                )
            )
        else:
            self._chat_display.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(label, size=13, weight=ft.FontWeight.BOLD,
                                color=colors.get(role, ft.Colors.ON_SURFACE)),
                        ft.Container(
                            content=ft.Text(content, size=14, color=ft.Colors.ON_SURFACE),
                            bgcolor=ft.Colors.SURFACE_CONTAINER,
                            border_radius=8,
                            padding=10,
                        ),
                    ], spacing=4),
                )
            )
        self._chat_display.scroll_to(offset=-1, duration=100)
        self._chat_display.update()
        return ft.Container()

    def _remove_thinking(self):
        if self._chat_display.controls and \
           isinstance(self._chat_display.controls[-1], ft.Container):
            c = self._chat_display.controls[-1]
            if isinstance(c.content, ft.Text) and c.content.value == "思考中...":
                self._chat_display.controls.pop()
                self._chat_display.update()
        return ft.Container()

    def _handle_error(self, msg):
        self._remove_thinking()
        self._add_msg("system", f"错误: {msg}")
        return ft.Container()

    def _re_enable_send(self):
        self._send_btn.disabled = False
        self._send_btn.update()
        return ft.Container()

    def _clear_history(self, e=None):
        self._messages = [self._messages[0]]
        self._chat_display.controls.clear()
        self._chat_display.controls.append(
            ft.Container(
                content=ft.Text("历史已清空", italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                padding=10,
            )
        )
        self._chat_display.update()
