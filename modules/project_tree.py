"""
 项目结构生成器
从 YMC-toolkit 工具箱移植 -- 解析 tree /f 风格目录树，自动创建文件结构。
"""

import os
import re


def run(input_file=None, output_dir=".", dry_run=False):
    """从目录树文本创建项目结构。"""
    text = ""
    if input_file:
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f" 读取文件失败: {e}")
            return
    else:
        print("  项目结构生成器")
        print("  " + "-" * 30)
        print("  请输入目录树文本 (tree /f 格式，输入空行结束):")
        lines = []
        try:
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        text = "\n".join(lines)

    if not text.strip():
        print("  未输入内容。")
        return

    # 简单解析：提取所有路径
    entries = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 过滤掉 tree 图形字符行 (├ └ │ 等)
        if re.match(r"^[├└│]", stripped):
            clean = re.sub(r"[├─└│]", "", stripped).strip()
        else:
            clean = stripped
        if clean:
            entries.append(clean)

    print(f"\n  解析到 {len(entries)} 个条目\n")

    if dry_run:
        print("  预览 (--dry-run):")
        for entry in entries:
            print(f"    {'[DIR]' if entry.endswith('/') else '[FILE]'} {entry}")
        print()
        return

    created_files = 0
    created_dirs = 0

    for entry in entries:
        is_dir = entry.endswith("/")
        path = os.path.join(output_dir, entry.rstrip("/"))

        if is_dir:
            os.makedirs(path, exist_ok=True)
            created_dirs += 1
            print(f"  创建目录: {entry}")
        else:
            dirname = os.path.dirname(path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                print(f"  创建文件: {entry}")
                created_files += 1
            else:
                print(f"  已存在: {entry}")

    print(f"\n  完成: 创建 {created_dirs} 个目录, {created_files} 个文件")
    print(f"    目标路径: {os.path.abspath(output_dir)}\n")
