#!/usr/bin/env python3
"""table-tools: 桌面工具集 CLI -- 整合所有零散项目为统一命令行工具。"""

import argparse
import configparser
import os
import shlex
import sys

# Windows 终端 UTF-8 支持
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 导入所有模块（放在 sys.path 调整后，加 noqa 抑制 E402）
import modules.stone as mod_stone  # noqa: E402
import modules.translate as mod_translate  # noqa: E402
import modules.document as mod_document  # noqa: E402
import modules.news as mod_news  # noqa: E402
import modules.chess as mod_chess  # noqa: E402
import modules.chat as mod_chat  # noqa: E402
import modules.prompt_gen as mod_prompt  # noqa: E402
import modules.mc_ping as mod_mc_ping  # noqa: E402
import modules.project_tree as mod_project_tree  # noqa: E402


def _load_config() -> configparser.ConfigParser:
    """加载 config.ini，文件不存在时返回空配置。"""
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(BASE_DIR, "config.ini"), encoding="utf-8")
    return cfg


def _cfg(cfg: configparser.ConfigParser, section: str, key: str, fallback: str = "") -> str:
    """安全地从配置读取字符串值。"""
    try:
        return cfg.get(section, key, fallback=fallback)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return fallback


def _cfgint(cfg: configparser.ConfigParser, section: str, key: str, fallback: int = 0) -> int:
    """安全地从配置读取整数值。"""
    try:
        return cfg.getint(section, key, fallback=fallback)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        return fallback


def _cfgbool(cfg: configparser.ConfigParser, section: str, key: str, fallback: bool = False) -> bool:
    """安全地从配置读取布尔值。"""
    try:
        return cfg.getboolean(section, key, fallback=fallback)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        return fallback


def build_parser(cfg: configparser.ConfigParser | None = None) -> argparse.ArgumentParser:
    """构建参数解析器。"""
    if cfg is None:
        cfg = configparser.ConfigParser()

    ai_url = _cfg(cfg, "AI", "api_url",
                  os.environ.get("AI_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions"))
    ai_key = _cfg(cfg, "AI", "api_key",
                  os.environ.get("AI_API_KEY", ""))
    ai_model = _cfg(cfg, "AI", "model",
                    os.environ.get("AI_MODEL", "qwen/qwen3-coder-480b-a35b-instruct"))

    parser = argparse.ArgumentParser(
        prog="table-tools",
        description="桌面工具集 -- 将桌面零散小工具整合为统一 CLI",
        epilog="直接运行进入交互模式 | 使用 table-tools <命令> --help 查看各命令详细用法",
    )
    parser.add_argument("--version", action="version", version="table-tools v1.0.0")

    sub = parser.add_subparsers(dest="command", help="可用命令")

    p_stone = sub.add_parser("stone", help="ASCII 石头艺术生成")
    p_stone.add_argument("--width", type=int, default=_cfgint(cfg, "stone", "width", 60), help="画布宽度")
    p_stone.add_argument("--height", type=int, default=_cfgint(cfg, "stone", "height", 30), help="画布高度")
    p_stone.add_argument("--count", type=int, default=_cfgint(cfg, "stone", "count", 120), help="目标石头数量")

    p_trans = sub.add_parser("translate", help="文本翻译 (英中互译)")
    p_trans.add_argument("text", nargs="?", help="要翻译的文本 (不提供则从剪贴板读取)")
    p_trans.add_argument("--engine", choices=["mymemory", "ai"],
                         default=_cfg(cfg, "translate", "engine", "mymemory"), help="翻译引擎")

    p_doc = sub.add_parser("document", help="公文/红头文件模板生成")
    p_doc.add_argument("--org", default=_cfg(cfg, "document", "org", "厦门市教育局"), help="发文单位")
    p_doc.add_argument("--type", default=_cfg(cfg, "document", "type", "通知"),
                       choices=["通知", "通报", "决定", "批复"], help="文件类型")
    p_doc.add_argument("--subject", default="关于...的通知", help="文件标题")
    p_doc.add_argument("--content", default="", help="正文内容 (支持 Markdown)")
    p_doc.add_argument("--output", "-o", help="输出文件路径 (默认打印到终端)")

    p_news = sub.add_parser("news", help="抓取今日新闻简报")
    p_news.add_argument("--count", type=int, default=_cfgint(cfg, "news", "count", 10), help="新闻条数")
    p_news.add_argument("--source",
                        choices=mod_news.SOURCE_CHOICES,
                        default=_cfg(cfg, "news", "source", "原版"), help="新闻来源 (原版/订阅/综合)")
    p_news.add_argument("--analyze", action="store_true",
                        default=_cfgbool(cfg, "news", "analyze", False), help="启用 AI 分析简报")
    p_news.add_argument("--api-url", default=ai_url, help="AI API 地址 (默认使用 [AI] 节)")
    p_news.add_argument("--api-key", default=ai_key, help="AI API 密钥 (默认使用 [AI] 节)")
    p_news.add_argument("--model", default=ai_model, help="AI 模型 (默认使用 [AI] 节)")

    p_chess = sub.add_parser("chess", help="中国象棋 (终端 ASCII 版)")
    p_chess.add_argument("--ai", action="store_true", default=_cfgbool(cfg, "chess", "ai", False), help="启用 AI 对手")

    p_chat = sub.add_parser("chat", help="AI 对话 (兼容 OpenAI API)")
    p_chat.add_argument("--api-url", default=_cfg(cfg, "chat", "api_url", ai_url), help="API 地址")
    p_chat.add_argument("--api-key", default=_cfg(cfg, "chat", "api_key", ai_key), help="API 密钥")
    p_chat.add_argument("--model", default=_cfg(cfg, "chat", "model", ai_model), help="模型名称")

    p_prompt = sub.add_parser("prompt", help="AI 提示词模板生成器")
    p_prompt.add_argument("desc", nargs="?", help="项目描述")
    p_prompt.add_argument("--template", default=_cfg(cfg, "prompt", "template", ""), help="自定义模板文件 (JSON)")
    p_prompt.add_argument("--output", "-o", help="输出到文件")

    p_mc = sub.add_parser("mc-ping", help="Minecraft 服务器状态查询")
    p_mc.add_argument("host", nargs="?", default=_cfg(cfg, "mc-ping", "host", ""), help="服务器地址")
    p_mc.add_argument("--port", type=int, default=_cfgint(cfg, "mc-ping", "port", 25565), help="端口")

    p_tree = sub.add_parser("project-tree", help="项目结构生成器 (从目录树文本创建)")
    p_tree.add_argument("--input", "-i", help="目录树文本文件路径")
    p_tree.add_argument("--output", "-o", default=_cfg(cfg, "project-tree", "output", "."), help="目标根目录")
    p_tree.add_argument("--dry-run", action="store_true", help="仅预览不创建")

    # GUI 模式
    sub.add_parser("gui", help="启动图形界面启动器")

    return parser


