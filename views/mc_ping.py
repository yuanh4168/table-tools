"""Minecraft 服务器状态查询"""

import threading
import flet as ft
from config import cfg_str, cfg_int
from modules import mc_ping as mod_mc_ping
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, info_row, section_title,
)


class MCPingView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._host = cfg_str("mc-ping", "host", "")
        self._port = str(cfg_int("mc-ping", "port", 25565))
        self._interval = str(cfg_int("mc-ping", "interval", 5))
        self._monitoring = False
        self._result_display = None
        self._server_info = None
        self._notify_on = cfg_int("mc-ping", "notify_threshold", 5)

    def build(self):
        self._host_input = text_input(label="服务器地址", value=self._host, width=280)
        self._port_input = text_input(label="端口", value=self._port, width=100)
        self._interval_input = text_input(label="间隔(秒)", value=self._interval, width=80)
        self._threshold_input = text_input(label="人数变动通知阈值(0=关闭)", value=str(self._notify_on), width=200)

        self._query_btn = primary_button("🔍 查询", on_click=self._do_query)
        self._monitor_btn = secondary_button("▶ 开始监控", on_click=self._toggle_monitor)
        self._status_text = ft.Text("就绪", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._server_info = ft.Container(visible=False)

        form = glass_card(
            content=ft.Column([
                ft.Row([
                    self._host_input,
                    self._port_input,
                ], spacing=12),
                ft.Row([
                    self._interval_input,
                    self._threshold_input,
                ], spacing=12),
                ft.Row([
                    self._query_btn,
                    self._monitor_btn,
                    self._status_text,
                ], spacing=12, alignment=ft.MainAxisAlignment.START),
            ], spacing=12),
            padding=20,
        )

        self._result_display = ft.Column(spacing=8)

        content = ft.Column([
            section_title("Minecraft 服务器状态"),
            ft.Container(height=4),
            form,
            self._result_display,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content)

    def _do_query(self, e=None):
        host = self._host_input.value.strip()
        try:
            port = int(self._port_input.value.strip() or "25565")
        except ValueError:
            port = 25565
        if not host:
            self._status_text.value = "请输入服务器地址"
            self._status_text.color = ft.Colors.ERROR
            self._status_text.update()
            return

        self._status_text.value = "查询中..."
        self._status_text.color = ft.Colors.PRIMARY
        self._status_text.update()
        self._query_btn.disabled = True
        self._query_btn.update()

        # 在后台线程中查询
        def worker():
            result = mod_mc_ping.query(host, port)
            self.page.add(self._update_result(result))
            self.page.update()

            self._status_text.value = f"完成 ({result.get('latency', '?')}ms)" if not result.get("error") else "查询失败"
            self._status_text.color = ft.Colors.ON_SURFACE_VARIANT if not result.get("error") else ft.Colors.ERROR
            self._query_btn.disabled = False
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _update_result(self, result):
        if result.get("error"):
            return self._build_error_card(result["error"])

        online = result.get("online", 0)
        max_players = result.get("max", 0)
        latency = result.get("latency", "?")
        motd = result.get("motd", "")
        version = result.get("version", "未知")
        players = result.get("players", [])

        info_items = [
            info_row("MOTD", motd),
            info_row("版本", version),
            info_row("在线", f"{online} / {max_players}"),
            info_row("延迟", f"{latency} ms"),
            info_row("地址", f"{result.get('host', '')}:{result.get('port', '')}"),
        ]
        if players:
            names = [p.get("name", "?") for p in players[:10]]
            info_items.append(info_row("玩家", ", ".join(names)))

        self._result_display.controls.clear()
        self._result_display.controls.append(
            glass_card(
                content=ft.Column(info_items, spacing=6),
                padding=16,
            )
        )
        return ft.Container()

    def _build_error_card(self, msg):
        self._result_display.controls.clear()
        self._result_display.controls.append(
            glass_card(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.Colors.ERROR, size=24),
                        ft.Text("查询失败", size=16, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.ERROR),
                    ], spacing=8),
                    ft.Text(msg, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                ], spacing=8),
                padding=16,
            )
        )
        return ft.Container()

    def _toggle_monitor(self, e=None):
        self._monitoring = not self._monitoring
        if self._monitoring:
            self._monitor_btn.text = "⏹ 停止监控"
            self._monitor_btn.update()
            self._start_monitor_loop()
        else:
            self._monitor_btn.text = "▶ 开始监控"
            self._monitor_btn.update()

    def _start_monitor_loop(self):
        def loop():
            import time
            while self._monitoring:
                host = self._host_input.value.strip()
                try:
                    port = int(self._port_input.value.strip() or "25565")
                except ValueError:
                    port = 25565
                if host:
                    result = mod_mc_ping.query(host, port)
                    self.page.add(self._update_result(result))
                    self.page.update()
                try:
                    interval = int(self._interval_input.value or "5")
                except ValueError:
                    interval = 5
                for _ in range(interval):
                    if not self._monitoring:
                        break
                    time.sleep(1)

        threading.Thread(target=loop, daemon=True).start()
