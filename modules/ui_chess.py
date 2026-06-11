"""
中国象棋 — UI 版（Tkinter）
从 xiangqi 项目移植，支持拖拽/点按走棋、规则校验、AI 对战。
"""

import tkinter as tk
from tkinter import messagebox
import threading
import math
import os
import json
from modules.ui_common import (
    ImageBackgroundMixin, C, F,
    make_button,
)

# ==================== 常量 ====================
CELL = 116
MARGIN = 80
BOARD_W = 8 * CELL
BOARD_H = 9 * CELL
WIN_W = BOARD_W + 2 * MARGIN
WIN_H = BOARD_H + 2 * MARGIN + 50

PIECE_NAMES = {
    "K": "帅", "A": "仕", "B": "相", "N": "馬", "R": "車", "C": "炮", "P": "兵",
    "k": "将", "a": "士", "b": "象", "n": "马", "r": "车", "c": "砲", "p": "卒",
}

INIT_PIECES = [
    ("R", "red", 0, 9), ("N", "red", 1, 9), ("B", "red", 2, 9), ("A", "red", 3, 9),
    ("K", "red", 4, 9), ("A", "red", 5, 9), ("B", "red", 6, 9), ("N", "red", 7, 9),
    ("R", "red", 8, 9),
    ("C", "red", 1, 7), ("C", "red", 7, 7),
    ("P", "red", 0, 6), ("P", "red", 2, 6), ("P", "red", 4, 6), ("P", "red", 6, 6), ("P", "red", 8, 6),
    ("r", "black", 0, 0), ("n", "black", 1, 0), ("b", "black", 2, 0), ("a", "black", 3, 0),
    ("k", "black", 4, 0), ("a", "black", 5, 0), ("b", "black", 6, 0), ("n", "black", 7, 0),
    ("r", "black", 8, 0),
    ("c", "black", 1, 2), ("c", "black", 7, 2),
    ("p", "black", 0, 3), ("p", "black", 2, 3), ("p", "black", 4, 3), ("p", "black", 6, 3), ("p", "black", 8, 3),
]


# ==================== AI 客户端（轻量，参考 xiangqi/ai.py）====================
class ChessAIClient:
    def __init__(self, api_url="", api_key="", model=""):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.system_prompt = ""

    def get_move(self, current_fen):
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({
            "role": "user",
            "content": (
                f"当前象棋局面（10x9矩阵，r=红方, b=黑方, --=空）：\n"
                f"{current_fen}\n"
                f"请你走一步红方，以相同的矩阵格式输出走棋后的新局面。只输出矩阵，不要解释。"
            )
        })
        resp = requests.post(self.api_url, headers=headers, json={
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2048,
        }, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"API 请求失败: {resp.status_code}")
        content = resp.json()["choices"][0]["message"]["content"]
        fen = self._extract_fen(content)
        if not fen:
            raise Exception(f"AI 未返回有效局面\n{content}")
        return fen

    @staticmethod
    def _extract_fen(text):
        lines = text.replace("\n", ";").split(";")
        cand = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cells = [c.strip() for c in line.replace("，", ",").split(",")]
            if len(cells) == 9 and all(
                c == "--" or (len(c) == 2 and c[0] in "rb" and c[1].isalpha())
                for c in cells
            ):
                cand.append(",".join(cells))
            if len(cand) == 10:
                return ";".join(cand)
        return None


