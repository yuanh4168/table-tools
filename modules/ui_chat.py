"""
AI 对话 — PCL-CE 风格 UI
兼容 OpenAI API 的聊天窗口，消息历史记录。
"""

import tkinter as tk
import threading
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, make_button, make_secondary_button,
    make_entry, make_label, make_text,
)


class ChatWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "chat"
    WIN_W, WIN_H = 800, 640

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("AI 对话")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(500, 400)
        self.configure(bg=C["bg"])

        self._messages = [
            {"role": "system", "content": "你是一个有用的助手。用中文回答，简洁直接。"}
        ]
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

    def _build_ui(self):
        # 配置栏
        cfg_card = Card(self, padding=8)
        cfg_card.pack(fill=tk.X, padx=12, pady=6)

        row = cfg_card.inner
        make_label(row, text="API:", font=F["small"], bg=C["bg_card"]).pack(side=tk.LEFT)
        self._api_var = tk.StringVar(
            value=cfg_str("chat", "api_url") or cfg_str("AI", "api_url",
                       "https://integrate.api.nvidia.com/v1/chat/completions"))
        make_entry(row, textvariable=self._api_var, width=28,
                   font=F["mono_sm"], highlightthickness=0).pack(side=tk.LEFT, padx=3)

        make_label(row, text="模型:", font=F["small"], bg=C["bg_card"]).pack(side=tk.LEFT)
        self._model_var = tk.StringVar(
            value=cfg_str("chat", "model") or cfg_str("AI", "model",
                       "qwen/qwen3-coder-480b-a35b-instruct"))
        make_entry(row, textvariable=self._model_var, width=18,
                   font=F["mono_sm"], highlightthickness=0).pack(side=tk.LEFT, padx=3)

        make_label(row, text="Key:", font=F["small"], bg=C["bg_card"]).pack(side=tk.LEFT)
        self._key_var = tk.StringVar(
            value=cfg_str("chat", "api_key") or cfg_str("AI", "api_key", ""))
        make_entry(row, textvariable=self._key_var, width=14, show="*",
                   font=F["mono_sm"], highlightthickness=0).pack(side=tk.LEFT, padx=3)

        # 消息显示区域
        msg_card = Card(self, padding=8)
        msg_card.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self._msg_display = make_text(msg_card.inner, height=12, font=F["body"],
                                       state=tk.DISABLED, wrap=tk.WORD)
        scroll = tk.Scrollbar(msg_card.inner, command=self._msg_display.yview,
                              bg=C["scrollbar"], troughcolor=C["bg"])
        self._msg_display.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._msg_display.pack(fill=tk.BOTH, expand=True)

        # 标签颜色
        self._msg_display.tag_config("user", foreground=C["info"], font=F["h3"])
        self._msg_display.tag_config("assistant", foreground=C["success"], font=F["h3"])
        self._msg_display.tag_config("system", foreground=C["warning"], font=F["h3"])
        self._msg_display.tag_config("body", foreground=C["fg"], font=F["body"])
        self._msg_display.tag_config("error", foreground=C["error"], font=F["body"])

        # 底部输入
        bottom = tk.Frame(self, bg=C["bg"])
        bottom.pack(fill=tk.X, padx=12, pady=(0, 12))

        self._input_var = tk.StringVar()
        entry = make_entry(bottom, textvariable=self._input_var, font=F["body"])
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        entry.bind("<Return>", lambda e: self._send())
        entry.focus_set()

        btn_frame = tk.Frame(bottom, bg=C["bg"])
        btn_frame.pack(side=tk.RIGHT, padx=(8, 0))

        make_button(btn_frame, text="发送", command=self._send).pack(side=tk.LEFT)
        make_secondary_button(btn_frame, text="清空历史",
                              command=self._clear_history).pack(side=tk.LEFT, padx=4)

    def _send(self):
        text = self._input_var.get().strip()
        if not text:
            return
        try:
            import requests  # noqa: F401
        except ImportError:
            self._append_msg("error", "需要 requests 库: pip install requests")
            return
        self._input_var.set("")

        if not self._key_var.get().strip():
            self._append_msg("system", "请输入 API 密钥")
            return

        self._append_msg("user", text)
        self._messages.append({"role": "user", "content": text})
        self._append_msg("system", "思考中...")
        self._set_send_btn_state(tk.DISABLED)
        threading.Thread(target=self._do_query, daemon=True).start()

    def _set_send_btn_state(self, state):
        for w in self.winfo_children():
            for child in w.winfo_children():
                if isinstance(child, tk.Button) and child.cget("text") == "发送":
                    child.config(state=state)
                    return

    def _do_query(self):
        import requests
        try:
            api_url = self._api_var.get().strip()
            model = self._model_var.get().strip()
            api_key = self._key_var.get().strip()

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
                self.after(0, self._handle_error, f"API 错误 ({resp.status_code}): {err}")
                return
            content = data["choices"][0]["message"]["content"]
            self._messages.append({"role": "assistant", "content": content})
            self.after(0, self._remove_thinking)
            self.after(0, self._append_msg, "assistant", content)
        except Exception as e:
            self.after(0, self._handle_error, str(e))

    def _handle_error(self, msg):
        self._remove_thinking()
        self._append_msg("error", msg)
        self._set_send_btn_state(tk.NORMAL)

    def _remove_thinking(self):
        self._msg_display.config(state=tk.NORMAL)
        self._msg_display.delete("1.0", tk.END)
        self._rebuild_display()
        self._set_send_btn_state(tk.NORMAL)

    def _rebuild_display(self):
        self._msg_display.config(state=tk.NORMAL)
        self._msg_display.delete("1.0", tk.END)
        role_labels = {"user": "你", "assistant": "AI", "system": "系统", "error": "错误"}
        for msg in self._messages[1:]:
            role = msg["role"]
            content = msg["content"]
            label = role_labels.get(role, role)
            self._msg_display.insert(tk.END, f"{label}:\n", role)
            self._msg_display.insert(tk.END, f"{content}\n\n", "body")
        self._msg_display.see(tk.END)
        self._msg_display.config(state=tk.DISABLED)

    def _append_msg(self, role, content):
        self._msg_display.config(state=tk.NORMAL)
        role_labels = {"user": "你", "assistant": "AI", "system": "系统", "error": "错误"}
        if role == "system" and content == "思考中...":
            self._msg_display.insert(tk.END, "思考中...\n", "system")
        else:
            label = role_labels.get(role, role)
            self._msg_display.insert(tk.END, f"{label}:\n", role)
            self._msg_display.insert(tk.END, f"{content}\n\n", "body")
        self._msg_display.see(tk.END)
        self._msg_display.config(state=tk.DISABLED)

    def _clear_history(self):
        self._messages = [self._messages[0]]
        self._msg_display.config(state=tk.NORMAL)
        self._msg_display.delete("1.0", tk.END)
        self._msg_display.config(state=tk.DISABLED)
