"""
 ASCII 石头艺术生成器
从 stone.py 移植  模拟石头生长过程，用 ASCII 字符描绘带边缘的石头纹理。
"""

import random


def smooth_stone(grid, height, width, iterations=1):
    """移除孤立的小毛刺（3x3 邻域内石头少于 3 个的移除）。"""
    for _ in range(iterations):
        new_grid = [row[:] for row in grid]
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                if grid[r][c] == 0:
                    continue
                cnt = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if grid[r + dr][c + dc] == 1:
                            cnt += 1
                if cnt <= 3:
                    new_grid[r][c] = 0
        grid[:] = new_grid
    return grid


def render(height, width, grid):
    """根据石头格子的邻域关系，选择不同字符描绘边缘。"""
    out = [[" " for _ in range(width)] for _ in range(height)]

    for r in range(height):
        for c in range(width):
            if grid[r][c] != 1:
                continue

            up = (r - 1 >= 0 and grid[r - 1][c] == 1)
            down = (r + 1 < height and grid[r + 1][c] == 1)
            left = (c - 1 >= 0 and grid[r][c - 1] == 1)
            right = (c + 1 < width and grid[r][c + 1] == 1)
            n4 = up + down + left + right

            if n4 == 4:
                out[r][c] = "#"
            elif n4 == 3:
                if not up and down and left and right:
                    out[r][c] = "-"
                elif up and not down and left and right:
                    out[r][c] = "-"
                elif up and down and not left and right:
                    out[r][c] = "|"
                elif up and down and left and not right:
                    out[r][c] = "|"
                else:
                    out[r][c] = "#"
            elif n4 == 2:
                if (up and down) and not (left or right):
                    out[r][c] = "|"
                elif (left and right) and not (up or down):
                    out[r][c] = "-"
                elif (up and left) or (down and right):
                    out[r][c] = "/"
                elif (up and right) or (down and left):
                    out[r][c] = "\\"
                else:
                    out[r][c] = "#"
            elif n4 == 1:
                up_left = (r - 1 >= 0 and c - 1 >= 0 and grid[r - 1][c - 1] == 1)
                up_right = (r - 1 >= 0 and c + 1 < width and grid[r - 1][c + 1] == 1)
                down_left = (r + 1 < height and c - 1 >= 0 and grid[r + 1][c - 1] == 1)
                down_right = (r + 1 < height and c + 1 < width and grid[r + 1][c + 1] == 1)

                if (up_left and not up and not left) or (down_right and not down and not right):
                    out[r][c] = "/"
                elif (up_right and not up and not right) or (down_left and not down and not left):
                    out[r][c] = "\\"
                else:
                    out[r][c] = "*"
            else:
                out[r][c] = ""

    for row in out:
        print("".join(row))


def run(width=60, height=30, target_count=120):
    """生成并打印 ASCII 石头艺术。"""
    if width < 5 or height < 5:
        print("[错误] 画布尺寸太小 (最小 5x5)")
        return

    max_iter = width * height * 2
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # 种子
    center_r, center_c = height // 2, width // 2
    grid[center_r][center_c] = 1
    stone_count = 1

    # 候选集
    candidates = set()
    def _try_add(r, c):
        if 0 <= r < height and 0 <= c < width and grid[r][c] == 0:
            candidates.add((r, c))
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        _try_add(center_r + dr, center_c + dc)

    # 生长
    iteration = 0
    while stone_count < target_count and iteration < max_iter and candidates:
        iteration += 1
        r, c = random.choice(list(candidates))
        progress = stone_count / target_count
        dr = r - center_r
        dc = c - center_c
        dir_factor = 1.9 if abs(dc) > abs(dr) else 0.95
        age_factor = 1.0 - 0.2 * progress
        prob = 0.5 * age_factor * dir_factor
        prob = max(0.0, min(1.0, prob))

        if random.random() < prob:
            grid[r][c] = 1
            stone_count += 1
            candidates.remove((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                _try_add(r + dr, c + dc)

    # 平滑
    smooth_stone(grid, height, width, iterations=1)

    # 输出
    print(f"\n  【石头艺术】{stone_count} 块石头 | {width}x{height} 画布 | {iteration} 次迭代\n")
    render(height, width, grid)
    print()

    return grid
