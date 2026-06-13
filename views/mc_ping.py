import base64
import io
import threading
import time
import flet as ft
from config import cfg_str, cfg_int
from modules import mc_ping as mod_mc_ping
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, info_row, section_title,
)

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class MCPingView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._host = cfg_str("mc-ping", "host", "")
        self._port = str(cfg_int("mc-ping", "port", 25565))
        self._interval = str(cfg_int("mc-ping", "interval", 5))
        self._monitoring = False
        self._monitor_thread = None
        self._result_display = None
        self._notify_on = cfg_int("mc-ping", "notify_threshold", 5)

        self._monitor_event = threading.Event()
        self._query_lock = threading.Lock()

        # 提前创建所有控件，确保实例稳定
        self._host_input = text_input(label="服务器地址", value=self._host, width=280)
        self._port_input = text_input(label="端口", value=self._port, width=100)
        self._interval_input = text_input(label="间隔(秒)", value=self._interval, width=80)
        self._threshold_input = text_input(
            label="通知阈值(0=关闭)", value=str(self._notify_on), width=200
        )

        # 两个按钮：开始与停止，停止按钮初始隐藏
        self._start_btn = primary_button("开始监控", on_click=self._start_monitor)
        self._stop_btn = secondary_button("停止监控", on_click=self._stop_monitor)
        self._stop_btn.visible = False

        # 倒计时显示文本
        self._countdown_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        self._query_btn = primary_button("查询", on_click=self._do_query)
        self._status_text = ft.Text("就绪", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._result_display = ft.Column(spacing=8)

    def build(self):
        # 每次 build 重新组装，但复用控件
        form = glass_card(
            content=ft.Column([
                ft.Row([self._host_input, self._port_input], spacing=12),
                ft.Row([self._interval_input, self._threshold_input], spacing=12),
                ft.Row([
                    self._query_btn,
                    self._start_btn,
                    self._stop_btn,
                    self._countdown_text,
                    self._status_text,
                ], spacing=12),
            ], spacing=12),
            padding=20,
        )

        self._result_display.controls.clear()
        content = ft.Column([
            section_title("Minecraft 服务器状态"),
            ft.Container(height=4),
            form,
            self._result_display,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        return page_wrapper(content, page=self.page)

    # ---------- 查询 ----------
    def _do_query(self, e=None):
        if not self._query_lock.acquire(blocking=False):
            return
        try:
            host = self._host_input.value.strip()
            try:
                port = int(self._port_input.value.strip() or "25565")
            except ValueError:
                port = 25565
            if not host:
                self._status_text.value = "请输入服务器地址"
                self._status_text.color = ft.Colors.ERROR
                self._query_lock.release()
                self.page.update()
                return

            self._status_text.value = "查询中..."
            self._status_text.color = ft.Colors.PRIMARY
            self._query_btn.disabled = True
            self.page.update()

            def worker():
                result = mod_mc_ping.query(host, port)
                self.page.run_task(self._show_query_result, result)

            threading.Thread(target=worker, daemon=True).start()
        except Exception:
            self._query_lock.release()
            raise

    async def _show_query_result(self, result):
        try:
            if result.get("error"):
                self._result_display.controls.clear()
                self._result_display.controls.append(self._build_error_card(result["error"]))
            else:
                self._update_result(result)
            self._status_text.value = (
                f"完成 ({result.get('latency', '?')}ms)"
                if not result.get("error")
                else "查询失败"
            )
            self._status_text.color = (
                ft.Colors.ON_SURFACE_VARIANT
                if not result.get("error")
                else ft.Colors.ERROR
            )
        finally:
            self._query_btn.disabled = False
            self._query_lock.release()
            self.page.update()

    def _update_result(self, result):
        if result.get("error"):
            return
        online = result.get("online", 0)
        max_players = result.get("max", 0)
        latency = result.get("latency", "?")
        motd = result.get("motd", "")
        version = result.get("version", "未知")
        players = result.get("players", [])
        favicon_b64 = result.get("favicon", "")

        icon_widget = None
        if favicon_b64 and HAS_PIL:
            try:
                img_data = base64.b64decode(favicon_b64)
                pil_img = PILImage.open(io.BytesIO(img_data))
                pil_img.thumbnail((64, 64))
                buf = io.BytesIO()
                pil_img.save(buf, format='PNG')
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode()
                icon_widget = ft.Image(
                    src=f"data:image/png;base64,{img_b64}", width=64, height=64
                )
            except Exception:
                icon_widget = ft.Icon(ft.icons.SPORTS_ESPORTS, size=40)
        else:
            icon_widget = ft.Icon(ft.icons.SPORTS_ESPORTS, size=40)

        info_items = [
            ft.Row([icon_widget], alignment=ft.MainAxisAlignment.CENTER),
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
            glass_card(content=ft.Column(info_items, spacing=6), padding=16)
        )

    def _build_error_card(self, msg):
        return glass_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.Colors.ERROR, size=24),
                    ft.Text(
                        "查询失败",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ERROR,
                    ),
                ], spacing=8),
                ft.Text(msg, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ], spacing=8),
            padding=16,
        )

    # ---------- 监控控制 ----------
    def _start_monitor(self, e=None):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_event.clear()

        # 切换按钮可见性
        self._start_btn.visible = False
        self._stop_btn.visible = True

        # 初始化倒计时文本
        try:
            interval = int(self._interval_input.value.strip())
            if interval < 1:
                interval = 1
        except ValueError:
            interval = 5
        self._countdown_text.value = f"下次查询: {interval}秒"
        self.page.update()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _stop_monitor(self, e=None):
        if not self._monitoring:
            return
        self._monitoring = False
        self._monitor_event.set()

        # 恢复按钮
        self._start_btn.visible = True
        self._stop_btn.visible = False
        self._countdown_text.value = ""
        self.page.update()

    def _monitor_loop(self):
        try:
            while not self._monitor_event.is_set():
                # 读取间隔
                try:
                    interval = int(self._interval_input.value.strip())
                    if interval < 1:
                        interval = 1
                except ValueError:
                    interval = 5

                # 倒计时更新
                for remaining in range(interval, 0, -1):
                    if self._monitor_event.is_set():
                        return

                    async def update_countdown(r):
                        if self._monitoring:
                            self._countdown_text.value = f"下次查询: {r}秒"
                            self.page.update()
                    self.page.run_task(update_countdown, remaining)

                    # 分段休眠，快速响应停止
                    for _ in range(10):
                        if self._monitor_event.is_set():
                            return
                        time.sleep(0.1)

                # 执行查询
                host = self._host_input.value.strip()
                try:
                    port = int(self._port_input.value.strip() or "25565")
                except ValueError:
                    port = 25565
                if host:
                    result = mod_mc_ping.query(host, port)
                    async def show():
                        if self._monitoring:
                            if result.get("error"):
                                self._result_display.controls.clear()
                                self._result_display.controls.append(
                                    self._build_error_card(result["error"])
                                )
                            else:
                                self._update_result(result)
                            self.page.update()
                    self.page.run_task(show)

        finally:
            # 如果是因为按钮停止触发的，_stop_monitor 已经重置了按钮状态
            # 但如果是页面销毁导致的线程结束，这里需要兜底
            async def cleanup():
                if self._monitoring:  # 说明是异常退出，需恢复按钮
                    self._start_btn.visible = True
                    self._stop_btn.visible = False
                    self._countdown_text.value = ""
                    self._monitoring = False
                    self.page.update()
            self.page.run_task(cleanup)