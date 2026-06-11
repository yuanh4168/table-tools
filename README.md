# table-tools — 桌面工具集

> 将零散桌面小工具整合为统一的 CLI + GUI 工具包。  
> Python 实现，轻量、无侵入，所有核心功能仅依赖 `requests`。

---

## 功能一览

| 命令 | 名称 | CLI | GUI | 说明 |
|------|------|:---:|:---:|------|
| `mc-ping` | Minecraft 服务器查询 | ✅ | ✅ | SRV 解析、延迟、MOTD、自定义 PNG 背景 |
| `chess` | 中国象棋 | ✅ | ✅ | Tkinter 棋盘、拖拽/点按、AI 对手 |
| `stone` | 石头艺术 | ✅ | 🟡 | ASCII 石头生长模拟 |
| `translate` | 翻译助手 | ✅ | 🟡 | 英中互译（MyMemory / AI） |
| `chat` | AI 对话 | ✅ | 🟡 | OpenAI 兼容 API 对话 |
| `news` | 新闻简报 | ✅ | 🟡 | Hacker News 抓取 + AI 分析 |
| `document` | 公文生成 | ✅ | 🟡 | 红头文件 Markdown 模板 |
| `prompt` | 提示词生成 | ✅ | 🟡 | AI 提示词结构化模板 |
| `project-tree` | 项目结构生成 | ✅ | 🟡 | 从 tree 文本创建项目 |

- ✅ 已完成  🟡 CLI only（GUI 启动器会提示使用终端）

---

## 快速开始

### 环境要求

- Python 3.10+
- Windows / Linux / macOS

### 安装

```bash
# 1. 克隆或下载本项目
git clone <repo-url> 或直接下载 ZIP

# 2. 进入目录
cd table-tools

# 3. 安装依赖（核心功能）
pip install -r requirements.txt

# 4. 开始使用
python cli.py --help          # 查看所有命令
python cli.py gui             # 启动图形界面
python gui.py                 # 同上

# Windows 快捷方式
run.bat --gui                 # GUI 模式
run.bat mc-ping               # CLI 模式
```

### 配置

编辑 `config.ini` 可设置各模块默认参数：

```ini
[mc-ping]
host = example.com
port = 25565

[chess]
ai = false

[AI]
api_key = your_api_key
```

命令行参数会覆盖配置文件中的设置。

---

## 📁 自定义图片系统

GUI 模式下，你可以将自己的 PNG 图片放入 `assets/` 目录来实现个性化 UI。

### 模块背景图

| 文件名 | 作用 |
|--------|------|
| `assets/launcher.png` | 主启动器背景 |
| `assets/mc_ping.png` | MC 服务器查询窗口背景 |
| `assets/chess.png` | 象棋窗口背景 |

图片会自动适应窗口大小（需要 Pillow 支持）。未提供图片时使用程序内置渲染。

**MC Ping 特别说明**：  
你可以在游戏中截图「多人游戏」服务器列表界面，保存为 `assets/mc_ping.png`，  
程序会将查询结果（MOTD、延迟、在线人数等）叠加渲染到图片的对应位置。

### 模块图标

| 文件名 | 作用 |
|--------|------|
| `assets/icon_mc_ping.png` | MC 查询按钮图标 |
| `assets/icon_chess.png` | 象棋按钮图标 |
| `assets/icon_stone.png` | 石头艺术按钮图标 |
| ... | 其余模块同理，64×64 px 推荐 |

> 💡 没有自定义图片时一切正常——程序会使用纯文本/Emoji 作为后备显示。

---

## CLI 用法速查

```bash
# Minecraft 服务器查询
python cli.py mc-ping                  # 使用 config.ini 中配置的服务器
python cli.py mc-ping mc.hypixel.net   # 指定服务器
python cli.py mc-ping example.com --port 25565

# 中国象棋
python cli.py chess            # 人机对战
python cli.py chess --ai       # AI 对手（终端 ASCII 版）

# 翻译
python cli.py translate "Hello world"
python cli.py translate        # 从剪贴板读取

# 新闻
python cli.py news --source tech --count 15 --analyze

# AI 对话
python cli.py chat --model gpt-4o

# 石头艺术
python cli.py stone --width 80 --height 40

# 公文生成
python cli.py document --org "XX公司" --subject "关于放假的通知"

# 提示词模板
python cli.py prompt "做一个待办事项管理应用"

# 从目录树文本重建项目结构
python cli.py project-tree -i tree.txt -o ./output

# 启动 GUI
python cli.py gui
```

