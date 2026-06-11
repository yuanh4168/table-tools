"""
 新闻简报  抓取各平台新闻标题，生成简报。
从 Daily Boot Chronicle 移植 -- 支持 HN 抓取 + AI 分析简报。
"""

from datetime import datetime

# requests 在函数内延迟导入


def fetch_hn_headlines(limit=10):
    """从 Hacker News API 获取标题。"""
    import requests
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


def ai_analyze(headlines, api_url, api_key, model):
    """调用 AI 分析新闻标题并生成简报。"""
    import requests
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
                            "content": f"以下是 {today} 的 Hacker News 热门标题，请分析并生成简报：\n\n{news_text}",
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
    source="china",
    analyze=False,
    api_url="https://integrate.api.nvidia.com/v1/chat/completions",
    api_key="",
    model="qwen/qwen3-coder-480b-a35b-instruct",
):
    """抓取并打印新闻简报，可选 AI 分析。"""
    today = datetime.now().strftime("%Y-%m-%d %A")
    print(f"\n   今日新闻简报  {today}")
    print(f"  {'=' * 40}\n")

    headlines = fetch_hn_headlines(count)

    label = {"china": "综合热点", "global": "全球热点", "tech": "科技热点"}.get(
        source, "综合热点"
    )
    print(f"   {label} (Hacker News):")
    for i, title in enumerate(headlines, 1):
        print(f"  {i:>2}. {title}")

    print(f"\n  {'=' * 40}")
    print(f"  来源: Hacker News | 共 {len(headlines)} 条")
    print()

    if analyze and api_key:
        print("  [AI 简报分析中...]\n")
        result = ai_analyze(headlines, api_url, api_key, model)
        print(f"  {'=' * 40}")
        print("   AI 分析简报")
        print(f"  {'=' * 40}")
        print(f"\n  {result}\n")
