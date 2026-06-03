from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import inject_style

st.set_page_config(page_title="餐廳點餐", page_icon="🍽️", layout="wide")
inject_style()

MENU = {
    "主餐": {
        "牛肉麵": 160,
        "雞腿飯": 150,
        "滷肉飯": 90,
    },
    "飲料": {
        "紅茶": 35,
        "奶茶": 45,
        "可樂": 40,
    },
    "甜點": {
        "布丁": 50,
        "蛋糕": 70,
        "冰淇淋": 60,
    },
}


def _format_menu_caption(items: dict[str, int]) -> str:
    return "\n".join([f"{name} NT{price}" for name, price in items.items()])


def _render_menu_selector() -> dict[str, list[str]]:
    st.markdown("#### 餐點選擇")
    selected: dict[str, list[str]] = {}
    cols = st.columns(3)
    for col, (category, items) in zip(cols, MENU.items()):
        with col:
            st.subheader(category)
            chosen = st.multiselect(
                f"選擇{category}",
                list(items.keys()),
                key=f"order_{category}",
            )
            selected[category] = chosen
            st.caption(_format_menu_caption(items))
    return selected


def _render_quantity_inputs(selected: dict[str, list[str]]) -> dict[str, int]:
    st.markdown("#### 數量設定")
    quantities: dict[str, int] = {}
    for category, items in MENU.items():
        if not selected.get(category):
            continue
        st.markdown(f"**{category}**")
        for item in selected[category]:
            quantities[item] = st.number_input(
                f"{item} 數量",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key=f"qty_{item}",
            )
    return quantities


def render_main() -> str:
    st.write("請先選擇主餐、飲料、甜點，再輸入每個餐點數量，最後按下送出訂單。")

    if "order_主餐" not in st.session_state:
        st.session_state["order_主餐"] = ["牛肉麵"]

    selected = _render_menu_selector()
    quantities = _render_quantity_inputs(selected)

    if "last_order" not in st.session_state:
        st.session_state.last_order = None

    submit = st.button("送出訂單", use_container_width=True)
    if submit:
        order_lines = []
        total = 0
        for category, items in MENU.items():
            for item in selected.get(category, []):
                qty = int(quantities.get(item, 1))
                price = items[item]
                subtotal = price * qty
                total += subtotal
                order_lines.append((category, item, qty, price, subtotal))

        st.session_state.last_order = {
            "lines": order_lines,
            "total": total,
        }
        st.success("訂單已送出！")

    if st.session_state.last_order:
        st.markdown("#### 訂單明細")
        lines = st.session_state.last_order["lines"]
        if lines:
            detail_text = []
            for category, item, qty, price, subtotal in lines:
                detail_text.append(f"- [{category}] {item} × {qty} = NT{subtotal}")
            detail_text.append(f"\n**總金額：NT{st.session_state.last_order['total']}**")
            st.markdown("\n".join(detail_text))
        else:
            st.write("尚未選擇任何餐點。")
    else:
        st.caption("送出訂單後會顯示明細與總金額。")

    return ""


page_shell(
    "餐廳點餐",
    "使用 multiselect、number_input、button、success、markdown/write 完成點餐頁面。",
    render_main,
    page_name="餐廳點餐",
)
