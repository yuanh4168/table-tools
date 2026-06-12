"""
公文生成器 — 完整 More EnQing 功能移植
红头公文 + 恩情文章，AI提示词生成，HTML渲染预览，导出。
"""

import datetime
import os
import re
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from modules.ui_common import (
    ImageBackgroundMixin, C, F, Card,
    cfg_str, make_button, make_secondary_button,
    make_entry, make_text, make_label,
    make_combobox, make_separator, flash_title,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==================== 核心函数（移植自 More EnQing app.js）====================

def build_red_prompt(org, doc_type, affair, doc_num, sign_unit, sign_date, min_words, table_req):
    """构建红头公文的 AI 提示词。"""
    final_doc_num = doc_num.strip() or f"〔{datetime.date.today().year}〕趣号"
    final_sign_unit = sign_unit.strip() or org
    final_date = sign_date.strip() or f"{datetime.date.today().year}年{datetime.date.today().month}月{datetime.date.today().day}日"
    table_text = "必须包含一个完整的信息表格（例如物资清单、降雨等级表等）。" if table_req == "是" else "不强制要求表格，但可根据内容自行决定。"
    return (
        f"你是一个幽默公文写手。请根据以下信息，输出一份红头文件的纯文本内容"
        f"（不要输出HTML，不要加额外解释），严格遵循下面的格式标记。\n\n"
        f"【用户输入】\n"
        f"- 发文机关：{org}\n"
        f"- 文号：{final_doc_num}\n"
        f"- 文件类型：{doc_type}\n"
        f"- 核心事由：{affair}\n"
        f"- 落款单位：{final_sign_unit}\n"
        f"- 成文日期：{final_date}\n"
        f"- 最低字数要求：{min_words} 字以上\n"
        f"- 表格要求：{table_text}\n\n"
        f"【输出格式】\n"
        f"<<RED_START>>\n"
        f"发文机关：{org}\n"
        f"文号：{final_doc_num}\n"
        f"文件类型：{doc_type}\n"
        f"标题：关于{affair}的{doc_type}\n"
        f"主送单位：请根据发文机关和事由自行编造合理的主送单位\n"
        f"<<BODY_START>>\n"
        f"（正文，严肃公文口吻，分条目展开，包含荒诞科学化论述，"
        f"总字数不低于{min_words}字。{table_text}）\n"
        f"<<BODY_END>>\n"
        f"落款单位：{final_sign_unit}\n"
        f"成文日期：{final_date}\n"
        f"（此件公开发布）\n"
        f"<<RED_END>>\n"
        f"只输出纯文本，不要解释。"
    )


def parse_red_text(text):
    """解析 AI 返回的红头公文文本。"""
    def_val = "未知"
    return {
        "org": _extract(text, r"发文机关[：:]\s*(.+)", def_val),
        "doc_num": _extract(text, r"文号[：:]\s*(.+)", def_val),
        "title": _extract(text, r"标题[：:]\s*(.+)", def_val),
        "body": _extract(text, r"<<BODY_START>>\s*([\s\S]*?)\s*<<BODY_END>>", "暂无正文"),
        "sign_unit": _extract(text, r"落款单位[：:]\s*(.+)", def_val),
        "sign_date": _extract(text, r"成文日期[：:]\s*(.+)", def_val),
    }


def render_red_html(data):
    """将红头公文数据渲染为 HTML。"""
    org = data.get("org", "未知")
    doc_num = data.get("doc_num", "")
    title = data.get("title", "")
    body = data.get("body", "")
    sign_unit = data.get("sign_unit", "")
    sign_date = data.get("sign_date", "")

    # 简单 Markdown 表格转 HTML
    body_html = _markdown_to_html(body)
    if not body_html:
        body_html = f"<p>  {body}</p>"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:white;display:flex;justify-content:center;padding:30px 20px;font-family:'Times New Roman','仿宋','FangSong',serif;}}
