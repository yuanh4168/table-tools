"""
 新闻简报  抓取各平台新闻标题，生成简报。
从 Daily Boot Chronicle 移植 -- 支持 HN 抓取 + RSS 源 + AI 分析简报。
"""

import requests
import time
from datetime import datetime

# RSS 支持 (移植自 Daily Boot Chronicle)
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ============================================================
# RSS 新闻源配置 (移植自 Daily Boot Chronicle)
# ============================================================
RSS_SOURCES = {
    "sources": [
        {"url": "https://www.engadget.com/rss.xml", "name": "Engadget", "lang": "en"},
        {"url": "https://www.theverge.com/rss/index.xml", "name": "The Verge", "lang": "en"},
        {"url": "https://techcrunch.com/feed/", "name": "TechCrunch", "lang": "en"},
        {"url": "https://feeds.arstechnica.com/arstechnica/index", "name": "Ars Technica", "lang": "en"},
        {"url": "https://www.solidot.org/index.rss", "name": "Solidot", "lang": "zh"},
        {"url": "https://www.nhk.or.jp/rss/news/cat6.xml", "name": "NHK国际", "lang": "en"},
    ]
}

# 三个来源选项
# "原版" -> Hacker News
# "订阅" -> RSS 聚合
# "综合" -> Hacker News + RSS 聚合
SOURCE_CHOICES = ["原版", "订阅", "综合"]

RSS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_hn_headlines(limit=10):
    """从 Hacker News API 获取标题。"""
    try:
        top = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=15,
        )
        ids = top.json()[:limit]
        items = []
        for nid in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{nid}.json",
                timeout=10,
            )
            data = item.json()
            if data and data.get("title"):
                items.append(data["title"])
        return items
    except Exception as e:
        return [f"[抓取失败] {e}"]


def fetch_rss_headlines(limit=10):
    """从所有 RSS 源抓取新闻标题，返回综合列表。

    移植自 Daily Boot Chronicle 的 NewsFetcher。
    """
    if not HAS_FEEDPARSER:
        return ["[错误] 缺少 feedparser 库，请执行: pip install feedparser"]

    all_items = []
    for src in RSS_SOURCES["sources"]:
        try:
            resp = requests.get(
                src["url"],
                headers={"User-Agent": RSS_USER_AGENT},
                timeout=10,
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                if title:
                    all_items.append(title)
            time.sleep(0.2)
        except Exception:
            pass  # 静默跳过失败源

    # 去重
    seen = set()
    unique = []
    for title in all_items:
        key = title[:40]
        if key not in seen:
            seen.add(key)
            unique.append(title)

    return unique[:limit]


def fetch_headlines(count=10, source="原版"):
    """统一的新闻获取入口。"""
    count = max(count, 1)
    if source == "原版":
        return fetch_hn_headlines(count)
    elif source == "订阅":
        return fetch_rss_headlines(count)
    elif source == "综合":
        half = max(count // 2, 1)
        hn = fetch_hn_headlines(half)
        rss = fetch_rss_headlines(count - len(hn))
        result = hn + rss
        # 去重
        seen = set()
        unique = []
        for item in result:
            key = item[:40]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique[:count]
    return fetch_hn_headlines(count)


def ai_analyze(headlines, api_url, api_key, model):
    """调用 AI 分析新闻标题并生成简报。"""
    news_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(headlines))
    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = (
        "你是一个新闻分析助手。根据提供的新闻标题列表，生成一份简洁的今日简报，包括："
        "1) 今日热点概述（1-2句话），2) 各条新闻的简要归类分析。"
        "用中文回答，控制在300字以内。"
    )

    timeout = 120
    for attempt in range(2):
        try:
            resp = requests.post(
                api_url,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"以下是 {today} 的热门标题，请分析并生成简报：\n\n{news_text}",
                        },
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1024,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
            data = resp.json()
            if resp.status_code != 200:
                return f"[AI分析失败] {data.get('error', {}).get('message', str(data))}"
            return data["choices"][0]["message"]["content"]
        except requests.Timeout:
            if attempt == 0:
                continue
            return "[AI分析异常] 请求超时（120s），请稍后重试"
        except Exception as e:
            return f"[AI分析异常] {e}"
    return "[AI分析异常] 请求失败"


def run(
    count=10,
    source="原版",
    analyze=False,
    api_url="https://integrate.api.nvidia.com/v1/chat/completions",
    api_key="",
    model="qwen/qwen3-coder-480b-a35b-instruct",
):
    """抓取并打印新闻简报，可选 AI 分析。"""
    today = datetime.now().strftime("%Y-%m-%d %A")
    print(f"\n   今日新闻简报  {today}")
    print(f"  {'=' * 40}\n")

    if source not in SOURCE_CHOICES:
        source = "原版"
    headlines = fetch_headlines(count, source)

    print(f"  来源：{source}")
    for i, title in enumerate(headlines, 1):
        print(f"  {i:>2}. {title}")

    source_map = {"原版": "Hacker News", "订阅": "RSS", "综合": "原版 + RSS"}
    print(f"\n  {'=' * 40}")
    print(f"  来源: {source_map.get(source, source)} | 共 {len(headlines)} 条")
    print()

    if analyze and api_key:
        print("  [AI 简报分析中...]\n")
        result = ai_analyze(headlines, api_url, api_key, model)
        print(f"  {'=' * 40}")
        print("   AI 分析简报")
        print(f"  {'=' * 40}")
        print(f"\n  {result}\n")
