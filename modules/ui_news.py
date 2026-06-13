"""
新闻简报 — PCL-CE 风格 UI
支持原版(HN)、订阅(RSS)、综合(HN+RSS) 三种来源，AI 分析简报。
"""

import tkinter as tk
import threading
from datetime import datetime
import requests
from modules.news import (
    fetch_hn_headlines, fetch_rss_headlines, fetch_headlines,
    SOURCE_CHOICES,
    ai_analyze,
)
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, cfg_int,
    make_button, make_secondary_button,
    make_label, make_text, make_combobox, make_spinbox,
)


class NewsWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "news"
    WIN_W, WIN_H = 800, 680

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("新闻简报")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(500, 400)
        self.configure(bg=C["bg"])
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)
        self.after(200, self._do_fetch)

    def _build_ui(self):
        # 顶部控制栏
        top_card = Card(self, padding=8)
        top_card.pack(fill=tk.X, padx=12, pady=8)

        row = top_card.inner
        make_label(row, text="来源:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)

        source_default = cfg_str("news", "source", "原版")
        if source_default not in SOURCE_CHOICES:
            source_default = "原版"
        self._source_var = tk.StringVar(value=source_default)
        src = make_combobox(row, values=SOURCE_CHOICES,
                            textvariable=self._source_var, width=8)
        src.pack(side=tk.LEFT, padx=4)

        make_label(row, text="条数:", bg=C["bg_card"], font=F["body"]).pack(side=tk.LEFT)
        self._count_var = tk.StringVar(value=str(cfg_int("news", "count", 10)))
        make_spinbox(row, from_=5, to=30, textvariable=self._count_var,
                     width=4, font=F["body"]).pack(side=tk.LEFT, padx=4)

        self._fetch_btn = make_button(row, text="刷新", command=self._do_fetch)
        self._fetch_btn.pack(side=tk.LEFT, padx=10)

        self._analyze_btn = make_secondary_button(row, text="AI 分析",
                                                   command=self._do_analyze)
        self._analyze_btn.pack(side=tk.LEFT)
        self._analyze_btn.config(state=tk.DISABLED)

        # 新闻列表
        list_card = Card(self, padding=8)
        list_card.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        make_label(list_card.inner, text="热门新闻", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 2))

        self._list_text = make_text(list_card.inner, height=8, font=F["body"],
                                     state=tk.DISABLED, wrap=tk.WORD)
        scroll = tk.Scrollbar(list_card.inner, command=self._list_text.yview,
                              bg=C["scrollbar"], troughcolor=C["bg"])
        self._list_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._list_text.pack(fill=tk.BOTH, expand=True)

        # AI 分析
        ai_card = Card(self, padding=8)
        ai_card.pack(fill=tk.BOTH, padx=12, pady=(4, 12))

        make_label(ai_card.inner, text="AI 分析简报", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 2))
        self._ai_text = make_text(ai_card.inner, height=5, font=F["body"],
                                   fg=C["success"], state=tk.DISABLED, wrap=tk.WORD)
        self._ai_text.pack(fill=tk.BOTH)

        self._headlines = []

    def _set_buttons(self, enabled=True):
        st = tk.NORMAL if enabled else tk.DISABLED
        self._fetch_btn.config(state=st)
        self._analyze_btn.config(state=st)

    def _do_fetch(self):
        self._set_buttons(False)
        self._fetch_btn.config(text="抓取中...")
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            limit = int(self._count_var.get())
        except ValueError:
            limit = 10
        source = self._source_var.get()
        items = fetch_headlines(limit, source)

        self._headlines = items
        self.after(0, self._show_list, items, source)
        self.after(0, self._set_buttons, True)
        self.after(0, lambda: self._fetch_btn.config(text="刷新"))

    def _show_list(self, items, source=""):
        self._list_text.config(state=tk.NORMAL)
        self._list_text.delete("1.0", tk.END)
        today = datetime.now().strftime("%Y-%m-%d %A")
        self._list_text.insert(tk.END, f"{today}\n\n", "date")
        self._list_text.tag_config("date", foreground=C["warning"], font=F["h2"])

        self._list_text.insert(tk.END, f"来源: {source}\n\n", "src_tag")
        self._list_text.tag_config("src_tag", foreground=C["info"], font=F["small"])

        for i, title in enumerate(items, 1):
            self._list_text.insert(tk.END, f"{i:>2}. {title}\n", "hl")
        self._list_text.tag_config("hl", foreground=C["fg"], font=F["body"])
        self._list_text.config(state=tk.DISABLED)

        if items and not items[0].startswith("[错误]") and not items[0].startswith("["):
            self._analyze_btn.config(state=tk.NORMAL)

    def _do_analyze(self):
        if not self._headlines:
            return
        self._ai_text.config(state=tk.NORMAL)
        self._ai_text.delete("1.0", tk.END)
        self._ai_text.insert("1.0", "分析中...")
        self._ai_text.config(state=tk.DISABLED)
        self._analyze_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self):
        news_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(self._headlines))
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            api_url = cfg_str("AI", "api_url",
                              "https://integrate.api.nvidia.com/v1/chat/completions")
            api_key = cfg_str("AI", "api_key", "")
            model = cfg_str("AI", "model", "qwen/qwen3-coder-480b-a35b-instruct")
            resp = requests.post(
                api_url,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个新闻分析助手。根据提供的新闻标题列表，生成一份简洁的今日简报，包括：1) 今日热点概述（1-2句话），2) 各条新闻的简要归类分析。用中文回答，控制在300字以内。"},
                        {"role": "user", "content": f"以下是 {today} 的热门标题，请分析并生成简报：\n\n{news_text}"}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1024,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
            data = resp.json()
            if resp.status_code != 200:
                result = f"[分析失败] {data.get('error', {}).get('message', str(data))}"
            else:
                result = data["choices"][0]["message"]["content"]
        except Exception as e:
            result = f"[分析异常] {e}"

        self.after(0, self._show_analysis, result)
        self.after(0, lambda: self._analyze_btn.config(state=tk.NORMAL))

    def _show_analysis(self, result):
        self._ai_text.config(state=tk.NORMAL)
        self._ai_text.delete("1.0", tk.END)
        self._ai_text.config(fg=C["error"] if result.startswith("[") else C["success"])
        self._ai_text.insert("1.0", result)
        self._ai_text.config(state=tk.DISABLED)
