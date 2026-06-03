from __future__ import annotations

import random
import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import inject_style

st.set_page_config(page_title="Playground", page_icon="🎛️", layout="wide")
inject_style()

MOOD_OPTIONS = ["😀 開心", "😐 普通", "😢 低落"]
DICE_FACE = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅",
}


def _roll_dice(count: int) -> list[int]:
    return [random.randint(1, 6) for _ in range(count)]


def _sync_dice_display(results: list[int]) -> None:
    st.session_state.playground_dice_results = results
    st.session_state.playground_dice_result = results[0] if results else 1
    st.session_state.playground_dice_faces = [DICE_FACE.get(n, "⚀") for n in results]


def render_main() -> str:
    st.markdown("#### 練習 1 · 心情儀表板")

    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input("暱稱", key="playground_nickname", placeholder="例如：小明")
    with col2:
        mood = st.radio("今天心情", MOOD_OPTIONS, horizontal=True, key="playground_mood")

    energy = st.slider("能量", min_value=1, max_value=10, value=5, key="playground_energy")
    event = st.text_area(
        "今天發生一件事（一句話）",
        placeholder="例如：段考結束了",
        key="playground_event",
    )

    st.divider()
    st.markdown("#### 互動骰子 🎲")
    if "playground_dice_result" not in st.session_state:
        st.session_state.playground_dice_result = 1
    if "playground_dice_results" not in st.session_state:
        st.session_state.playground_dice_results = [1]
    if "playground_dice_faces" not in st.session_state:
        st.session_state.playground_dice_faces = ["⚀"]
    if "playground_dice_history" not in st.session_state:
        st.session_state.playground_dice_history = []
    if "playground_dice_count" not in st.session_state:
        st.session_state.playground_dice_count = 1
    if "playground_dice_show_history" not in st.session_state:
        st.session_state.playground_dice_show_history = True

    dice_mode_col, dice_count_col = st.columns([2, 1])
    with dice_mode_col:
        st.session_state.playground_dice_count = st.radio(
            "骰子數量",
            [1, 2, 3],
            horizontal=True,
            key="playground_dice_count_radio",
        )
    with dice_count_col:
        st.caption("每次一起骰幾顆")

    current_results = st.session_state.playground_dice_results
    current_faces = st.session_state.playground_dice_faces
    if len(current_results) != st.session_state.playground_dice_count:
        current_results = [st.session_state.playground_dice_result] * st.session_state.playground_dice_count
        current_faces = [DICE_FACE.get(n, "⚀") for n in current_results]

    preview_cols = st.columns(st.session_state.playground_dice_count)
    for i, (col, face_value) in enumerate(zip(preview_cols, current_faces), start=1):
        with col:
            st.markdown(
                f"""
                <div style='text-align:center; font-size:64px; line-height:1.1;'>
                    {face_value}
                </div>
                <div style='text-align:center; font-size:16px; color:#666;'>
                    第 {i} 顆
                </div>
                """,
                unsafe_allow_html=True,
            )

    result_cols = st.columns([2, 1])
    if len(st.session_state.playground_dice_results) == st.session_state.playground_dice_count:
        result_text = "、".join(str(n) for n in st.session_state.playground_dice_results)
    else:
        result_text = str(st.session_state.playground_dice_result)
    result_cols[0].metric("目前骰子結果", result_text)

    roll_btn = result_cols[1].button("🎲 骰一下", use_container_width=True)
    if roll_btn:
        with st.spinner("骰子正在轉動..."):
            time.sleep(0.6)
        results = _roll_dice(st.session_state.playground_dice_count)
        _sync_dice_display(results)
        st.session_state.playground_dice_history.insert(0, results if len(results) > 1 else results[0])
        st.session_state.playground_dice_history = st.session_state.playground_dice_history[:10]
        st.rerun()

    st.caption("按下按鈕就會隨機骰出 1 到 6。多顆骰子會一起出結果。")

    history_toggle_col, _ = st.columns([1, 3])
    with history_toggle_col:
        st.session_state.playground_dice_show_history = st.checkbox(
            "顯示最近結果",
            value=st.session_state.playground_dice_show_history,
            key="playground_dice_show_history_checkbox",
        )

    if st.session_state.playground_dice_show_history and st.session_state.playground_dice_history:
        with st.expander("最近結果", expanded=True):
            for idx, item in enumerate(st.session_state.playground_dice_history[:5], start=1):
                if isinstance(item, list):
                    faces = " ".join(DICE_FACE.get(n, "⚀") for n in item)
                    st.write(f"{idx}. {faces}  →  {item}")
                else:
                    st.write(f"{idx}. {DICE_FACE.get(item, '⚀')}  →  {item}")

    st.divider()
    st.markdown("#### 計數器（AI coding 小練習）")
    if "playground_count" not in st.session_state:
        st.session_state.playground_count = 0

    metric_col, minus_col, plus_col = st.columns([2, 1, 1])
    metric_col.metric("Count", st.session_state.playground_count)

    if minus_col.button("-1", use_container_width=True):
        st.session_state.playground_count = max(0, st.session_state.playground_count - 1)
        st.rerun()

    if plus_col.button("+1", use_container_width=True):
        st.session_state.playground_count += 1
        st.rerun()

    st.caption("試著請 Agent 在 `pages/2_Playground.py` 加一個「-1」按鈕。")

    st.divider()
    st.markdown("#### 接線練習 · 用 Prompt 請 Agent 串接 Extra Context")
    st.info(
        "右欄 Agent 一開始還不一定知道左欄的暱稱、心情、能量、今日事件和計數器。"
        "你的任務是用清楚的 Prompt，請右欄 Agent 幫你把左欄資訊透過 Extra Context 串接過去。"
    )

    with st.expander("可以這樣跟右欄 Agent 說", expanded=True):
        st.markdown(
            """
先試試短版 Prompt：

```text
請用 Extra Context 的方式，將 Playground 左邊欄位的暱稱、心情、能量、今日事件、計數器，串接到右邊欄位的 Agent。
```

如果 Agent 沒有改完整，可以改用更明確的版本：

```text
請修改 `pages/2_Playground.py`，讓 `render_main()` 把左欄的暱稱、心情、能量、今日事件、計數器整理成 Extra Context，並回傳給右欄 Agent。

請參考 `pages/1_Home.py` 的寫法：
- 使用 `format_extra_context`
- 在畫面上顯示「給 Agent 的摘要」
- 最後 `return` 這段摘要

請不要修改 `studio_shell/agent_panel.py` 或 `studio_shell/page_shell.py`。
```
"""
        )

    summary = (
        f"暱稱：{nickname or '（未填）'}\n"
        f"心情：{mood}\n"
        f"能量：{energy}/10\n"
        f"今日事件：{event or '（未填）'}\n"
        f"計數器：{st.session_state.playground_count}\n"
        f"骰子結果：{result_text}"
    )

    st.markdown("#### 左欄狀態預覽")
    st.caption("這些內容會一併傳給右欄 Agent，作為 Extra Context。")
    st.json(
        {
            "暱稱": nickname or "（未填）",
            "心情": mood,
            "能量": f"{energy}/10",
            "今日事件": event or "（未填）",
            "計數器": st.session_state.playground_count,
            "骰子結果": result_text,
        }
    )

    st.markdown("#### 給 Agent 的摘要")
    st.code(summary, language="text")

    st.markdown("#### 右欄可以這樣問")
    st.markdown(
        """
接線完成後，改一下左欄的心情或能量，然後在右欄問：

- 「根據我的心情和能量，給我三個今晚可以放鬆的建議。」
- 「用鼓勵的語氣寫一段 50 字給我，不要說教。」

**驗收：** 接線後，改心情或能量 → 用同一句話問右欄 → 回答應跟著變。
"""
    )

    return summary


page_shell(
    "Playground",
    "練習用 Prompt 請右欄 Agent 把左欄狀態透過 Extra Context 串接過去。",
    render_main,
    page_name="Playground",
)
