"""配置管理 — 读写 config.ini"""

import configparser
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

_cache: configparser.ConfigParser | None = None


def _load() -> configparser.ConfigParser:
    global _cache
    if _cache is None:
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
    "news": "Hacker News 热门抓取 + AI 分析",
    "document": "红头公文 / 恩情文章 / 简易模板",
    "prompt": "AI 提示词模板生成",
    "project-tree": "项目目录结构输出",
    "chess": "中国象棋人机对战",
}