# ==================== 规则引擎 ====================
class ChessRules:
    """精简规则引擎，参考 xiangqi/rules.py"""

    @staticmethod
    def get_legal_moves(piece, pieces, board):
        x, y = piece["x"], piece["y"]
        color = piece["color"]
        t = piece["type"].upper()
        raw = []
        if t in ("K",):
            raw = ChessRules._king_moves(x, y, color, board)
        elif t in ("A",):
            raw = ChessRules._advisor_moves(x, y, color, board)
        elif t in ("B",):
            raw = ChessRules._elephant_moves(x, y, color, board)
        elif t in ("N",):
            raw = ChessRules._knight_moves(x, y, color, board)
        elif t in ("R",):
            raw = ChessRules._rook_moves(x, y, color, board)
        elif t in ("C",):
            raw = ChessRules._cannon_moves(x, y, color, board)
        elif t in ("P",):
            raw = ChessRules._pawn_moves(x, y, color, board)
        return ChessRules._filter_check(piece, x, y, raw, pieces, board)

    @staticmethod
    def _filter_check(piece, ox, oy, moves, pieces, board):
        safe = []
        for nx, ny in moves:
            captured = ChessRules._get_at(nx, ny, pieces)
            piece["x"], piece["y"] = nx, ny
            if captured:
                pieces.remove(captured)
            if not ChessRules._king_attacked(piece["color"], pieces, board):
                safe.append((nx, ny))
            piece["x"], piece["y"] = ox, oy
            if captured:
                pieces.append(captured)
        return safe

    @staticmethod
    def _king_attacked(color, pieces, board):
        king = next((p for p in pieces if p["type"] in ("K", "k") and p["color"] == color), None)
        if not king:
            return True
        b2 = [[None] * 9 for _ in range(10)]
        for p in pieces:
            b2[p["y"]][p["x"]] = p
        opp = "red" if color == "black" else "black"
        for p in pieces:
            if p["color"] != opp:
                continue
            m = ChessRules._all_raw(p, b2)
            if (king["x"], king["y"]) in m:
                return True
        return False

    @staticmethod
    def _all_raw(piece, board):
        x, y, color, t = piece["x"], piece["y"], piece["color"], piece["type"].upper()
        if t == "K":
            return ChessRules._king_moves(x, y, color, board)
        if t == "A":
            return ChessRules._advisor_moves(x, y, color, board)
        if t == "B":
            return ChessRules._elephant_moves(x, y, color, board)
        if t == "N":
            return ChessRules._knight_moves(x, y, color, board)
        if t == "R":
            return ChessRules._rook_moves(x, y, color, board)
        if t == "C":
            return ChessRules._cannon_moves(x, y, color, board)
        if t == "P":
            return ChessRules._pawn_moves(x, y, color, board)
        return []

    @staticmethod
    def _inb(x, y):
        return 0 <= x <= 8 and 0 <= y <= 9

    @staticmethod
    def _palace(x, y, color):
        if color == "red":
            return 3 <= x <= 5 and 7 <= y <= 9
        return 3 <= x <= 5 and 0 <= y <= 2

    @staticmethod
    def _get_at(x, y, pieces):
        for p in pieces:
            if p["x"] == x and p["y"] == y:
                return p
        return None

    @staticmethod
    def _king_moves(x, y, color, board):
        m = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if ChessRules._inb(nx, ny) and ChessRules._palace(nx, ny, color):
                t = board[ny][nx]
                if not t or t["color"] != color:
                    m.append((nx, ny))
        return m

    @staticmethod
    def _advisor_moves(x, y, color, board):
        m = []
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = x + dx, y + dy
            if ChessRules._palace(nx, ny, color):
                t = board[ny][nx]
                if not t or t["color"] != color:
                    m.append((nx, ny))
        return m

    @staticmethod
    def _elephant_moves(x, y, color, board):
        m = []
        for ex, ey, mx, my in [(1, 1, 2, 2), (1, -1, 2, -2), (-1, 1, -2, 2), (-1, -1, -2, -2)]:
            nx, ny = x + mx, y + my
            if ChessRules._inb(nx, ny):
                if (color == "red" and ny >= 5) or (color == "black" and ny <= 4):
                    if not board[y + ey][x + ex]:
                        t = board[ny][nx]
                        if not t or t["color"] != color:
                            m.append((nx, ny))
        return m

    @staticmethod
    def _knight_moves(x, y, color, board):
        m = []
        for lx, ly, mx, my in [
            (0, 1, -1, 2), (0, 1, 1, 2), (0, -1, -1, -2), (0, -1, 1, -2),
            (1, 0, 2, 1), (1, 0, 2, -1), (-1, 0, -2, 1), (-1, 0, -2, -1)
        ]:
            nx, ny = x + mx, y + my
            if ChessRules._inb(nx, ny):
                if not board[y + ly][x + lx]:
                    t = board[ny][nx]
                    if not t or t["color"] != color:
                        m.append((nx, ny))
        return m

    @staticmethod
    def _rook_moves(x, y, color, board):
        m = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            while ChessRules._inb(nx, ny):
                t = board[ny][nx]
                if t:
                    if t["color"] != color:
                        m.append((nx, ny))
                    break
                m.append((nx, ny))
                nx += dx
                ny += dy
        return m

    @staticmethod
    def _cannon_moves(x, y, color, board):
        m = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            while ChessRules._inb(nx, ny):
                if board[ny][nx]:
                    break
                m.append((nx, ny))
                nx += dx
                ny += dy
            nx += dx
            ny += dy
            while ChessRules._inb(nx, ny):
                t = board[ny][nx]
                if t:
                    if t["color"] != color:
                        m.append((nx, ny))
                    break
                nx += dx
                ny += dy
        return m

    @staticmethod
    def _pawn_moves(x, y, color, board):
        m = []
        forward = -1 if color == "red" else 1
        ny = y + forward
        if ChessRules._inb(x, ny):
            t = board[ny][x]
            if not t or t["color"] != color:
                m.append((x, ny))
        river_y = 4 if color == "red" else 5
        if (color == "red" and y <= river_y) or (color == "black" and y >= river_y):
            for dx in (-1, 1):
                nx = x + dx
                if ChessRules._inb(nx, y):
                    t = board[y][nx]
                    if not t or t["color"] != color:
                        m.append((nx, y))
        return m