def dispatch(args: argparse.Namespace) -> None:
    """根据解析后的参数路由到对应模块。"""
    cmd = args.command
    if cmd == "gui":
        try:
            from gui import main as gui_main
            gui_main()
        except Exception as e:
            print(f"  GUI 启动失败: {e}")
            print("  请确保已安装 tkinter (Python 内置)")
        return
    elif cmd == "stone":
        mod_stone.run(args.width, args.height, args.count)
    elif cmd == "translate":
        mod_translate.run(args.text, args.engine)
    elif cmd == "document":
        mod_document.run(args.org, args.type, args.subject, args.content, args.output)
    elif cmd == "news":
        mod_news.run(args.count, args.source, args.analyze,
                     args.api_url, args.api_key, args.model)
    elif cmd == "chess":
        mod_chess.run(args.ai)
    elif cmd == "chat":
        mod_chat.run(args.api_url, args.api_key, args.model)
    elif cmd == "prompt":
        mod_prompt.run(args.desc, args.template, args.output)
    elif cmd == "mc-ping":
        if not args.host:
            print("  未指定服务器地址。请在 config.ini 中设置 [mc-ping] host，或直接传参。")
            return
        mod_mc_ping.run(args.host, args.port)
    elif cmd == "project-tree":
        mod_project_tree.run(args.input, args.output, args.dry_run)


def interactive_loop(parser: argparse.ArgumentParser) -> None:
    """交互式主循环 -- 持续接受用户输入并执行命令。"""
    banner = r"""
  _                    _             _
 | |_ ___ _ __ ___  __| | ___  _ __ | |_
 | __/ _ \ '__/ _ \/ _` |/ _ \| '_ \| __|
 | ||  __/ | |  __/ (_| | (_) | | | | |_
  \__\___|_|  \___|\__,_|\___/|_| |_|\__|
    """
    print(banner)
    print("  table-tools 桌面工具集 -- 交互模式")
    print("  " + "-" * 40)
    print("  直接输入命令名启动, 例如: stone")
    print("  可带参数覆盖配置:   stone --width 80")
    print("  输入 help    查看所有命令")
    print("  输入 exit    退出")
    print()

    while True:
        try:
            line = input("table> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not line:
            continue
        if line in ("exit", "quit", "q"):
            print("再见!")
            break
        if line == "help":
            parser.print_help()
            print()
            continue

        try:
            argv = shlex.split(line)
        except ValueError as e:
            print(f"解析错误: {e}")
            continue

        try:
            args = parser.parse_args(argv)
        except SystemExit:
            continue

        if args.command:
            dispatch(args)
            print()


def main(argv: list[str] | None = None) -> None:
    cfg = _load_config()
    parser = build_parser(cfg)

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        interactive_loop(parser)
        return

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch(args)


if __name__ == "__main__":
    main()
