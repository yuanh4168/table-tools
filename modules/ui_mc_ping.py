"""
Minecraft 服务器状态查询 — 新主题风格 UI
支持非阻塞重复查询、状态变化气泡提醒、自定义 PNG 背景。
"""

import tkinter as tk
import threading
import time
from modules import mc_ping as mod_mc_ping
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card, ServerInfoCard,
    cfg_str, cfg_int,
    make_button, make_entry, make_label,
    make_checkbutton, make_spinbox, notify,
)


class MCPingWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "mc_ping"
    WIN_W, WIN_H = 720, 520

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("Minecraft 服务器状态")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(600, 400)
        self.configure(bg=C["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._repeat_active = False
        self._repeat_thread: threading.Thread | None = None
        self._last_result: dict | None = None
        self._prev_online: bool | None = None
        self._prev_players: int | None = None
        self._query_running = False
        self._notify_threshold = cfg_int("mc-ping", "notify_threshold", 0)

        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _build_ui(self):
        # 查询栏
        query_frame = Card(self, padding=10)
        query_frame.pack(fill=tk.X, padx=14, pady=(12, 6))

        row = tk.Frame(query_frame.inner, bg=C["bg_card"])
        row.pack(fill=tk.X)

        make_label(row, text="服务器:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)
        self._host_var = tk.StringVar(value=cfg_str("mc-ping", "host", ""))
        make_entry(row, textvariable=self._host_var, width=22,
                   font=F["mono_sm"]).pack(side=tk.LEFT, padx=4)

        make_label(row, text="端口:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT, padx=(4, 0))
        self._port_var = tk.StringVar(value=str(cfg_int("mc-ping", "port", 25565)))
        make_entry(row, textvariable=self._port_var, width=6,
                   font=F["mono_sm"]).pack(side=tk.LEFT, padx=4)

        self._query_btn = make_button(row, text="查询", command=self._start_query)
        self._query_btn.pack(side=tk.LEFT, padx=8)

        # 循环查询
        self._repeat_var = tk.BooleanVar(value=False)
        make_checkbutton(row, text="监控", variable=self._repeat_var,
                         command=self._toggle_repeat,
                         bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT, padx=4)

        self._interval_var = tk.StringVar(value="5")
        make_spinbox(row, from_=1, to=60, textvariable=self._interval_var,
                     width=3, font=F["body"]).pack(side=tk.LEFT)
        make_label(row, text="秒", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)

        # 通知阈值
        make_label(row, text="| 人数变动通知:", bg=C["bg_card"], font=F["small"]).pack(side=tk.LEFT, padx=(8, 2))
        self._threshold_var = tk.StringVar(value=str(self._notify_threshold))
        make_spinbox(row, from_=0, to=50, textvariable=self._threshold_var,
                     width=3, font=F["small"]).pack(side=tk.LEFT)
        make_label(row, text="人", bg=C["bg_card"], font=F["small"]).pack(side=tk.LEFT)

        # 服务器信息卡片
        self._server_card = ServerInfoCard(self)
        self._server_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 12))

        self._show_placeholder()

    def _show_placeholder(self):
        self._server_card.set_result({
            "motd": "输入服务器地址后点击「查询」",
            "version": "支持 SRV 解析、MOTD、玩家列表",
            "host": "Minecraft Java Edition",
            "port": "",
            "online": "?",
            "max": "?",
            "latency": "",
            "players": [],
        })

    def _start_query(self):
        if self._query_running:
            return
        self._query_running = True
        self._query_btn.config(text="查询中…", state=tk.DISABLED)
        threading.Thread(target=self._do_query, daemon=True).start()

    def _do_query(self):
        host = self._host_var.get().strip()
        port_str = self._port_var.get().strip() or "25565"
        try:
            port = int(port_str)
        except ValueError:
            port = 25565
        if not host:
            self._after_safe(self._server_card.set_error, "请输入服务器地址")
            self._after_safe(self._query_done)
            return
        result = mod_mc_ping.query(host, port)
        self._last_result = result
        self._after_safe(self._show_result, result)
        self._after_safe(self._query_done)

    def _show_result(self, result: dict):
        if result.get("error"):
            self._server_card.set_error(result["error"])
        else:
            self._server_card.set_result(result)

    def _query_done(self):
        self._query_running = False
        self._query_btn.config(text="查询", state=tk.NORMAL)

    @staticmethod
    def _after_safe(fn, *args):
        try:
            root = tk._default_root
            if root and root.winfo_exists():
                root.after(0, fn, *args)
        except Exception:
            pass

    def _check_notify(self, result: dict):
        """检查状态变化并发送气泡通知。"""
        if result.get("error"):
            current_online = False
            current_players = 0
        else:
            current_online = True
            current_players = result.get("online", 0)

        host = self._host_var.get().strip() or "服务器"

        # 首次运行，仅记录状态
        if self._prev_online is None:
            self._prev_online = current_online
            self._prev_players = current_players
            return

        # 状态变化通知
        if current_online and not self._prev_online:
            notify("Minecraft 服务器", f"🟢 {host}\n服务器已上线")
        elif not current_online and self._prev_online:
            err = result.get("error", "连接断开")
            notify("Minecraft 服务器", f"🔴 {host}\n服务器已下线 ({err})", error=True)

        # 人数变动通知
        if current_online and self._prev_online:
            try:
                threshold = int(self._threshold_var.get() or 0)
            except ValueError:
                threshold = 0
            if threshold > 0:
                diff = current_players - self._prev_players
                if abs(diff) >= threshold:
                    direction = "↑" if diff > 0 else "↓"
                    notify(
                        "Minecraft 服务器",
                        f"{host}\n玩家变动: {self._prev_players} → {current_players} ({direction}{abs(diff)})"
                    )

        self._prev_online = current_online
        self._prev_players = current_players

    def _toggle_repeat(self):
        if self._repeat_var.get():
            self._repeat_active = True
            self._prev_online = None
            self._prev_players = None
            self._repeat_thread = threading.Thread(target=self._repeat_loop, daemon=True)
            self._repeat_thread.start()
        else:
            self._repeat_active = False

    def _repeat_loop(self):
        while self._repeat_active:
            host = self._host_var.get().strip()
            port_str = self._port_var.get().strip() or "25565"
            try:
                port = int(port_str)
            except ValueError:
                port = 25565
            if host and not self._query_running:
                result = mod_mc_ping.query(host, port)
                self._last_result = result
                self._after_safe(self._show_result, result)
                self._after_safe(self._check_notify, result)
            interval = int(self._interval_var.get() or 5)
            for _ in range(interval * 2):
                if not self._repeat_active:
                    break
                time.sleep(0.5)

    def _on_close(self):
        self._repeat_active = False
        self.destroy()
