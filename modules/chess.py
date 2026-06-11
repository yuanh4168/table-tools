"""
  中国象棋  终端 ASCII 版
从 xiangqi 移植  命令行人机对弈，支持 AI 对手。
"""



# ====== 棋子与棋盘常量 ======
EMPTY = "．"
PIECES = {
    "R": "车", "N": "马", "B": "象", "A": "仕", "K": "帅", "C": "炮", "P": "兵",
    "r": "車", "n": "馬", "b": "相", "a": "士", "k": "將", "c": "砲", "p": "卒",
}

INIT_BOARD = [
    ["r", "n", "b", "a", "k", "a", "b", "n", "r"],
    [EMPTY] * 9,
    [EMPTY, "c", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, "c", EMPTY],
    ["p", EMPTY, "p", EMPTY, "p", EMPTY, "p", EMPTY, "p"],
    [EMPTY] * 9,
    [EMPTY] * 9,
    ["P", EMPTY, "P", EMPTY, "P", EMPTY, "P", EMPTY, "P"],
    [EMPTY, "C", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, "C", EMPTY],
    [EMPTY] * 9,
    ["R", "N", "B", "A", "K", "A", "B", "N", "R"],
]


def display_board(board):
    """在终端绘制棋盘。"""
    top = "  " + chr(0x250C) + chr(0x2500) * 25 + chr(0x2510)
    print(top)
    for i, row in enumerate(board):
        cells = []
        for cell in row:
            cells.append(PIECES.get(cell, cell))
        line = " ".join(cells)
        sep = chr(0x2502)
        if i == 0:
            print(f"9 {sep}{line}{sep}")
        elif i == 9:
            print(f"0 {sep}{line}{sep}")
        else:
            print(f"{9 - i} {sep}{line}{sep}")
    bottom = "  " + chr(0x2514) + chr(0x2500) * 25 + chr(0x2518)
    print(bottom)
    col_headers = "    a b c d e g h i j"
    print(col_headers)
    print()


def parse_move(move_str):
    """解析用户输入如 'a2a4'  ((0,1), (2,1))。"""
    move_str = move_str.strip().lower()
    if len(move_str) < 4:
        return None
    col_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "g": 5, "h": 6, "i": 7, "j": 8}
    try:
        x1 = col_map[move_str[0]]
        y1 = 9 - int(move_str[1])
        x2 = col_map[move_str[2]]
        y2 = 9 - int(move_str[3])
        return (y1, x1), (y2, x2)
    except (KeyError, ValueError, IndexError):
        return None


def is_valid_move(board, from_pos, to_pos, is_red_turn):
    """简单合法性检查。"""
    y1, x1 = from_pos
    y2, x2 = to_pos
    piece = board[y1][x1]
    if piece == EMPTY:
        return False
    is_red = piece.isupper()
    if is_red != is_red_turn:
        return False
    target = board[y2][x2]
    if target != EMPTY:
        target_is_red = target.isupper()
        if target_is_red == is_red:
            return False
    return True


def make_move(board, from_pos, to_pos):
    """执行走棋并返回新棋盘。"""
    y1, x1 = from_pos
    y2, x2 = to_pos
    new_board = [row[:] for row in board]
    new_board[y2][x2] = new_board[y1][x1]
    new_board[y1][x1] = EMPTY
    return new_board


def ai_move(board, is_red_turn):
    """简单 AI：随机走一步合法棋。"""
    import random
    pieces = []
    for y in range(10):
        for x in range(9):
            p = board[y][x]
            if p != EMPTY:
                is_red = p.isupper()
                if is_red == is_red_turn:
                    pieces.append((y, x, p))

    random.shuffle(pieces)
    for y1, x1, p in pieces:
        # 尝试邻近格子
        for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            y2, x2 = y1 + dy, x1 + dx
            if 0 <= y2 < 10 and 0 <= x2 < 9:
                if is_valid_move(board, (y1, x1), (y2, x2), is_red_turn):
                    return (y1, x1), (y2, x2)
    return None


def run(ai_enabled=False):
    """启动终端象棋游戏。"""
    board = [row[:] for row in INIT_BOARD]
    is_red_turn = True
    move_count = 0

    print()
    print("    中国象棋 (终端版)")
    print("  " + "-" * 30)
    print("  输入走法如: a2a4 (列字母+行数字)")
    print("  输入 'q' 退出\n")

    while True:
        display_board(board)
        turn_label = "红方 (大写)" if is_red_turn else "黑方"
        print(f"  第 {move_count + 1} 手  {turn_label}走棋")

        if ai_enabled and not is_red_turn:
            # AI 走棋
            print("  AI 思考中...")
            move = ai_move(board, is_red_turn)
            if not move:
                print("  AI 无棋可走，你赢了！")
                break
            (y1, x1), (y2, x2) = move
            piece_name = PIECES.get(board[y1][x1], board[y1][x1])
            print(f"  AI 走: {chr(97 + x1)}{9 - y1}  {chr(97 + x2)}{9 - y2} ({piece_name})")
            board = make_move(board, (y1, x1), (y2, x2))
            is_red_turn = not is_red_turn
            move_count += 1
            continue

        cmd = input("  > ").strip()
        if cmd.lower() == "q":
            print("  游戏结束。")
            break

        parsed = parse_move(cmd)
        if not parsed:
            print("   格式错误，请使用如 a2a4 格式\n")
            continue

        from_pos, to_pos = parsed
        if not is_valid_move(board, from_pos, to_pos, is_red_turn):
            print("   非法走法\n")
            continue

        y1, x1 = from_pos
        piece_name = PIECES.get(board[y1][x1], board[y1][x1])
        print(f"  {piece_name} {chr(97 + x1)}{9 - y1}  {chr(97 + to_pos[1])}{9 - to_pos[0]}")
        board = make_move(board, from_pos, to_pos)
        is_red_turn = not is_red_turn
        move_count += 1
