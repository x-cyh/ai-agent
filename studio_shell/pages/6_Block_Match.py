from __future__ import annotations

import random
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import format_extra_context, inject_style


st.set_page_config(page_title="方塊消消樂", page_icon="🟦", layout="wide")
inject_style()

COLORS = ["🟥", "🟨", "🟩", "🟦", "🟪"]
BOARD_SIZE = 6


def _new_board() -> list[list[str]]:
    return [[random.choice(COLORS) for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def _ensure_state() -> None:
    if "block_board" not in st.session_state:
        st.session_state.block_board = _new_board()
        st.session_state.block_score = 0
        st.session_state.block_moves = 20
        st.session_state.block_message = "選擇相鄰同色方塊消除。"


def _neighbors(row: int, col: int) -> list[tuple[int, int]]:
    return [
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    ]


def _connected_group(board: list[list[str]], row: int, col: int) -> set[tuple[int, int]]:
    color = board[row][col]
    group = {(row, col)}
    stack = [(row, col)]

    while stack:
        current_row, current_col = stack.pop()
        for next_row, next_col in _neighbors(current_row, current_col):
            if not (0 <= next_row < BOARD_SIZE and 0 <= next_col < BOARD_SIZE):
                continue
            if (next_row, next_col) in group:
                continue
            if board[next_row][next_col] == color:
                group.add((next_row, next_col))
                stack.append((next_row, next_col))

    return group


def _drop_blocks(board: list[list[str]]) -> list[list[str]]:
    next_board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for col in range(BOARD_SIZE):
        kept = [board[row][col] for row in range(BOARD_SIZE) if board[row][col]]
        refill = [random.choice(COLORS) for _ in range(BOARD_SIZE - len(kept))]
        column = refill + kept
        for row in range(BOARD_SIZE):
            next_board[row][col] = column[row]
    return next_board


def _clear_group(row: int, col: int) -> None:
    board = st.session_state.block_board
    group = _connected_group(board, row, col)

    if st.session_state.block_moves <= 0:
        st.session_state.block_message = "步數用完，請重新開始。"
        return

    if len(group) < 2:
        st.session_state.block_moves -= 1
        st.session_state.block_message = "至少要連到 2 個同色方塊才能消除。"
        return

    for block_row, block_col in group:
        board[block_row][block_col] = ""

    st.session_state.block_board = _drop_blocks(board)
    st.session_state.block_moves -= 1
    gained = len(group) * len(group) * 5
    st.session_state.block_score += gained
    st.session_state.block_message = f"消除 {len(group)} 個方塊，獲得 {gained} 分！"


def _reset_game() -> None:
    st.session_state.block_board = _new_board()
    st.session_state.block_score = 0
    st.session_state.block_moves = 20
    st.session_state.block_message = "新局開始。"


def render_main() -> str:
    _ensure_state()

    st.markdown("#### 方塊消消樂")
    st.write("點擊連在一起的同色方塊，消除越多得分越高。")

    stats = st.columns(3)
    stats[0].metric("分數", st.session_state.block_score)
    stats[1].metric("剩餘步數", st.session_state.block_moves)
    stats[2].metric("方塊種類", len(COLORS))

    st.info(st.session_state.block_message)

    board = st.session_state.block_board
    for row in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for col in range(BOARD_SIZE):
            with cols[col]:
                st.button(
                    board[row][col],
                    key=f"block_{row}_{col}",
                    use_container_width=True,
                    disabled=st.session_state.block_moves <= 0,
                    on_click=_clear_group,
                    args=(row, col),
                )

    if st.button("重新開始", use_container_width=True):
        _reset_game()
        st.rerun()

    extra = format_extra_context(
        "方塊消消樂",
        分數=st.session_state.block_score,
        剩餘步數=st.session_state.block_moves,
        狀態=st.session_state.block_message,
    )
    return extra


page_shell(
    "方塊消消樂",
    "點擊相鄰同色方塊，消除並累積分數。",
    render_main,
    page_name="方塊消消樂",
)
