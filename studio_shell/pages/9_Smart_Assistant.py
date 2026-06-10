from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHELL_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import (
    format_extra_context,
    inject_style,
    load_page_data,
    save_page_data,
    shared_data_path,
)

PAGE_NAME = "Smart Assistant"

st.set_page_config(page_title="智慧助手", page_icon="🧠", layout="wide")
inject_style()


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _normalize_checklist(items: object) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    if not isinstance(items, list):
        return normalized

    for item in items:
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
            done = bool(item.get("done", False))
        else:
            text = str(item).strip()
            done = False
        if text:
            normalized.append({"text": text, "done": done})
    return normalized


def _build_checklist(tasks: list[str], previous: object) -> list[dict[str, object]]:
    previous_items = _normalize_checklist(previous)
    done_map = {
        str(item.get("text", "")).strip(): bool(item.get("done", False))
        for item in previous_items
        if str(item.get("text", "")).strip()
    }
    return [{"text": task, "done": done_map.get(task, False)} for task in tasks]


def _generate_plan(goal: str, deadline: str, blocker: str, notes: str) -> tuple[list[str], list[str], str]:
    clean_goal = goal.strip()
    clean_deadline = deadline.strip()
    clean_blocker = blocker.strip()
    note_lines = _split_lines(notes)

    tasks: list[str] = []
    top3: list[str] = []

    if clean_goal:
        tasks.append(f"釐清成果：把「{clean_goal}」定義成可完成的具體結果")
        tasks.append("拆成 3 到 5 個可在短時間完成的小步驟")
    else:
        tasks.append("先寫下這次想完成的目標，避免待辦太模糊")
        tasks.append("把目標拆成可以立刻開始的第一個小任務")

    if clean_deadline:
        tasks.append(f"回推時程：依截止時間「{clean_deadline}」安排優先順序")
    else:
        tasks.append("補上預計完成時間，幫助安排先後順序")

    if clean_blocker:
        tasks.append(f"處理卡點：先解決「{clean_blocker}」這個阻礙")
    else:
        tasks.append("找出目前最大的阻礙，先排除再往下做")

    if note_lines:
        tasks.append(f"整理補充資訊：優先處理「{note_lines[0]}」")

    top3.extend(tasks[:3])

    if clean_blocker:
        first_step = f"先花 10 分鐘把「{clean_blocker}」寫成一個可解決的小問題。"
    elif clean_goal:
        first_step = f"先列出完成「{clean_goal}」前一定要做的 3 件事。"
    else:
        first_step = "先用一句話寫下你現在最想完成的事情。"

    return tasks, top3, first_step


def render_main() -> str:
    state = load_page_data(PAGE_NAME, shell_root=SHELL_ROOT)

    st.markdown("#### 智慧助手")
    st.caption("輸入你的目標與卡點，先得到可執行的待辦拆解。")

    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input(
            "暱稱",
            value=state.get("nickname", ""),
            placeholder="例如：小明",
        )
        goal = st.text_area(
            "目標",
            value=state.get("goal", ""),
            placeholder="例如：完成一個能跟 agent 結合的實用工具",
            height=100,
        )
        blocker = st.text_area(
            "目前卡住的地方",
            value=state.get("blocker", ""),
            placeholder="例如：不知道先做哪個功能、資料結構還沒想好",
            height=90,
        )
    with col2:
        deadline = st.text_input(
            "截止時間",
            value=state.get("deadline", ""),
            placeholder="例如：這週日、明天下午 6 點",
        )
        notes = st.text_area(
            "補充資訊",
            value=state.get("notes", ""),
            placeholder="例如：希望先做 MVP、最好能寫進共享 JSON",
            height=140,
        )

    task_breakdown, top3_today, first_step = _generate_plan(goal, deadline, blocker, notes)
    checklist = _build_checklist(task_breakdown, state.get("checklist", []))

    st.divider()
    st.markdown("#### 助手建議")

    result_col1, result_col2 = st.columns([1.25, 1])
    with result_col1:
        st.markdown("**任務拆解**")
        for idx, item in enumerate(task_breakdown, start=1):
            st.markdown(f"{idx}. {item}")

        st.markdown("**可勾選待辦**")
        updated_checklist: list[dict[str, object]] = []
        for idx, item in enumerate(checklist):
            checked = st.checkbox(
                item["text"],
                value=bool(item.get("done", False)),
                key=f"smart_assistant_check_{idx}",
            )
            updated_checklist.append({"text": item["text"], "done": checked})

    with result_col2:
        st.markdown("**今天最重要 3 件事**")
        for idx, item in enumerate(top3_today, start=1):
            st.markdown(f"{idx}. {item}")
        st.markdown("**建議第一步**")
        st.info(first_step)

        done_count = sum(1 for item in updated_checklist if bool(item.get("done", False)))
        total_count = len(updated_checklist)
        st.metric("完成進度", f"{done_count}/{total_count}")

    save_page_data(
        PAGE_NAME,
        {
            "nickname": nickname,
            "goal": goal,
            "deadline": deadline,
            "blocker": blocker,
            "notes": notes,
            "task_breakdown": task_breakdown,
            "top3_today": top3_today,
            "first_step": first_step,
            "checklist": updated_checklist,
        },
        shell_root=SHELL_ROOT,
    )

    st.divider()
    st.markdown("#### 給 Agent 的摘要")
    extra = format_extra_context(
        PAGE_NAME,
        共享資料檔=str(shared_data_path(PAGE_NAME, shell_root=SHELL_ROOT)),
        左欄暱稱=nickname or "（未填）",
        左欄目標=goal or "（未填）",
        左欄截止時間=deadline or "（未填）",
        左欄卡點=blocker or "（未填）",
        左欄補充資訊=notes or "（未填）",
        左欄今日前三項="；".join(top3_today) if top3_today else "（未填）",
        左欄建議第一步=first_step or "（未填）",
        左欄完成進度=f"{done_count}/{total_count}",
    )
    st.code(extra, language="text")

    st.markdown("#### 右欄可以這樣問")
    st.markdown(
        """
- 「根據我的目標，幫我把任務拆得更細。」
- 「請依照截止時間幫我重排優先順序。」
- 「請把左欄的建議第一步改成更容易開始的版本。」
- 「請把第一個待辦標記成完成。」
"""
    )
    return extra


page_shell(
    "Smart Assistant",
    "把模糊目標變成可執行待辦的智慧助手。",
    render_main,
    page_name=PAGE_NAME,
)
