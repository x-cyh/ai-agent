from __future__ import annotations

from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'pages' / '4_Restaurant_Order.py'
text = path.read_text(encoding='utf-8')

needle = '    st.write("請先選擇主餐、飲料、甜點，再輸入每個餐點數量，最後按下送出訂單。")\n\n    selected = _render_menu_selector()\n'
replacement = '    st.write("請先選擇主餐、飲料、甜點，再輸入每個餐點數量，最後按下送出訂單。")\n\n    if "order_主餐" not in st.session_state:\n        st.session_state["order_主餐"] = ["牛肉麵"]\n\n    selected = _render_menu_selector()\n'

if needle not in text:
    raise SystemExit('needle not found')
path.write_text(text.replace(needle, replacement, 1), encoding='utf-8')
print('updated', path)