.document{{max-width:1000px;width:100%;background:white;padding:42px 40px 56px;}}
.red-header{{text-align:center;margin-bottom:18px;border-bottom:2px solid #b11e23;padding-bottom:14px;}}
.org-name{{font-size:2rem;font-weight:800;font-family:'黑体',sans-serif;color:#b11e23;}}
.doc-number{{font-size:1rem;margin-top:8px;}}
.title{{text-align:center;font-size:1.6rem;font-weight:600;margin:30px 0 24px;font-family:'黑体',sans-serif;}}
.content{{font-size:1rem;line-height:1.75;margin-bottom:20px;}}
.content p{{margin-bottom:1em;}}
.content table{{margin:1em auto;border-collapse:collapse;width:100%;}}
.content th,.content td{{border:1px solid #aaa;padding:8px;text-align:center;}}
.signature{{text-align:right;margin-top:56px;}}
.stamp{{color:#b11e23;margin-top:6px;font-size:0.9rem;}}
.version-note{{margin-top:48px;padding-top:12px;border-top:1px solid #ddd;font-size:0.7rem;text-align:center;}}
</style></head><body>
<div class="document">
<div class="red-header"><div class="org-name">{_esc(org)}</div><div class="doc-number">{_esc(doc_num)}</div></div>
<div class="title">{_esc(title)}</div>
<div class="content">{body_html}</div>
<div class="signature"><div>{_esc(sign_unit)}</div><div>{_esc(sign_date)}</div><div class="stamp">（此件公开发布）</div></div>
<div class="version-note">{_esc(org)}办公室 印发</div>
</div></body></html>"""


def build_eulogy_prompt(hero, deed, place, time, enable_img):
    """构建恩情文章的 AI 提示词。"""
    p = place.strip() or "那片热土"
    t = time.strip() or "那个难忘的日子"
    img_inst = ""
    if enable_img == "是":
        img_inst = "你必须在文章适当位置插入图片占位符，格式为 <<IMG: 图片内容描述>>，请根据情节生成2-4个具体描述。"
    return (
        f"你是一位擅长夸张感恩文章的作者。请根据以下信息，输出一篇恩情文章的纯文本内容"
        f"（不要输出HTML，遵循格式标记）。\n\n"
        f"【素材】\n"
        f"- 主角：{hero}\n"
        f"- 事迹：{deed}\n"
        f"- 地点：{p}\n"
        f"- 时间：{t}\n"
        f"- 图片要求：{img_inst}\n\n"
        f"【输出格式】\n"
        f"<<EULOGY_START>>\n"
        f"标题：XXXXXXXX（必须包含主角名字）\n"
        f"<<BODY_START>>\n"
        f"（正文，极度夸张感人，约400~800字，分3~10段。{img_inst}）\n"
        f"<<BODY_END>>\n"
        f"作者：一位被感动的见证者\n"
        f"<<EULOGY_END>>\n\n"
        f"只输出纯文本。"
    )


def parse_eulogy_text(text):
    """解析 AI 返回的恩情文章文本。"""
    return {
        "title": _extract(text, r"标题[：:]\s*(.+)", "恩情永存"),
        "body": _extract(text, r"<<BODY_START>>\s*([\s\S]*?)\s*<<BODY_END>>", "无正文"),
    }


def render_eulogy_html(data):
    """将恩情文章数据渲染为 HTML。"""
    title = data.get("title", "恩情永存")
    body = data.get("body", "")

    processed = body.replace("<<IMG:", '<div class="img-placeholder">📷 ')
    processed = processed.replace(">>", '</div>')

    paragraphs = processed.split("\n\n")
    body_html = "".join(f"<p>  {p.replace(chr(10), '<br>')}</p>" for p in paragraphs if p.strip())
    if not body_html:
        body_html = f"<p>  {body}</p>"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{background:#fef9ef;font-family:'Georgia','宋体',serif;padding:30px 20px;}}
.article{{max-width:800px;margin:0 auto;background:#fffef7;padding:40px 30px;border-radius:28px;}}
h1{{text-align:center;font-size:1.8rem;color:#b45f2b;margin-bottom:30px;border-left:6px solid #e67e22;padding-left:16px;}}
p{{text-indent:2em;margin-bottom:1.2em;font-size:1rem;line-height:1.7;}}
.quote{{font-style:italic;text-align:center;margin-top:30px;}}
.img-placeholder{{border:2px dashed #c0392b;background:#fff0f0;padding:12px;margin:15px 0;border-radius:16px;text-align:center;font-weight:bold;}}
</style></head><body>
<div class="article"><h1>📖 {_esc(title)}</h1>{body_html}<div class="quote">恩情似海，铭记于心</div></div></body></html>"""


# ==================== 辅助函数 ====================


def _extract(text, pattern, default=""):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


def _esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _markdown_to_html(text):
    """简单 Markdown 转 HTML（段落、表格）。"""
    lines = text.split("\n")
    output = []
    table_buf = []
    in_table = False

    def flush_table():
        if not table_buf:
            return ""
        rows = []
        for i, row in enumerate(table_buf):
            cells = [c.strip() for c in row.split("|") if c.strip()]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{_esc(c)}</{tag}>" for c in cells) + "</tr>")
        table_buf.clear()
        return "<table>" + "".join(rows) + "</table>"

    for line in lines:
        if line.strip().startswith("|"):
            in_table = True
            table_buf.append(line.strip())
        else:
            if in_table:
                output.append(flush_table())
                in_table = False
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("---"):
                continue
            if stripped.startswith("##"):
                output.append(f"<h3>{_esc(stripped.lstrip('#').strip())}</h3>")
            elif stripped.startswith("#"):
                output.append(f"<h2>{_esc(stripped.lstrip('#').strip())}</h2>")
            elif re.match(r"^\d+[.、]", stripped):
                output.append(f"<p><strong>{_esc(stripped)}</strong></p>")
            else:
                output.append(f"<p>  {_esc(stripped)}</p>")
    if in_table:
        output.append(flush_table())
    return "\n".join(output)


def _open_in_browser(html_content):
    """将 HTML 写入临时文件并在浏览器打开。"""
    try:
        fd, path = tempfile.mkstemp(suffix=".html", prefix="document_", dir=BASE_DIR)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html_content)
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(path)}")
    except Exception as e:
        messagebox.showerror("打开失败", str(e))


def _call_ai_api(prompt):
    """调用 AI API 生成内容。"""
    import requests
    api_url = cfg_str("AI", "api_url", "https://integrate.api.nvidia.com/v1/chat/completions")
    api_key = cfg_str("AI", "api_key", "")
    model = cfg_str("AI", "model", "qwen/qwen3-coder-480b-a35b-instruct")

    if not api_key:
        return "[错误] 请在 config.ini 中配置 AI API 密钥"

    try:
        resp = requests.post(
            api_url,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        data = resp.json()
        if resp.status_code != 200:
            return f"[错误] {data.get('error', {}).get('message', str(data))}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[错误] {e}"


# ==================== 主窗口 ====================

class DocumentWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "document"
    WIN_W, WIN_H = 960, 760

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("公文生成器")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(700, 580)
        self.configure(bg=C["bg"])
        self._build_ui()
        self.setup_bg(self, self.WIN_W, self.WIN_H)

        self._current_html = ""

    def _clear_main(self):
        for w in self._main_area.winfo_children():
            w.destroy()

    def _build_ui(self):
        # 选项卡
        tab_frame = tk.Frame(self, bg=C["bg"])
        tab_frame.pack(fill=tk.X, padx=12, pady=(8, 0))

        self._tab_var = tk.StringVar(value="red")
        for val, lbl in [("red", "📄 红头公文"), ("eulogy", "📖 恩情文章"), ("simple", "📝 简易模板")]:
            rb = tk.Radiobutton(
                tab_frame, text=lbl, variable=self._tab_var, value=val,
                bg=C["bg"], fg=C["fg"], selectcolor=C["bg_card"],
                font=F["body"], activebackground=C["bg"], activeforeground=C["fg"],
                relief=tk.FLAT, highlightthickness=0, indicatoron=0,
                padx=14, pady=4, cursor="hand2",
                command=self._switch_tab,
            )
            rb.pack(side=tk.LEFT, padx=2)

        # 分隔
        make_separator(self, bg=C["separator"]).pack(fill=tk.X, padx=12, pady=4)

        # 主区域
        self._main_area = tk.Frame(self, bg=C["bg"])
        self._main_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # 底部状态栏
        self._status_frame = tk.Frame(self, bg=C["bg"], height=28)
        self._status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._status_label = tk.Label(
            self._status_frame, text="就绪", font=F["small"],
            fg=C["fg_muted"], bg=C["bg"], anchor="w")
        self._status_label.pack(fill=tk.X, padx=12)

        self._switch_tab()

    def _set_status(self, msg):
        self._status_label.config(text=msg)
        self.update_idletasks()

    def _switch_tab(self):
        tab = self._tab_var.get()
        self._clear_main()
        if tab == "red":
            self._build_red_tab()
        elif tab == "eulogy":
            self._build_eulogy_tab()
        else:
            self._build_simple_tab()

    # ==================== 红头公文选项卡 ====================

    def _build_red_tab(self):
        main = self._main_area
        outer = tk.Frame(main, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        # 左侧表单
        form_card = Card(outer, padding=12)
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        row_h = {"bg": C["bg_card"], "fg": C["fg"], "font": F["body"]}
        entries = {}
        fields = [
            ("发文机关:", "red_org", cfg_str("document", "org", "厦门市教育局")),
            ("文件类型:", "red_type", "通知"),
            ("核心事由:", "red_event", "加强数字化建设"),
            ("文号:", "red_num", f"〔{datetime.date.today().year}〕号"),
            ("落款单位:", "red_sign", ""),
            ("成文日期:", "red_date", ""),
            ("最低字数:", "red_words", "800"),
            ("要求表格:", "red_table", "否"),
        ]

        for i, (label, key, default) in enumerate(fields):
            r = i
            make_label(form_card.inner, text=label, **row_h).grid(
                row=r, column=0, sticky="e", padx=4, pady=4)

            if key == "red_type":
                var = tk.StringVar(value=default)
                cb = make_combobox(form_card.inner, values=["通知", "通报", "决定", "批复"],
                                   textvariable=var, width=18)
                cb.grid(row=r, column=1, padx=4, pady=4)
                entries[key] = var
            elif key == "red_table":
                var = tk.StringVar(value=default)
                cb = make_combobox(form_card.inner, values=["否", "是"],
                                   textvariable=var, width=18)
                cb.grid(row=r, column=1, padx=4, pady=4)
                entries[key] = var
            else:
                var = tk.StringVar(value=default)
                make_entry(form_card.inner, textvariable=var, width=22).grid(
                    row=r, column=1, padx=4, pady=4)
                entries[key] = var

        # 按钮
        btn_r = len(fields)
        btn_frame = tk.Frame(form_card.inner, bg=C["bg_card"])
        btn_frame.grid(row=btn_r, column=0, columnspan=2, pady=10)

        make_button(btn_frame, text="生成提示词",
                    command=lambda: self._gen_red_prompt(entries)).pack(side=tk.LEFT)
        make_secondary_button(btn_frame, text="AI 生成全文",
                              command=lambda: self._gen_red_full(entries)).pack(side=tk.LEFT, padx=4)

        # 右侧显示区
        display_card = Card(outer, padding=10)
        display_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 显示标签页切换
        self._red_display_mode = tk.StringVar(value="prompt")
        mode_frame = tk.Frame(display_card.inner, bg=C["bg_card"])
        mode_frame.pack(fill=tk.X, pady=(0, 4))

        for val, lbl in [("prompt", "提示词"), ("result", "AI 结果"), ("html", "HTML 预览")]:
            rb = tk.Radiobutton(
                mode_frame, text=lbl, variable=self._red_display_mode, value=val,
                bg=C["bg_card"], fg=C["fg"], selectcolor=C["bg_input"],
                font=F["small"], activebackground=C["bg_card"], activeforeground=C["fg"],
                relief=tk.FLAT, highlightthickness=0, indicatoron=0,
                padx=8, pady=2, cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=1)

        self._red_text = make_text(display_card.inner, height=20, font=F["mono_sm"],
                                    wrap=tk.WORD)
        self._red_text.pack(fill=tk.BOTH, expand=True)
        self._red_text.insert("1.0", "填写左侧表单后点击「生成提示词」或「AI 生成全文」")

        # 操作按钮
        op_frame = tk.Frame(display_card.inner, bg=C["bg_card"])
        op_frame.pack(fill=tk.X, pady=(4, 0))
        make_secondary_button(op_frame, text="复制内容",
                              command=lambda: self._copy_text(self._red_text)).pack(side=tk.LEFT)
        make_secondary_button(op_frame, text="浏览器预览",
                              command=self._preview_red_html).pack(side=tk.LEFT, padx=4)
        make_secondary_button(op_frame, text="导出 HTML",
                              command=self._export_red_html).pack(side=tk.LEFT, padx=4)

        self._entries_red = entries

    def _gen_red_prompt(self, entries):
        prompt = build_red_prompt(
            entries["red_org"].get(),
            entries["red_type"].get(),
            entries["red_event"].get(),
            entries["red_num"].get(),
            entries["red_sign"].get(),
            entries["red_date"].get(),
            entries["red_words"].get(),
            entries["red_table"].get(),
        )
        self._red_display_mode.set("prompt")
        self._red_text.delete("1.0", tk.END)
        self._red_text.insert("1.0", prompt)
        self._set_status("提示词已生成")

    def _gen_red_full(self, entries):
        prompt = build_red_prompt(
            entries["red_org"].get(),
            entries["red_type"].get(),
            entries["red_event"].get(),
            entries["red_num"].get(),
            entries["red_sign"].get(),
            entries["red_date"].get(),
            entries["red_words"].get(),
            entries["red_table"].get(),
        )
        self._red_display_mode.set("result")
        self._red_text.delete("1.0", tk.END)
        self._red_text.insert("1.0", "正在调用 AI 生成...\n")
        self._set_status("AI 生成中...")

        def worker():
            result = _call_ai_api(prompt)
            self.after(0, self._show_red_result, result)

        threading.Thread(target=worker, daemon=True).start()

    def _show_red_result(self, result):
        self._red_text.delete("1.0", tk.END)
        self._red_text.insert("1.0", result)
        if not result.startswith("[错误]"):
            # 解析并生成 HTML
            data = parse_red_text(result)
            self._current_html = render_red_html(data)
            self._set_status("AI 生成完成！可点击「浏览器预览」查看效果")
        else:
            self._set_status("生成失败")

    def _preview_red_html(self):
        if self._current_html:
            _open_in_browser(self._current_html)
        else:
            # 尝试从当前文本解析
            text = self._red_text.get("1.0", tk.END).strip()
            if text and not text.startswith("正在") and not text.startswith("填写"):
                data = parse_red_text(text)
                self._current_html = render_red_html(data)
                _open_in_browser(self._current_html)
            else:
                messagebox.showinfo("提示", "请先生成 AI 内容")

    def _export_red_html(self):
        if not self._current_html:
            self._preview_red_html()
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("所有文件", "*.*")],
            title="导出公文 HTML")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_html)
            messagebox.showinfo("成功", f"已导出至:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    # ==================== 恩情文章选项卡 ====================

    def _build_eulogy_tab(self):
        main = self._main_area
        outer = tk.Frame(main, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        # 左侧表单
        form_card = Card(outer, padding=12)
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        row_h = {"bg": C["bg_card"], "fg": C["fg"], "font": F["body"]}
        entries = {}
        fields = [
            ("主角:", "e_hero", "雷锋同志"),
            ("事迹:", "e_deed", "默默奉献"),
            ("地点:", "e_place", ""),
            ("时间:", "e_time", ""),
            ("图片占位:", "e_img", "否"),
        ]

        for i, (label, key, default) in enumerate(fields):
            r = i
            make_label(form_card.inner, text=label, **row_h).grid(
                row=r, column=0, sticky="e", padx=4, pady=4)
            if key == "e_img":
                var = tk.StringVar(value=default)
                cb = make_combobox(form_card.inner, values=["否", "是"],
                                   textvariable=var, width=18)
                cb.grid(row=r, column=1, padx=4, pady=4)
                entries[key] = var
            else:
                var = tk.StringVar(value=default)
                make_entry(form_card.inner, textvariable=var, width=22).grid(
                    row=r, column=1, padx=4, pady=4)
                entries[key] = var

        btn_r = len(fields)
        btn_frame = tk.Frame(form_card.inner, bg=C["bg_card"])
        btn_frame.grid(row=btn_r, column=0, columnspan=2, pady=10)

        make_button(btn_frame, text="生成提示词",
                    command=lambda: self._gen_eulogy_prompt(entries)).pack(side=tk.LEFT)
        make_secondary_button(btn_frame, text="AI 生成全文",
                              command=lambda: self._gen_eulogy_full(entries)).pack(side=tk.LEFT, padx=4)

        # 右侧显示区
        display_card = Card(outer, padding=10)
        display_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._eulogy_display_mode = tk.StringVar(value="prompt")
        mode_frame = tk.Frame(display_card.inner, bg=C["bg_card"])
        mode_frame.pack(fill=tk.X, pady=(0, 4))

        for val, lbl in [("prompt", "提示词"), ("result", "AI 结果"), ("html", "HTML 预览")]:
            rb = tk.Radiobutton(
                mode_frame, text=lbl, variable=self._eulogy_display_mode, value=val,
                bg=C["bg_card"], fg=C["fg"], selectcolor=C["bg_input"],
                font=F["small"], activebackground=C["bg_card"], activeforeground=C["fg"],
                relief=tk.FLAT, highlightthickness=0, indicatoron=0,
                padx=8, pady=2, cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=1)

        self._eulogy_text = make_text(display_card.inner, height=20, font=F["mono_sm"],
                                       wrap=tk.WORD)
        self._eulogy_text.pack(fill=tk.BOTH, expand=True)
        self._eulogy_text.insert("1.0", "填写左侧表单后点击「生成提示词」或「AI 生成全文」")

        op_frame = tk.Frame(display_card.inner, bg=C["bg_card"])
        op_frame.pack(fill=tk.X, pady=(4, 0))
        make_secondary_button(op_frame, text="复制内容",
                              command=lambda: self._copy_text(self._eulogy_text)).pack(side=tk.LEFT)
        make_secondary_button(op_frame, text="浏览器预览",
                              command=self._preview_eulogy_html).pack(side=tk.LEFT, padx=4)

        self._entries_eulogy = entries
        self._eulogy_current_html = ""

    def _gen_eulogy_prompt(self, entries):
        prompt = build_eulogy_prompt(
            entries["e_hero"].get(),
            entries["e_deed"].get(),
            entries["e_place"].get(),
            entries["e_time"].get(),
            entries["e_img"].get(),
        )
        self._eulogy_display_mode.set("prompt")
        self._eulogy_text.delete("1.0", tk.END)
        self._eulogy_text.insert("1.0", prompt)
        self._set_status("提示词已生成")

    def _gen_eulogy_full(self, entries):
        prompt = build_eulogy_prompt(
            entries["e_hero"].get(),
            entries["e_deed"].get(),
            entries["e_place"].get(),
            entries["e_time"].get(),
            entries["e_img"].get(),
        )
        self._eulogy_display_mode.set("result")
        self._eulogy_text.delete("1.0", tk.END)
        self._eulogy_text.insert("1.0", "正在调用 AI 生成...\n")
        self._set_status("AI 生成中...")

        def worker():
            result = _call_ai_api(prompt)
            self.after(0, self._show_eulogy_result, result)

        threading.Thread(target=worker, daemon=True).start()

    def _show_eulogy_result(self, result):
        self._eulogy_text.delete("1.0", tk.END)
        self._eulogy_text.insert("1.0", result)
        if not result.startswith("[错误]"):
            data = parse_eulogy_text(result)
            self._eulogy_current_html = render_eulogy_html(data)
            self._set_status("AI 生成完成！可点击「浏览器预览」查看效果")
        else:
            self._set_status("生成失败")

    def _preview_eulogy_html(self):
        if self._eulogy_current_html:
            _open_in_browser(self._eulogy_current_html)
        else:
            text = self._eulogy_text.get("1.0", tk.END).strip()
            if text and not text.startswith("正在") and not text.startswith("填写"):
                data = parse_eulogy_text(text)
                self._eulogy_current_html = render_eulogy_html(data)
                _open_in_browser(self._eulogy_current_html)
            else:
                messagebox.showinfo("提示", "请先生成 AI 内容")

    # ==================== 简易模板选项卡 ====================

    def _build_simple_tab(self):
        """原有的简易模板功能。"""
        main = self._main_area
        outer = tk.Frame(main, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        form_card = Card(outer, padding=12)
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        row_h = {"bg": C["bg_card"], "fg": C["fg"], "font": F["body"]}

        r = 0
        make_label(form_card.inner, text="发文单位:", **row_h).grid(
            row=r, column=0, sticky="e", padx=6, pady=6)
        self._org_var = tk.StringVar(value=cfg_str("document", "org", "厦门市教育局"))
        make_entry(form_card.inner, textvariable=self._org_var, width=24).grid(
            row=r, column=1, padx=6, pady=6)

        r = 1
        make_label(form_card.inner, text="文件类型:", **row_h).grid(
            row=r, column=0, sticky="e", padx=6, pady=6)
        self._type_var = tk.StringVar(value=cfg_str("document", "type", "通知"))
        cb = make_combobox(form_card.inner, values=["通知", "通报", "决定", "批复"],
                           textvariable=self._type_var, width=20)
        cb.grid(row=r, column=1, padx=6, pady=6)

        r = 2
        make_label(form_card.inner, text="文件标题:", **row_h).grid(
            row=r, column=0, sticky="e", padx=6, pady=6)
        self._subject_var = tk.StringVar(value="关于...的通知")
        make_entry(form_card.inner, textvariable=self._subject_var, width=24).grid(
            row=r, column=1, padx=6, pady=6)

        r = 3
        make_label(form_card.inner, text="正文内容:", **row_h).grid(
            row=r, column=0, sticky="ne", padx=6, pady=6)
        self._content_text = make_text(form_card.inner, width=30, height=10, font=F["body"])
        self._content_text.grid(row=r, column=1, padx=6, pady=6)

        r = 4
        btn_frame = tk.Frame(form_card.inner, bg=C["bg_card"])
        btn_frame.grid(row=r, column=0, columnspan=2, pady=10)

        make_button(btn_frame, text="导出文件", command=self._export_simple).pack(side=tk.LEFT)
        make_secondary_button(btn_frame, text="复制内容",
                              command=self._copy_simple).pack(side=tk.LEFT, padx=6)

        # 右侧预览
        preview_card = Card(outer, padding=10)
        preview_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        make_label(preview_card.inner, text="预览", font=F["h2"],
                   bg=C["bg_card"]).pack(fill=tk.X, pady=(0, 4))
        self._preview_text = make_text(preview_card.inner, height=15, font=F["mono"],
                                        fg=C["fg"], state=tk.DISABLED, wrap=tk.WORD)
        self._preview_text.pack(fill=tk.BOTH, expand=True)

        self._update_preview()

        for var in (self._org_var, self._type_var, self._subject_var):
            var.trace_add("write", lambda *_: self._update_preview())
        self._content_text.bind("<KeyRelease>", lambda e: self._update_preview())
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

    def _gen_simple(self):
        org = self._org_var.get().strip()
        doc_type = self._type_var.get()
        subject = self._subject_var.get().strip()
        content = self._content_text.get("1.0", tk.END).strip()
        now = datetime.datetime.now()
        doc_number = f"〔{now.year}〕第{now.month}{now.day}号"

        lines = [
            f"# {org}\n",
            f"## {'文' if doc_type == '通知' else ''}{doc_type}\n",
            f"**{org}文件**\n",
            f"**{org}** · {doc_number}\n",
            "---\n",
            f"# {subject}\n",
        ]
        if content:
            lines.append(content)
        else:
            lines.extend([
                "各省、自治区、直辖市有关部门：\n",
                "为贯彻落实党中央、国务院决策部署，现就有关事项通知如下：\n",
                "一、提高思想认识，充分领会工作重要性。\n",
                "二、加强组织领导，确保各项措施落实到位。\n",
                "三、强化监督检查，建立健全长效机制。\n",
                "各地区、各部门要认真贯彻执行，遇到重要情况及时报告。\n",
            ])
        lines.extend(["\n---\n", f"**{org}**", f"{now.year}年{now.month}月{now.day}日"])
        return "\n".join(lines)

    def _update_preview(self):
        result = self._gen_simple()
        self._preview_text.config(state=tk.NORMAL)
        self._preview_text.delete("1.0", tk.END)
        self._preview_text.insert("1.0", result)
        self._preview_text.config(state=tk.DISABLED)

    def _export_simple(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("所有文件", "*.*")],
            title="导出公文")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._gen_simple())
            messagebox.showinfo("成功", f"已导出至:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _copy_simple(self):
        self.clipboard_clear()
        self.clipboard_append(self._gen_simple())
        flash_title(self, "✓ 已复制")

    def _copy_text(self, widget):
        text = widget.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            flash_title(self, "✓ 已复制")
