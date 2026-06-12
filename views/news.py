"""新闻简报"""

import threading
import flet as ft
from datetime import datetime
from config import cfg_str
from modules import news as mod_news
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, section_title,
)


class NewsView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._headlines = []

    def build(self):
        self._count_input = ft.Dropdown(
            label="条数",
            options=[ft.dropdown.Option(str(i)) for i in [5, 10, 15, 20, 30]],
            value="10",
            width=100,
            border_radius=12,
        )

        self._fetch_btn = primary_button("📰 刷新", on_click=self._do_fetch)
        self._analyze_btn = secondary_button("🤖 AI 分析", on_click=self._do_analyze)
        self._status = ft.Text("就绪", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        self._news_list = ft.ListView(spacing=4, padding=8, height=350)
        self._ai_result = text_input(label="AI 分析简报", multiline=True, height=150)
        self._ai_result.read_only = True

        control_card = glass_card(
            content=ft.Row([
                self._count_input,
                self._fetch_btn,
                self._analyze_btn,
                self._status,
            ], spacing=12),
            padding=16,
        )

        news_card = glass_card(
            content=ft.Column([
                ft.Text("热门新闻", size=16, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE),
                ft.Container(
                    content=self._news_list,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=12,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    height=350,
                ),
            ], spacing=8),
            padding=16,
        )

        ai_card = glass_card(
            content=ft.Column([
                ft.Text("AI 分析简报", size=16, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE),
                self._ai_result,
            ], spacing=8),
            padding=16,
        )

        content = ft.Column([
            section_title("新闻简报"),
            ft.Container(height=4),
            control_card,
            news_card,
            ai_card,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content)

    def _do_fetch(self, e=None):
        try:
            limit = int(self._count_input.value or 10)
        except ValueError:
            limit = 10

        self._status.value = "抓取中..."
        self._status.color = ft.Colors.PRIMARY
        self._status.update()
        self._fetch_btn.disabled = True
        self._fetch_btn.update()

        def worker():
            headlines = mod_news.fetch_hn_headlines(limit)
            self._headlines = headlines
            self.page.add(self._show_list(headlines))
            self.page.add(self._enable_fetch())
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _show_list(self, items):
        self._news_list.controls.clear()
        today = datetime.now().strftime("%Y-%m-%d %A")
        self._news_list.controls.append(
            ft.Container(
                content=ft.Text(today, size=14, weight=ft.FontWeight.W_600,
                               color=ft.Colors.PRIMARY),
                padding=ft.Padding(0, 0, 0, 4),
            )
        )
        for i, title in enumerate(items, 1):
            color = ft.Colors.ERROR if title.startswith("[") else ft.Colors.ON_SURFACE
            self._news_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{i:>2}.", size=13, color=ft.Colors.PRIMARY, width=30),
                        ft.Text(title, size=13, color=color),
                    ], spacing=4),
                    padding=ft.Padding(0, 2, 0, 2),
                )
            )
        self._news_list.update()
        if items and not items[0].startswith("["):
            self._analyze_btn.disabled = False
            self._analyze_btn.update()
        self._status.value = f"共 {len(items)} 条"
        self._status.color = ft.Colors.ON_SURFACE_VARIANT
        self._status.update()
        return ft.Container()

    def _enable_fetch(self):
        self._fetch_btn.disabled = False
        self._fetch_btn.update()
        return ft.Container()

    def _do_analyze(self, e=None):
        if not self._headlines:
            return

        self._ai_result.value = "分析中..."
        self._ai_result.read_only = False
        self._ai_result.update()
        self._analyze_btn.disabled = True
        self._analyze_btn.update()
        self._status.value = "AI 分析中..."
        self._status.update()

        def worker():
            import requests
            news_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(self._headlines))
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                api_url = cfg_str("AI", "api_url",
                                  "https://integrate.api.nvidia.com/v1/chat/completions")
                api_key = cfg_str("AI", "api_key", "")
                model = cfg_str("AI", "model", "qwen/qwen3-coder-480b-a35b-instruct")

                if not api_key:
                    self.page.add(self._show_analysis("[错误] 未配置 API 密钥"))
                    self.page.update()
                    return

                resp = requests.post(api_url, json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个新闻分析助手。"},
                        {"role": "user", "content": f"以下是 {today} 的 Hacker News 热门标题，请分析并生成简报：\n\n{news_text}"}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1024,
                }, headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }, timeout=120)
                data = resp.json()
                if resp.status_code != 200:
                    result = f"[分析失败] {data.get('error', {}).get('message', str(data))}"
                else:
                    result = data["choices"][0]["message"]["content"]
            except Exception as ex:
                result = f"[分析异常] {ex}"

            self.page.add(self._show_analysis(result))
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _show_analysis(self, result):
        self._ai_result.value = result
        self._ai_result.read_only = True
        self._ai_result.update()
        self._analyze_btn.disabled = False
        self._analyze_btn.update()
        if result.startswith("["):
            self._status.value = "分析失败"
            self._status.color = ft.Colors.ERROR
        else:
            self._status.value = "分析完成 ✓"
            self._status.color = ft.Colors.TERTIARY
        self._status.update()
        return ft.Container()
