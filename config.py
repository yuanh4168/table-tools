"""配置管理 — 读写 config.ini（支持打包后 exe 同目录）"""

import configparser
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_cache: configparser.ConfigParser | None = None


def resource_path(relative_path: str) -> str:
    """返回资源文件的绝对路径，支持打包后的 exe 同目录查找"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境：exe 所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：当前文件所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


CONFIG_PATH = resource_path("config.ini")


def _ensure_config():
    """确保 config.ini 存在，若不存在则创建默认配置"""
    if not os.path.exists(CONFIG_PATH):
        template = """[AI]
api_url = https://integrate.api.nvidia.com/v1/chat/completions
api_key = 
model = meta/llama-3.1-70b-instruct

[chat]
api_url = 
api_key = 
model = 
window_mode = new

[news]
window_mode = new
source = 原版

[translate]
engine = mymemory
window_mode = new

[stone]
width = 60
height = 30
count = 120

[document]
org = 厦门市教育局
type = 通知
window_mode = new

[mc-ping]
host = fm.rainplay.cn
port = 25065
notify_threshold = 5
window_mode = new

[chess]
ai = false
window_mode = new

[prompt]
template = 
window_mode = new

[project-tree]
output = .
window_mode = new

[mc_ping]
window_mode = new
"""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(template)


def _load() -> configparser.ConfigParser:
    global _cache
    if _cache is None:
        _ensure_config()  # 确保配置文件存在
        _cache = configparser.ConfigParser()
        _cache.read(CONFIG_PATH, encoding="utf-8")
    return _cache


def _save():
    cfg = _load()
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)
    except Exception:
        pass


def cfg_str(section: str, key: str, fallback: str = "") -> str:
    try:
        return _load().get(section, key, fallback=fallback)
    except Exception:
        return fallback


def cfg_int(section: str, key: str, fallback: int = 0) -> int:
    try:
        return _load().getint(section, key, fallback=fallback)
    except Exception:
        return fallback


def cfg_bool(section: str, key: str, fallback: bool = False) -> bool:
    try:
        return _load().getboolean(section, key, fallback=fallback)
    except Exception:
        return fallback


def set_cfg(section: str, key: str, value: str):
    cfg = _load()
    if section not in cfg:
        cfg[section] = {}
    cfg[section][key] = value
    _save()


def get_window_mode(key: str) -> str:
    mode = cfg_str(key, "window_mode", "new").strip().lower()
    return mode if mode in ("new", "replace") else "new"


def set_window_mode(key: str, mode: str):
    set_cfg(key, "window_mode", mode)


# 模块注册表
MODULE_KEYS = [
    "mc_ping", "translate", "chat", "news", "prompt", "project-tree"
]

MODULE_NAMES = {
    "mc_ping": "Minecraft 服务器",
    "translate": "翻译助手",
    "chat": "AI 对话",
    "news": "新闻简报",
    "document": "公文生成",
    "prompt": "提示词生成",
    "project-tree": "项目结构",
    "chess": "中国象棋",
}

MODULE_ICONS = {
    "mc_ping": "DEVICES",
    "translate": "TRANSLATE",
    "chat": "CHAT",
    "news": "NEWSPAPER",
    "document": "DESCRIPTION",
    "prompt": "ELECTRIC_BOLT",
    "project-tree": "ACCOUNT_TREE",
    "chess": "SPORTS_ESPORTS",
}

MODULE_DESC = {
    "mc_ping": "Minecraft Java Edition 服务器状态查询",
    "translate": "多引擎翻译（MyMemory / AI）",
    "chat": "兼容 OpenAI API 的 AI 对话",
    "news": "新闻简报（HN + RSS 多源抓取 + AI 分析）",
    "document": "红头公文 / 恩情文章 / 简易模板",
    "prompt": "AI 提示词模板生成",
    "project-tree": "项目目录结构输出",
    "chess": "中国象棋人机对战",
}