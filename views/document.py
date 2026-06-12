"""公文生成器 — 完整 More EnQing 功能"""

import datetime
import os
import re
import tempfile
import threading
import flet as ft
from config import cfg_str
from views.common import (
    page_wrapper, glass_card, primary_button, secondary_button,
    text_input, dropdown, section_title,
)

# ==================== 核心函数（移植自 More EnQing）====================


def _call_ai_api(prompt):
    """调用 AI API 生成内容。"""
    import requests
    api_url = cfg_str("AI", "api_url",
                      "https://integrate.api.nvidia.com/v1/chat/completions")
    api_key = cfg_str("AI", "api_key", "")
    model = cfg_str("AI", "model", "qwen/qwen3-coder-480b-a35b-instruct")

    if not api_key:
        return "[错误] 请在 config.ini 中配置 AI API 密钥"
    try:
        resp = requests.post(api_url, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }, timeout=120)
        data = resp.json()
        if resp.status_code != 200:
            return f"[错误] {data.get('error', {}).get('message', str(data))}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[错误] {e}"


def _esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_red_prompt(org, doc_type, affair, doc_num, sign_unit, sign_date, min_words, table_req):
    final_doc_num = doc_num.strip() or f"〔{datetime.date.today().year}〕趣号"
    final_sign_unit = sign_unit.strip() or org
    final_date = sign_date.strip() or f"{datetime.date.today().year}年{datetime.date.today().month}月{datetime.date.today().day}日"
    table_text = "必须包含一个完整的信息表格" if table_req == "是" else "不强制要求表格"
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
        f"<<RED_START>>\n发文机关：{org}\n文号：{final_doc_num}\n"
        f"文件类型：{doc_type}\n标题：关于{affair}的{doc_type}\n"
        f"<<BODY_START>>\n（正文，严肃公文口吻，{table_text}）\n"
        f"<<BODY_END>>\n落款单位：{final_sign_unit}\n"
        f"成文日期：{final_date}\n（此件公开发布）\n<<RED_END>>"
    )