---

## 项目结构

```
table-tools/
├── cli.py                 # CLI 入口（参数解析 + 路由）
├── gui.py                 # GUI 启动器（Tkinter 主窗口）
├── config.ini             # 配置文件
├── requirements.txt       # Python 依赖
├── run.bat                # Windows 快捷启动
├── README.md
├── assets/                # 用户自定义图片
│   ├── mc_ping.png        # MC 查询背景
│   ├── chess.png          # 象棋背景
│   ├── icon_*.png         # 模块图标（64×64）
│   └── ...
└── modules/
    ├── __init__.py
    ├── stone.py           # ASCII 石头艺术
    ├── translate.py       # 翻译引擎
    ├── document.py        # 公文模板
    ├── news.py            # 新闻简报
    ├── chess.py           # 终端中国象棋
    ├── chat.py            # AI 对话
    ├── prompt_gen.py      # 提示词模板
    ├── mc_ping.py         # MC 服务器查询（核心协议）
    ├── project_tree.py    # 项目结构生成
    ├── ui_common.py       # UI 通用组件（图片加载、背景）
    ├── ui_mc_ping.py      # MC 查询 GUI 窗口
    └── ui_chess.py        # 象棋 GUI 窗口
```

### 架构说明

- **CLI 层** (`cli.py`)：参数解析 → 路由到各模块的 `run()` 函数
- **GUI 层** (`gui.py`)：Tkinter 启动器 → 调用各 `ui_*.py` 模块的窗口
- **业务层** (`modules/*.py`)：纯逻辑，与 UI 无关，可被 CLI 和 GUI 共用
- **资源层** (`assets/`)：用户提供的 PNG 图片，可选

添加新模块只需：
1. 在 `modules/` 下创建业务逻辑文件（含 `run()` 函数）
2. 在 `cli.py` 中注册子命令
3. （可选）创建 `ui_*.py` 提供 GUI 窗口

---

## GUI 开发指南

### 图片背景系统

模块继承 `ImageBackgroundMixin` 即可获得自定义 PNG 背景支持：

```python
from modules.ui_common import ImageBackgroundMixin

class MyWindow(tk.Toplevel, ImageBackgroundMixin):
    MODULE_NAME = "my_module"  # 对应 assets/my_module.png

    def __init__(self):
        super().__init__()
        self.setup_bg(self, 600, 400)  # 自动加载背景图
        if self.using_custom_bg:
            # 使用自定义背景时的特殊渲染
            pass
```

### 添加新模块 UI

```python
# 1. 在 modules/ui_my_module.py 创建窗口类
class MyModuleWindow(tk.Toplevel):
    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        self.title("我的模块")
        # ... 构建 UI ...

# 2. 在 gui.py 中注册
from modules.ui_my_module import MyModuleWindow
UI_MODULES["my-module"] = ("显示名称", MyModuleWindow)

# 3. 添加到 MODULES 列表
MODULES = [
    # ...
    ("my-module", "🔧", "我的\n模块", UI_MODULES.get("my-module", (None, None))[1]),
]
```

### GUI 模块引用

当 GUI 需要调用模块的业务逻辑时，直接 import 对应的 `modules/*.py`：

```python
from modules import mc_ping as mod_mc_ping
result = mod_mc_ping.query("example.com", 25565)
# result 是 dict，包含 host, port, version, online, max, motd, latency, ...
```

所有 `query()` 函数设计为纯数据返回，不打印任何内容，适合 GUI 调用。

---

## 性能与体积

- **核心依赖仅 `requests`** — 安装体积 < 1MB
- **Pillow 完全可选** — 不安装则使用 Tkinter 内置 PNG 支持（基础功能）
- **GUI 使用 Tkinter** — Python 内置 GUI 库，零额外体积
- **非阻塞查询** — 网络请求使用线程，UI 不卡顿
- **源文件 < 200KB** — 全部代码不足 3000 行

---

## 开发贡献

### 编码风格

- Python 3.10+ type hints
- 模块独立，各模块间不互相引用
- 每个模块提供 `run()`（CLI 入口）和必要的纯数据函数（GUI 调用）
- GUI 窗口类以 `Window` 结尾

### 测试

```bash
python cli.py stone --width 40 --height 20
python cli.py mc-ping localhost
python cli.py translate "测试"
python cli.py gui
```

### 打包（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --name table-tools cli.py
# 或打包 GUI 版
pyinstaller --onefile --name table-tools-gui gui.py
```

---

## License

MIT