# ==================== 简单随机 AI ====================
def _random_ai_move(pieces, is_red_turn):
    import random
    board = [[None] * 9 for _ in range(10)]
    for p in pieces:
        board[p["y"]][p["x"]] = p
    color = "red" if is_red_turn else "black"
    my_pieces = [p for p in pieces if p["color"] == color]
    random.shuffle(my_pieces)
    for p in my_pieces:
        moves = ChessRules.get_legal_moves(p, pieces[:], board)
        if moves:
            nx, ny = random.choice(moves)
            return p, (nx, ny)
    return None


# ==================== AI 配置文件路径 ====================
AI_CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "table-tools")
AI_CONFIG_FILE = os.path.join(AI_CONFIG_DIR, "chess_ai.json")


# ==================== 主窗口 ====================
class ChessWindow(tk.Toplevel, ImageBackgroundMixin):
    """象棋窗口"""

    MODULE_NAME = "chess"

    def __init__(self, parent=None):
        tk.Toplevel.__init__(self, parent)
        ImageBackgroundMixin.__init__(self)
        self.title("中国象棋")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 状态
        self.flipped = False
        self.pieces = []
        self.drag_piece = None
        self.drag_start_xy = (0, 0)
        self.check_rules = tk.BooleanVar(value=True)
        self.click_mode = tk.BooleanVar(value=False)
        self.ai_enabled = tk.BooleanVar(value=False)
        self.animating = False
        self.ai_thinking = False
        self.highlight_circles = []
        self.legal_targets = []
        self.selected_piece = None
        self.selection_highlight_id = None
        self._ai_client = ChessAIClient()

        self.load_initial_pieces()
        self._build_ui()
        self.draw_board()

    def load_initial_pieces(self):
        self.pieces = [
            {"type": t, "color": c, "x": x, "y": y, "id": None}
            for t, c, x, y in INIT_PIECES
        ]

    # ---------- UI 控件 ----------
    def _build_ui(self):
        self._canvas = tk.Canvas(self, width=WIN_W, height=WIN_H - 50,
                                  bg="#f0d9b5", highlightthickness=0)
        self._canvas.pack()

        ctrl = tk.Frame(self, bg=C["bg_card"])
        ctrl.pack(fill=tk.X)

        ck_args = {"bg": C["bg_card"], "fg": C["fg"], "selectcolor": C["bg_input"],
                    "font": F["small"]}

        tk.Checkbutton(ctrl, text="己方为黑方", variable=tk.BooleanVar(value=False),
                       command=self.flip_board, **ck_args).pack(side=tk.LEFT, padx=3)
        tk.Checkbutton(ctrl, text="规则校验", variable=self.check_rules,
                       command=self.clear_highlights, **ck_args).pack(side=tk.LEFT, padx=3)
        tk.Checkbutton(ctrl, text="点按模式", variable=self.click_mode,
                       command=self.clear_selection, **ck_args).pack(side=tk.LEFT, padx=3)
        tk.Checkbutton(ctrl, text="AI 对战", variable=self.ai_enabled,
                       command=self.toggle_ai, **ck_args).pack(side=tk.LEFT, padx=3)

        btn_args = {"bg": C["bg_button"], "fg": C["fg"], "font": F["small"],
                     "relief": tk.FLAT, "cursor": "hand2", "padx": 8, "pady": 2,
                     "activebackground": C["bg_button_hover"],
                     "activeforeground": C["fg"],
                     "borderwidth": 0, "highlightthickness": 0}
        tk.Button(ctrl, text="翻转", command=self.flip_board, **btn_args).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="AI 走棋", command=self.request_ai_move, **btn_args).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="AI 设置", command=self.open_ai_settings, **btn_args).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="重开", command=self.restart, **btn_args).pack(side=tk.LEFT, padx=2)

        # 事件绑定
        self._canvas.bind("<Button-1>", self.on_press)
        self._canvas.bind("<B1-Motion>", self.on_drag)
        self._canvas.bind("<ButtonRelease-1>", self.on_release)

    # ---------- 绘制 ----------
    def draw_board(self):
        c = self._canvas
        c.delete("all")
        self.highlight_circles.clear()
        w, h = WIN_W, WIN_H - 50

        # 背景
        c.create_rectangle(0, 0, w, h, fill="#f0d9b5", outline="")

        # 棋盘线
        for i in range(10):
            y = MARGIN + i * CELL
            c.create_line(MARGIN, y, MARGIN + 8 * CELL, y, fill="black",
                          width=2 if i in (0, 9) else 1)
        for i in range(9):
            x = MARGIN + i * CELL
            c.create_line(x, MARGIN, x, MARGIN + 4 * CELL, fill="black")
            c.create_line(x, MARGIN + 5 * CELL, x, MARGIN + 9 * CELL, fill="black")
        # 边线加粗
        c.create_line(MARGIN, MARGIN, MARGIN, MARGIN + 9 * CELL, fill="black", width=2)
        c.create_line(MARGIN + 8 * CELL, MARGIN, MARGIN + 8 * CELL, MARGIN + 9 * CELL, fill="black", width=2)

        # 楚河汉界
        c.create_text(MARGIN + 4 * CELL, MARGIN + 4.5 * CELL,
                      text="楚  河          汉  界", font=("楷体", 14), fill="black")

        # 九宫斜线
        for x1, y1, x2, y2 in [
            (MARGIN + 3 * CELL, MARGIN + 7 * CELL, MARGIN + 5 * CELL, MARGIN + 9 * CELL),
            (MARGIN + 3 * CELL, MARGIN, MARGIN + 5 * CELL, MARGIN + 2 * CELL),
        ]:
            c.create_line(x1, y1, x2, y2, fill="black")
            c.create_line(x2, y1, x1, y2, fill="black")

        # 棋子
        for p in self.pieces:
            dx = MARGIN + p["x"] * CELL
            dy = MARGIN + ((9 - p["y"]) if self.flipped else p["y"]) * CELL
            txt = PIECE_NAMES.get(p["type"], p["type"])
            col = "red" if p["color"] == "red" else "black"
            pid = c.create_text(dx, dy, text=txt,
                                font=("楷体", 24, "bold"), fill=col, anchor="center")
            p["id"] = pid
            p["disp_x"] = dx
            p["disp_y"] = dy

        # 选中高亮
        if self.click_mode.get() and self.selected_piece is not None:
            self.draw_selection_highlight()

    def draw_selection_highlight(self):
        if self.selected_piece:
            dx = self.selected_piece["disp_x"]
            dy = self.selected_piece["disp_y"]
            r = 22
            self.selection_highlight_id = self._canvas.create_rectangle(
                dx - r, dy - r, dx + r, dy + r,
                outline="yellow", width=3
            )

    def clear_highlights(self):
        for cid in self.highlight_circles:
            self._canvas.delete(cid)
        self.highlight_circles.clear()
        self.legal_targets.clear()

    def clear_selection(self):
        if self.selection_highlight_id:
            self._canvas.delete(self.selection_highlight_id)
            self.selection_highlight_id = None
        self.selected_piece = None
        self.clear_highlights()

    def draw_highlights(self, targets):
        self.clear_highlights()
        for tx, ty in targets:
            dx = MARGIN + tx * CELL
            dy = MARGIN + ((9 - ty) if self.flipped else ty) * CELL
            cid = self._canvas.create_oval(dx - 8, dy - 8, dx + 8, dy + 8,
                                           fill="#90ee90", outline="#228b22", width=2)
            self.highlight_circles.append(cid)
        self.legal_targets = targets

    def build_board_array(self):
        board = [[None] * 9 for _ in range(10)]
        for p in self.pieces:
            board[p["y"]][p["x"]] = p
        return board

    def own_color(self):
        return "black" if self.flipped else "red"

    def can_control(self, piece):
        return piece["color"] == self.own_color()

    # ---------- 动画 ----------
    def _local_anim(self, piece, start, end, cb):
        self.animating = True
        steps = 10
        dx = (end[0] - start[0]) / steps
        dy = (end[1] - start[1]) / steps

        def step(i=0):
            if i <= steps:
                self._canvas.coords(piece["id"], start[0] + dx * i, start[1] + dy * i)
                self.after(20, step, i + 1)
            else:
                self.animating = False
                cb()

        self._canvas.itemconfig(piece["id"], font=("楷体", 32, "bold"))
        self.after(20, step)

    # ---------- 事件 ----------
    def on_press(self, event):
        if self.animating or self.ai_thinking:
            return
        if self.click_mode.get():
            return
        self.clear_highlights()
        for p in reversed(self.pieces):
            if math.hypot(event.x - p["disp_x"], event.y - p["disp_y"]) < CELL / 2 and self.can_control(p):
                self.drag_piece = p
                self.drag_start_xy = (p["x"], p["y"])
                self._canvas.tag_raise(p["id"])
                if self.check_rules.get():
                    legal = ChessRules.get_legal_moves(p, self.pieces[:], self.build_board_array())
                    self.draw_highlights(legal)
                break

    def on_drag(self, event):
        if self.animating or self.ai_thinking or self.click_mode.get() or not self.drag_piece:
            return
        self._canvas.coords(self.drag_piece["id"], event.x, event.y)
        self.drag_piece["disp_x"] = event.x
        self.drag_piece["disp_y"] = event.y

    def on_release(self, event):
        if self.animating or self.ai_thinking:
            return
        if self.click_mode.get():
            self._handle_click(event)
            return
        if not self.drag_piece:
            return

        gx = round((event.x - MARGIN) / CELL)
        gy = round((event.y - MARGIN) / CELL)
        ax = gx
        ay = 9 - gy if self.flipped else gy

        if (ax, ay) == self.drag_start_xy:
            self._snap_back()
            self.drag_piece = None
            self.clear_highlights()
            return

        if self.check_rules.get() and self.legal_targets:
            best = min(self.legal_targets, key=lambda t: math.hypot(t[0] - ax, t[1] - ay))
            ax, ay = best

        if not (0 <= ax <= 8 and 0 <= ay <= 9):
            self._snap_back()
            self.drag_piece = None
            self.clear_highlights()
            return

        target = self._get_at(ax, ay)
        if target and target["color"] == self.drag_piece["color"]:
            self._snap_back()
            self.drag_piece = None
            self.clear_highlights()
            return

        piece = self.drag_piece
        start = (piece["disp_x"], piece["disp_y"])
        end = (MARGIN + ax * CELL, MARGIN + ((9 - ay) if self.flipped else ay) * CELL)
        if target:
            self._canvas.delete(target["id"])
            self.pieces.remove(target)
        self.drag_piece = None
        self.clear_highlights()

        def after_anim():
            piece["x"] = ax
            piece["y"] = ay
            self.draw_board()

        self._local_anim(piece, start, end, after_anim)

    def _handle_click(self, event):
        gx = round((event.x - MARGIN) / CELL)
        gy = round((event.y - MARGIN) / CELL)
        ax = gx
        ay = 9 - gy if self.flipped else gy
        if not (0 <= ax <= 8 and 0 <= ay <= 9):
            self.clear_selection()
            return

        clicked = self._get_at(ax, ay)

        if self.selected_piece is None:
            if clicked and self.can_control(clicked):
                self.selected_piece = clicked
                self.drag_start_xy = (clicked["x"], clicked["y"])
                self.draw_selection_highlight()
                if self.check_rules.get():
                    legal = ChessRules.get_legal_moves(clicked, self.pieces[:], self.build_board_array())
                    self.draw_highlights(legal)
            return

        if clicked and clicked is self.selected_piece:
            self.clear_selection()
            return
        if clicked and self.can_control(clicked):
            self.selected_piece = clicked
            self.drag_start_xy = (clicked["x"], clicked["y"])
            self.draw_selection_highlight()
            if self.check_rules.get():
                legal = ChessRules.get_legal_moves(clicked, self.pieces[:], self.build_board_array())
                self.draw_highlights(legal)
            return

        if self.check_rules.get() and (ax, ay) not in self.legal_targets:
            self.clear_selection()
            return
        if (ax, ay) == self.drag_start_xy:
            self.clear_selection()
            return

        target = self._get_at(ax, ay)
        if target and target["color"] == self.selected_piece["color"]:
            self.clear_selection()
            return

        piece = self.selected_piece
        start = (MARGIN + piece["x"] * CELL, MARGIN + ((9 - piece["y"]) if self.flipped else piece["y"]) * CELL)
        end = (MARGIN + ax * CELL, MARGIN + ((9 - ay) if self.flipped else ay) * CELL)
        if target:
            self._canvas.delete(target["id"])
            self.pieces.remove(target)
        self.selected_piece = None
        self.clear_selection()

        def after_anim():
            piece["x"] = ax
            piece["y"] = ay
            self.draw_board()

        self._local_anim(piece, start, end, after_anim)

    def _snap_back(self):
        if self.drag_piece:
            self.drag_piece["x"], self.drag_piece["y"] = self.drag_start_xy
            self.draw_board()

    def _get_at(self, x, y):
        for p in self.pieces:
            if p["x"] == x and p["y"] == y:
                return p
        return None

    # ---------- AI ----------
    def toggle_ai(self):
        if self.ai_enabled.get():
            if not self._ai_client.api_key:
                self.ai_enabled.set(False)
                messagebox.showwarning("AI 未配置", "请点击「AI 设置」配置 API 密钥。\n若不配置则使用内置随机 AI。")
                # 仍然启用，使用随机AI
                self.ai_enabled.set(True)
            status_msg = "AI 已开启"
        else:
            status_msg = "AI 已关闭"
        self._show_status(status_msg)

    def _show_status(self, msg):
        c = self._canvas
        c.create_text(WIN_W // 2, 20, text=msg,
                      fill="blue", font=("微软雅黑", 12))
        self.after(1200, self.draw_board)

    def request_ai_move(self):
        if self.ai_thinking or self.animating:
            return
        self.ai_thinking = True
        self._show_status("AI 思考中...")

        threading.Thread(target=self._ai_worker, daemon=True).start()

    def _ai_worker(self):
        try:
            fen = self._gen_fen()
            # 尝试 API AI，失败则使用随机 AI
            if self._ai_client.api_key:
                try:
                    new_fen = self._ai_client.get_move(fen)
                    self.after(0, self._apply_ai_move, new_fen)
                    return
                except Exception:
                    pass
            # 随机 AI
            self._do_random_ai()
        except Exception as e:
            self.after(0, self._ai_error, str(e))

    def _do_random_ai(self):
        # AI 作为用户的对手：flipped=False 时 AI 走黑方，flipped=True 时 AI 走红方
        ai_color = "black" if not self.flipped else "red"
        move = _random_ai_move(self.pieces, is_red_turn=(ai_color == "red"))
        if move:
            piece, (nx, ny) = move
            # 应用走法
            ox, oy = piece["x"], piece["y"]
            target = self._get_at(nx, ny)
            start = (MARGIN + ox * CELL, MARGIN + ((9 - oy) if self.flipped else oy) * CELL)
            end = (MARGIN + nx * CELL, MARGIN + ((9 - ny) if self.flipped else ny) * CELL)
            if target:
                self._canvas.delete(target["id"])
                self.pieces.remove(target)

            def after_anim():
                piece["x"] = nx
                piece["y"] = ny
                self.ai_thinking = False
                self.draw_board()

            self._local_anim(piece, start, end, after_anim)
        else:
            self.ai_thinking = False
            self._show_status("AI 无棋可走")

    def _apply_ai_move(self, new_fen):
        self.ai_thinking = False
        self._apply_fen(new_fen)

    def _ai_error(self, msg):
        self.ai_thinking = False
        messagebox.showerror("AI 错误", str(msg))
        self.draw_board()

    def _gen_fen(self):
        board = [["--"] * 9 for _ in range(10)]
        for p in self.pieces:
            c = "r" if p["color"] == "red" else "b"
            board[p["y"]][p["x"]] = f"{c}{p['type']}"
        return ";".join([",".join(row) for row in board])

    def _apply_fen(self, fen):
        """从 FEN 文本恢复局面"""
        try:
            rows = fen.split(";")
            if len(rows) != 10:
                return
            new_data = []
            for y, row in enumerate(rows):
                cells = row.split(",")
                if len(cells) != 9:
                    continue
                for x, cell in enumerate(cells):
                    cell = cell.strip()
                    if cell in ("--", ""):
                        continue
                    if len(cell) < 2:
                        continue
                    cc, tp = cell[0], cell[1]
                    if cc not in ("r", "b") or tp not in PIECE_NAMES:
                        continue
                    new_data.append({
                        "type": tp,
                        "color": "red" if cc == "r" else "black",
                        "x": x, "y": y, "id": None
                    })
            self.pieces = [{"type": p["type"], "color": p["color"],
                            "x": p["x"], "y": p["y"], "id": None}
                           for p in new_data]
            self.clear_selection()
            self.draw_board()
        except Exception:
            pass

    # ---------- AI 设置 ----------
    def open_ai_settings(self):
        win = tk.Toplevel(self)
        win.title("AI 设置")
        win.grab_set()
        win.configure(bg=C["bg"])

        fields = [
            ("API 地址:", self._ai_client.api_url),
            ("API 密钥:", self._ai_client.api_key),
            ("模型:", self._ai_client.model),
        ]
        vars = []
        for i, (label, val) in enumerate(fields):
            tk.Label(win, text=label, bg=C["bg"], fg=C["fg"],
                     font=F["body"]).grid(row=i, column=0, sticky="e", padx=5, pady=4)
            var = tk.StringVar(value=val)
            tk.Entry(win, textvariable=var, width=50,
                     bg=C["bg_input"], fg=C["fg"], insertbackground=C["fg"],
                     relief=tk.FLAT, highlightthickness=1,
                     highlightbackground=C["border"],
                     highlightcolor=C["border_focus"],
                     bd=0,
                     show="*" if "密钥" in label else "").grid(row=i, column=1, pady=4)
            vars.append(var)

        def save():
            self._ai_client.api_url = vars[0].get()
            self._ai_client.api_key = vars[1].get()
            self._ai_client.model = vars[2].get()
            self._save_ai_config()
            win.destroy()
            messagebox.showinfo("提示", "AI 配置已保存")

        btn_frame = tk.Frame(win, bg=C["bg"])
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        make_button(btn_frame, text="保存", command=save).pack()

    def _save_ai_config(self):
        os.makedirs(AI_CONFIG_DIR, exist_ok=True)
        try:
            with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "api_url": self._ai_client.api_url,
                    "api_key": self._ai_client.api_key,
                    "model": self._ai_client.model,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ---------- 其他 ----------
    def flip_board(self):
        self.flipped = not self.flipped
        self.draw_board()

    def restart(self):
        self.load_initial_pieces()
        self.clear_selection()
        self.ai_thinking = False
        self.draw_board()

    def _on_close(self):
        self.destroy()
