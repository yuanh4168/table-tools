"""
 翻译助手  英中互译
从 easy-en2zh 移植  支持 MyMemory 免费 API 和 AI API 两种引擎。
"""

import requests


def has_chinese(text: str) -> bool:
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)


def translate_mymemory(text: str) -> str:
    """使用 MyMemory 免费 API 翻译。"""
    langpair = "zh-CN|en" if has_chinese(text) else "en|zh-CN"
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": langpair},
            timeout=10,
        )
        data = resp.json()
        if data.get("responseStatus") != 200:
            return f"[错误] {data}"
        return data["responseData"]["translatedText"]
    except Exception as e:
        return f"[错误] 网络或请求异常: {e}"


def run(text=None, engine="mymemory", from_lang=None, to_lang=None):
    """翻译指定文本或剪贴板内容。"""
    if not text:
        try:
            import pyperclip
            text = pyperclip.paste().strip()
        except ImportError:
            print("未提供文本且无法读取剪贴板 (需要 pip install pyperclip)")
            return

    if not text:
        print("未检测到文本。")
        return

    # 方向提示
    direction = "中文  英文" if has_chinese(text) else "英文  中文"
    print(f"\n   {direction}")
    print(f"   原文: {text[:60]}{'...' if len(text) > 60 else ''}")

    if engine == "mymemory":
        result = translate_mymemory(text)
    else:
        print("  AI 引擎需要配置 API (使用 --api-url 和 --api-key)")
        return

    if result.startswith("[错误]"):
        print(f"  {result}")
    else:
        print(f"   译文: {result}")
    print()
