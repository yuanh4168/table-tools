"""
 AI 对话  兼容 OpenAI API 的命令行对话。
从 ai-chat / cc-haha-noapi / ait 移植  简洁的终端 AI 对话。
"""

# requests 在函数内延迟导入


def run(api_url, api_key, model):
    """启动交互式 AI 对话。"""
    if not api_key:
        print("\n    未设置 API 密钥!")
        print("  设置环境变量 AI_API_KEY 或在参数中传入 --api-key")
        print("  或使用: export AI_API_KEY=your_key (Linux/Mac)")
        print("  或使用: set AI_API_KEY=your_key (Windows)\n")
        return

    print("\n   AI 对话启动")
    print(f"   模型: {model}")
    print("   输入 /help 查看命令, /exit 退出\n")

    messages = [
        {"role": "system", "content": "你是一个有用的助手。用中文回答，简洁直接。"}
    ]

    while True:
        try:
            user_input = input("   > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("  再见！")
            break
        elif user_input.lower() == "/help":
            print("   命令列表:")
            print("    /exit     退出对话")
            print("    /clear    清空对话历史")
            print("    /help     显示帮助")
            continue
        elif user_input.lower() == "/clear":
            messages = messages[:1]
            print("   对话历史已清空\n")
            continue
        elif user_input.lower() == "/debug":
            print("   配置信息:")
            print(f"     API: {api_url}")
            print(f"     Model: {model}")
            print(f"     消息数: {len(messages)}")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            import requests
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            resp = requests.post(api_url, json=payload, headers=headers, timeout=120)
            data = resp.json()

            if resp.status_code != 200:
                error_msg = data.get("error", {}).get("message", str(data))
                print(f"   API 错误 ({resp.status_code}): {error_msg}\n")
                messages.pop()
                continue

            content = data["choices"][0]["message"]["content"]
            print(f"   > {content}\n")
            messages.append({"role": "assistant", "content": content})

        except requests.exceptions.Timeout:
            print("   请求超时，请检查网络\n")
            messages.pop()
        except Exception as e:
            print(f"   错误: {e}\n")
            messages.pop()
