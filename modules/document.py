"""
 公文/红头文件模板生成器
从 More EnQing 移植  生成红头文件样式 Markdown 模板。
"""

import datetime
import os


def run(org, doc_type, subject, content, output):
    """生成红头文件风格 Markdown 文档。"""
    now = datetime.datetime.now()
    year = now.year
    doc_number = f"〔{year}〕第{now.month}{now.day}号"

    lines = []
    # 红头
    lines.append(f"# {org}\n")
    lines.append(f"## {'文' if doc_type == '通知' else ''}{doc_type}\n")
    lines.append(f"**{org}文件**")
    lines.append("")
    lines.append(f"**{org}** · {doc_number}\n")
    lines.append("---\n")

    # 标题
    lines.append(f"# {subject}\n")

    # 正文
    if content:
        lines.append(content)
    else:
        lines.append("各省、自治区、直辖市有关部门：\n")
        lines.append("为贯彻落实党中央、国务院决策部署，现就有关事项通知如下：\n")
        lines.append("一、提高思想认识，充分领会工作重要性。\n")
        lines.append("二、加强组织领导，确保各项措施落实到位。\n")
        lines.append("三、强化监督检查，建立健全长效机制。\n")
        lines.append("各地区、各部门要认真贯彻执行，遇到重要情况及时报告。\n")

    lines.append("\n---\n")
    lines.append(f"**{org}**")
    lines.append(f"{now.year}年{now.month}月{now.day}日\n")

    result = "\n".join(lines)

    if output:
        os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"   已输出至: {output}")
    else:
        print()
        print(result)
        print()
