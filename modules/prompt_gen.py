"""
 AI 提示词模板生成器
从 YMC-toolkit 工具箱移植  根据项目描述生成结构化提示词。
"""

import json

DEFAULT_TEMPLATE = """# 项目：{project_name}

## 项目描述
{description}

## 技术栈要求
- 语言: Python 3.10+
- 框架: (按需选择)
- 数据库: (按需选择)

## 功能需求
1. (功能一)
2. (功能二)
3. (功能三)

## 输出要求
- 提供完整的可运行代码
- 包含必要的注释
- 遵循 PEP 8 规范

## 额外说明
{extra}
"""


def run(desc=None, template_path=None, output=None):
    """生成 AI 提示词模板。"""
    if not desc:
        print("\n   AI 提示词模板生成器")
        print("  " + "-" * 30)
        print("  请输入项目描述 (输入空行结束):")
        lines = []
        try:
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        desc = "\n".join(lines)

    if not desc.strip():
        print("  未输入描述。")
        return

    # 尝试从模板文件加载
    template = DEFAULT_TEMPLATE
    if template_path:
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                template = data.get("template", template)
        except Exception as e:
            print(f"    模板文件加载失败: {e}，使用默认模板")

    # 提取项目名
    project_name = desc.split("\n")[0].strip()[:40]
    if len(project_name) > 30:
        project_name = project_name[:30] + "..."

    content = template.format(
        project_name=project_name,
        description=desc,
        extra="请根据上述需求实现完整代码。",
    )

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   提示词已输出至: {output}")
    else:
        print()
        print("  " + "=" * 40)
        print(content)
        print("  " + "=" * 40)
        print()
