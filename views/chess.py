"""中国象棋 — Flet 棋盘版"""

import copy
import flet as ft
from modules.chess import INIT_BOARD, EMPTY
from views.common import page_wrapper, glass_card, secondary_button


class ChessView:
    def __init__(self, page, navigate=None):
        self.page = page
        self.navigate = navigate
        self._board = copy.deepcopy(INIT_BOARD)
        self._current_turn = "red"  # red goes first
        self._selected = None
        self._game_over = False
        self._status_msg = "红方走棋"

        # 棋子图标映射
        self._piece_chars = {
            "R": "车", "N": "马", "B": "象", "A": "仕", "K": "帅", "C": "炮", "P": "兵",
            "r": "車", "n": "馬", "b": "相", "a": "士", "k": "將", "c": "砲", "p": "卒",
        }

    def build(self):
        self._board_grid = ft.Column(spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self._status_text = ft.Text("红方走棋", size=16, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.PRIMARY)
        self._move_log = ft.ListView(spacing=2, padding=4, height=200)

        self._reset_btn = secondary_button("重新开局", on_click=self._reset)
        self._undo_btn = secondary_button("↩ 悔棋", on_click=self._undo)

        self._render_board()

        board_card = glass_card(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.SPORTS_ESPORTS, color=ft.Colors.PRIMARY),
                    self._status_text,
                ], spacing=8),
                ft.Container(
                    content=self._board_grid,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Row([self._reset_btn, self._undo_btn], spacing=12,
                       alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=20,
        )

        log_card = glass_card(
            content=ft.Column([
                ft.Text("走棋记录", size=14, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE),
                self._move_log,
            ], spacing=4),
            padding=16,
        )

        # 布局：棋盘居左，记录居右
        content = ft.Row([
            ft.Container(content=board_card, width=460),
            ft.Container(content=log_card, expand=True),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START)

        return page_wrapper(content, page=self.page)

    def _render_board(self):
        self._board_grid.controls.clear()
        for ri, row in enumerate(self._board):
            cells = []
            for ci, cell in enumerate(row):
                is_selected = self._selected == (ri, ci)
                piece_char = self._piece_chars.get(cell, "")
                is_red = cell.isupper() if cell != EMPTY else False
                is_black = cell.islower() if cell != EMPTY else False

                fg_color = "#CC0000" if is_red else "#000000" if is_black else None
                bg_color = "#FFF3E0" if is_selected else "#F5F0E8"

                # 棋盘交叉点背景
                if (ri, ci) == (0, 0) or (ri, ci) == (0, 8) or \
                   (ri, ci) == (9, 0) or (ri, ci) == (9, 8):
                    bg_color = "#F5F0E8"

                btn = ft.Container(
                    content=ft.Text(piece_char or "·",
                                    size=22 if piece_char else 14,
                                    weight=ft.FontWeight.BOLD if piece_char else ft.FontWeight.NORMAL,
                                    color=fg_color or ft.Colors.GREY_400,
                                    text_align=ft.TextAlign.CENTER),
                    width=44,
                    height=44,
                    bgcolor=bg_color,
                    border=ft.Border.all(2, ft.Colors.PRIMARY) if is_selected else None,
                    border_radius=22 if piece_char else 0,
                    alignment=ft.Alignment(0, 0),
                    ink=True,
                    on_click=lambda _, r=ri, c=ci: self._on_cell_click(r, c),
                    shadow=ft.BoxShadow(blur_radius=4, color="#00000022") if piece_char else None,
                )
                cells.append(btn)

            row_widget = ft.Row(cells, spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            self._board_grid.controls.append(row_widget)

        # 添加列标
        col_labels = ft.Row(
            [ft.Container(width=44, content=ft.Text(c, size=10,
                           color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER))
             for c in "abcdefghi"],
            spacing=2, alignment=ft.MainAxisAlignment.CENTER
        )
        self._board_grid.controls.append(col_labels)

    def _on_cell_click(self, ri, ci):
        if self._game_over:
            return

        cell = self._board[ri][ci]
        is_red_piece = cell.isupper() and cell != EMPTY
        is_black_piece = cell.islower() and cell != EMPTY

        if self._selected is None:
            # 选择棋子
            if (self._current_turn == "red" and is_red_piece) or \
               (self._current_turn == "black" and is_black_piece):
                self._selected = (ri, ci)
                self._render_board()
                self._board_grid.update()
        else:
            sr, sc = self._selected
            # 如果点击的是自己的棋子，切换选择
            if (self._current_turn == "red" and is_red_piece) or \
               (self._current_turn == "black" and is_black_piece):
                self._selected = (ri, ci)
                self._render_board()
                self._board_grid.update()
                return

            # 尝试走棋
            self._board[ri][ci] = self._board[sr][sc]
            self._board[sr][sc] = EMPTY
            self._selected = None

            # 切换回合
            self._current_turn = "black" if self._current_turn == "red" else "red"
            self._status_text.value = f"{'红方' if self._current_turn == 'red' else '黑方'}走棋"
            self._status_text.color = ft.Colors.PRIMARY if self._current_turn == "red" else ft.Colors.ON_SURFACE

            # 记录
            from_c = chr(ord('a') + sc)
            to_c = chr(ord('a') + ci)
            piece = self._piece_chars.get(cell, "?")
            self._move_log.controls.append(
                ft.Text(f"{'红' if is_red_piece else '黑'}{piece}: {from_c}{9-sr}→{to_c}{9-ri}",
                       size=12, color=ft.Colors.ON_SURFACE_VARIANT)
            )
            self._move_log.scroll_to(offset=-1, duration=100)

            self._render_board()
            self._board_grid.update()

    def _reset(self, e=None):
        self._board = copy.deepcopy(INIT_BOARD)
        self._current_turn = "red"
        self._selected = None
        self._game_over = False
        self._status_text.value = "红方走棋"
        self._status_text.color = ft.Colors.PRIMARY
        self._move_log.controls.clear()
        self._render_board()
        self._board_grid.update()
        self._move_log.update()

    def _undo(self, e=None):
        if self._move_log.controls:
            self._move_log.controls.pop()
            self._move_log.update()