def parse_red_text(text):
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
    org, doc_num, title = data["org"], data["doc_num"], data["title"]
    body, sign_unit, sign_date = data["body"], data["sign_unit"], data["sign_date"]
    paragraphs = body.split("\n\n")
    body_html = "".join(f"<p>  {p.replace(chr(10), '<br>')}</p>"
                        for p in paragraphs if p.strip())
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:white;display:flex;justify-content:center;padding:30px 20px;font-family:'Times New Roman','仿宋',serif;}}
.document{{max-width:1000px;width:100%;background:white;padding:42px 40px 56px;}}
.red-header{{text-align:center;margin-bottom:18px;border-bottom:2px solid #b11e23;padding-bottom:14px;}}
.org-name{{font-size:2rem;font-weight:800;font-family:'黑体',sans-serif;color:#b11e23;}}
.title{{text-align:center;font-size:1.6rem;font-weight:600;margin:30px 0 24px;font-family:'黑体',sans-serif;}}
.content{{font-size:1rem;line-height:1.75;}}
.signature{{text-align:right;margin-top:56px;}}
.stamp{{color:#b11e23;margin-top:6px;}}
</style></head><body>
<div class="document">
<div class="red-header"><div class="org-name">{_esc(org)}</div><div class="doc-number">{_esc(doc_num)}</div></div>
<div class="title">{_esc(title)}</div>
<div class="content">{body_html}</div>
<div class="signature"><div>{_esc(sign_unit)}</div><div>{_esc(sign_date)}</div><div class="stamp">（此件公开发布）</div></div>
</div></body></html>"""


def build_eulogy_prompt(hero, deed, place, time, enable_img):
    p = place.strip() or "那片热土"
    t = time.strip() or "那个难忘的日子"
    img_inst = ""
    if enable_img == "是":
        img_inst = "在文章适当位置插入图片占位符 <<IMG: 描述>>，生成2-4个。"
    return (
        f"你是一位擅长夸张感恩文章的作者。根据以下信息输出恩情文章纯文本。\n\n"
        f"主角：{hero}\n事迹：{deed}\n地点：{p}\n时间：{t}\n"
        f"图片要求：{img_inst}\n\n"
        f"<<EULOGY_START>>\n标题：（含主角名字）\n"
        f"<<BODY_START>>\n（正文，夸张感人，400~800字）\n"
        f"<<BODY_END>>\n作者：一位被感动的见证者\n<<EULOGY_END>>"
    )


def parse_eulogy_text(text):
    return {
        "title": _extract(text, r"标题[：:]\s*(.+)", "恩情永存"),
        "body": _extract(text, r"<<BODY_START>>\s*([\s\S]*?)\s*<<BODY_END>>", "无正文"),
    }


def render_eulogy_html(data):
    title, body = data["title"], data["body"]
    processed = body.replace("<<IMG:", '<div class="img-ph">📷 ')
    processed = processed.replace(">>", '</div>')
    paragraphs = processed.split("\n\n")
    body_html = "".join(f"<p>  {p.replace(chr(10), '<br>')}</p>"
                        for p in paragraphs if p.strip())
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{background:#fef9ef;font-family:'Georgia','宋体',serif;padding:30px 20px;}}
.article{{max-width:800px;margin:0 auto;background:#fffef7;padding:40px 30px;border-radius:28px;}}
h1{{text-align:center;font-size:1.8rem;color:#b45f2b;}}
p{{text-indent:2em;margin-bottom:1.2em;line-height:1.7;}}
.img-ph{{border:2px dashed #c0392b;background:#fff0f0;padding:12px;margin:15px 0;border-radius:16px;text-align:center;}}
</style></head><body>
<div class="article"><h1>📖 {_esc(title)}</h1>{body_html}<p class="quote" style="text-align:center;margin-top:30px;">恩情似海，铭记于心</p></div></body></html>"""


def _extract(text, pattern, default=""):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


def _open_in_browser(html_content):
    try:
        fd, path = tempfile.mkstemp(suffix=".html", prefix="doc_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html_content)
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(path)}")
    except Exception as e:
        print(f"打开浏览器失败: {e}")


class DocumentView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._current_html = ""
        self._eulogy_html = ""

    def build(self):
        self._tab_index = 0
        tab_data = [("📄 红头公文", 0), ("📖 恩情文章", 1), ("📝 简易模板", 2)]
        tab_btns = []

        def make_tab_click(idx):
            def on_click(e):
                self._tab_index = idx
                for i, btn in enumerate(tab_btns):
                    btn.bgcolor = ft.Colors.PRIMARY_CONTAINER if i == idx else ft.Colors.TRANSPARENT
                    btn.update()
                self._red_content.visible = idx == 0
                self._eulogy_content.visible = idx == 1
                self._simple_content.visible = idx == 2
                self.page.update()
            return on_click

        for label, idx in tab_data:
            btn = ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.W_500),
                padding=ft.Padding(16, 8, 16, 8),
                border_radius=8,
                ink=True,
                bgcolor=ft.Colors.PRIMARY_CONTAINER if idx == 0 else None,
                on_click=make_tab_click(idx),
            )
            tab_btns.append(btn)

        tab_row = ft.Row(tab_btns, spacing=4)

        self._red_content = self._build_red_tab()
        self._eulogy_content = self._build_eulogy_tab()
        self._simple_content = self._build_simple_tab()
        self._eulogy_content.visible = False
        self._simple_content.visible = False

        c = ft.Column([
            section_title("公文生成器"),
            ft.Container(height=4),
            tab_row,
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            self._red_content,
            self._eulogy_content,
            self._simple_content,
        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        return page_wrapper(c)

    # ========== 红头公文 ==========

    def _build_red_tab(self):
        self._red_org = text_input(label="发文机关", value=cfg_str("document", "org", "厦门市教育局"))
        self._red_type = dropdown(label="文件类型", options=["通知", "通报", "决定", "批复"], value="通知")
        self._red_event = text_input(label="核心事由", value="加强数字化建设")
        self._red_num = text_input(label="文号", value=f"〔{datetime.date.today().year}〕号")
        self._red_sign = text_input(label="落款单位", value="")
        self._red_date = text_input(label="成文日期", value="")
        self._red_words = text_input(label="最低字数", value="800")
        self._red_table = dropdown(label="要求表格", options=["否", "是"], value="否")

        self._red_result = text_input(label="结果", multiline=True, height=300)
        self._red_result.read_only = True

        self._red_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        form = ft.Column([
            ft.Row([self._red_org, self._red_type], spacing=12),
            self._red_event,
            ft.Row([self._red_num, self._red_sign, self._red_date], spacing=12),
            ft.Row([self._red_words, self._red_table], spacing=12),
            ft.Row([
                primary_button("生成提示词", on_click=self._gen_red_prompt),
                secondary_button("🤖 AI 生成全文", on_click=self._gen_red_full),
                secondary_button("🌐 浏览器预览", on_click=self._preview_red_html),
                self._red_status,
            ], spacing=12, wrap=True),
        ], spacing=12)

        return ft.Row([
            glass_card(content=form, padding=16, width=600),
            glass_card(content=self._red_result, padding=16, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)

    def _gen_red_prompt(self, e=None):
        prompt = build_red_prompt(
            self._red_org.value, self._red_type.value, self._red_event.value,
            self._red_num.value, self._red_sign.value, self._red_date.value,
            self._red_words.value, self._red_table.value,
        )
        self._red_result.value = prompt
        self._red_result.read_only = False
        self._red_result.update()
        self._red_result.read_only = True
        self._red_status.value = "提示词已生成 ✓"
        self._red_status.color = ft.Colors.TERTIARY
        self._red_status.update()

    def _gen_red_full(self, e=None):
        prompt = build_red_prompt(
            self._red_org.value, self._red_type.value, self._red_event.value,
            self._red_num.value, self._red_sign.value, self._red_date.value,
            self._red_words.value, self._red_table.value,
        )
        self._red_result.value = "AI 生成中..."
        self._red_result.read_only = False
        self._red_result.update()
        self._red_result.read_only = True
        self._red_status.value = "AI 生成中..."
        self._red_status.color = ft.Colors.PRIMARY
        self._red_status.update()

        def worker():
            result = _call_ai_api(prompt)
            self.page.add(self._show_red_result(result))
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _show_red_result(self, result):
        self._red_result.value = result
        self._red_result.read_only = False
        self._red_result.update()
        self._red_result.read_only = True
        if not result.startswith("[错误]"):
            data = parse_red_text(result)
            self._current_html = render_red_html(data)
            self._red_status.value = "AI 生成完成 ✓ 可浏览器预览"
            self._red_status.color = ft.Colors.TERTIARY
        else:
            self._red_status.value = "生成失败"
            self._red_status.color = ft.Colors.ERROR
        self._red_status.update()
        return ft.Container()

    def _preview_red_html(self, e=None):
        if self._current_html:
            _open_in_browser(self._current_html)
        elif self._red_result.value and not self._red_result.value.startswith("AI"):
            data = parse_red_text(self._red_result.value)
            html = render_red_html(data)
            _open_in_browser(html)

    # ========== 恩情文章 ==========

    def _build_eulogy_tab(self):
        self._e_hero = text_input(label="主角", value="雷锋同志")
        self._e_deed = text_input(label="事迹", value="默默奉献")
        self._e_place = text_input(label="地点", value="")
        self._e_time = text_input(label="时间", value="")
        self._e_img = dropdown(label="图片占位", options=["否", "是"], value="否")

        self._e_result = text_input(label="结果", multiline=True, height=300)
        self._e_result.read_only = True
        self._e_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        form = ft.Column([
            ft.Row([self._e_hero, self._e_deed], spacing=12),
            ft.Row([self._e_place, self._e_time, self._e_img], spacing=12),
            ft.Row([
                primary_button("生成提示词", on_click=self._gen_eulogy_prompt),
                secondary_button("🤖 AI 生成全文", on_click=self._gen_eulogy_full),
                secondary_button("🌐 浏览器预览", on_click=self._preview_eulogy_html),
                self._e_status,
            ], spacing=12, wrap=True),
        ], spacing=12)

        return ft.Row([
            glass_card(content=form, padding=16, width=600),
            glass_card(content=self._e_result, padding=16, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)

    def _gen_eulogy_prompt(self, e=None):
        prompt = build_eulogy_prompt(
            self._e_hero.value, self._e_deed.value,
            self._e_place.value, self._e_time.value, self._e_img.value,
        )
        self._e_result.value = prompt
        self._e_result.read_only = False
        self._e_result.update()
        self._e_result.read_only = True
        self._e_status.value = "提示词已生成 ✓"
        self._e_status.color = ft.Colors.TERTIARY
        self._e_status.update()

    def _gen_eulogy_full(self, e=None):
        prompt = build_eulogy_prompt(
            self._e_hero.value, self._e_deed.value,
            self._e_place.value, self._e_time.value, self._e_img.value,
        )
        self._e_result.value = "AI 生成中..."
        self._e_result.read_only = False
        self._e_result.update()
        self._e_result.read_only = True
        self._e_status.value = "AI 生成中..."
        self._e_status.color = ft.Colors.PRIMARY
        self._e_status.update()

        def worker():
            result = _call_ai_api(prompt)
            self.page.add(self._show_eulogy_result(result))
            self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _show_eulogy_result(self, result):
        self._e_result.value = result
        self._e_result.read_only = False
        self._e_result.update()
        self._e_result.read_only = True
        if not result.startswith("[错误]"):
            data = parse_eulogy_text(result)
            self._eulogy_html = render_eulogy_html(data)
            self._e_status.value = "AI 生成完成 ✓"
            self._e_status.color = ft.Colors.TERTIARY
        else:
            self._e_status.value = "生成失败"
            self._e_status.color = ft.Colors.ERROR
        self._e_status.update()
        return ft.Container()

    def _preview_eulogy_html(self, e=None):
        if self._eulogy_html:
            _open_in_browser(self._eulogy_html)
        elif self._e_result.value and not self._e_result.value.startswith("AI"):
            data = parse_eulogy_text(self._e_result.value)
            html = render_eulogy_html(data)
            _open_in_browser(html)

    # ========== 简易模板 ==========

    def _build_simple_tab(self):
        self._s_org = text_input(label="发文单位", value=cfg_str("document", "org", "厦门市教育局"))
        self._s_type = dropdown(label="文件类型", options=["通知", "通报", "决定", "批复"], value="通知")
        self._s_subject = text_input(label="文件标题", value="关于...的通知")
        self._s_content = text_input(label="正文内容", multiline=True, height=150)

        self._s_preview = text_input(label="预览", multiline=True, height=300)
        self._s_preview.read_only = True
        self._s_status = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        def update_preview(e=None):
            self._s_preview.value = self._gen_simple()
            self._s_preview.read_only = False
            try:
                self._s_preview.update()
            except Exception:
                pass  # 控件未挂载时忽略
            self._s_preview.read_only = True

        for inp in [self._s_org, self._s_subject, self._s_content]:
            inp.on_change = update_preview

        form = ft.Column([
            ft.Row([self._s_org, self._s_type], spacing=12),
            self._s_subject,
            self._s_content,
            ft.Row([
                primary_button("导出文件", on_click=self._export_simple),
                secondary_button("复制内容", on_click=self._copy_simple),
                self._s_status,
            ], spacing=12),
        ], spacing=12)

        # 初始填充预览值
        self._s_preview.value = self._gen_simple()

        return ft.Row([
            glass_card(content=form, padding=16, width=500),
            glass_card(content=self._s_preview, padding=16, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)

    def _gen_simple(self):
        org = self._s_org.value.strip()
        doc_type = self._s_type.value
        subject = self._s_subject.value.strip()
        content = self._s_content.value.strip()
        now = datetime.datetime.now()
        doc_number = f"〔{now.year}〕第{now.month}{now.day}号"

        lines = [
            f"# {org}\n",
            f"## {'文' if doc_type == '通知' else ''}{doc_type}\n",
            f"**{org}文件**\n",
            f"**{org}** · {doc_number}\n---\n",
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

    def _export_simple(self, e=None):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("所有文件", "*.*")],
            title="导出公文")
        root.destroy()
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._gen_simple())
            self._s_status.value = "已导出 ✓"
            self._s_status.color = ft.Colors.TERTIARY
            self._s_status.update()
        except Exception as ex:
            self._s_status.value = f"导出失败: {ex}"
            self._s_status.color = ft.Colors.ERROR
            self._s_status.update()

    def _copy_simple(self, e=None):
        text = self._gen_simple()
        try:
            import pyperclip
            pyperclip.copy(text)
            self._s_status.value = "已复制 ✓"
            self._s_status.color = ft.Colors.TERTIARY
        except ImportError:
            self._s_status.value = "需要 pyperclip"
            self._s_status.color = ft.Colors.ERROR
        self._s_status.update()
