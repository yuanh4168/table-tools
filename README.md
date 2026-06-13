# table-tools — 桌面工具集

> 将零散桌面小工具整合为统一 CLI + 双 GUI（Tkinter / Flet）工具包。  
> Python 实现，轻量无侵入，开箱即用。

---

## 功能一览

| 模块 | CLI | Tkinter GUI | Flet GUI | 说明 |
|------|:---:|:---:|:---:|------|
| **Minecraft 服务器查询** | ✅ | ✅ | ✅ | SRV解析、延迟、MOTD、玩家列表 |
| **中国象棋** | ✅ | ✅ | ✅ | 终端 / Tkinter / Flet 三端棋盘 |
| **翻译助手** | ✅ | ✅ | ✅ | MyMemory 免费 API 英中互译 |
| **AI 对话** | ✅ | ✅ | ✅ | OpenAI 兼容 API（默认 NVIDIA NIM） |
| **新闻简报** | ✅ | ✅ | ✅ | Hacker News 热门 + AI 分析 |
| **公文生成** | ✅ | ✅ | ✅ | 红头文件 / 恩情文章 / 简易模板 |
| **提示词生成** | ✅ | ✅ | ✅ | AI 提示词结构化模板 |
| **项目结构生成** | ✅ | ✅ | ✅ | 从 tree 文本创建目录/文件 |
| **石头艺术** | ✅ | ❌ | ❌ | ASCII 石头生长模拟 |

---

## 快速开始

### 环境要求
- Python 3.10+
- Windows / Linux / macOS

### 安装

```bash
git clone <repo-url>
cd table-tools
pip install -r requirements.txt