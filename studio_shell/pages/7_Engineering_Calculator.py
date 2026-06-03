from __future__ import annotations

import math
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import format_extra_context, inject_style


st.set_page_config(page_title="工程計算機", page_icon="🧮", layout="wide")
inject_style()

UNIT_FACTORS = {
    "長度": {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "in": 0.0254,
        "ft": 0.3048,
    },
    "面積": {
        "mm²": 0.000001,
        "cm²": 0.0001,
        "m²": 1.0,
        "km²": 1_000_000.0,
        "in²": 0.00064516,
        "ft²": 0.09290304,
    },
    "力": {
        "N": 1.0,
        "kN": 1000.0,
        "kgf": 9.80665,
        "lbf": 4.4482216153,
    },
    "壓力": {
        "Pa": 1.0,
        "kPa": 1000.0,
        "MPa": 1_000_000.0,
        "bar": 100_000.0,
        "psi": 6894.7572932,
    },
}


def _format_number(value: float) -> str:
    return f"{value:,.6g}"


def _render_unit_converter() -> str:
    st.markdown("#### 單位換算")
    category = st.selectbox("換算類型", list(UNIT_FACTORS.keys()))
    units = list(UNIT_FACTORS[category].keys())
    cols = st.columns(3)
    amount = cols[0].number_input("數值", value=1.0, format="%.6f")
    from_unit = cols[1].selectbox("從", units, key="eng_from_unit")
    to_unit = cols[2].selectbox("到", units, index=min(2, len(units) - 1), key="eng_to_unit")

    result = amount * UNIT_FACTORS[category][from_unit] / UNIT_FACTORS[category][to_unit]
    st.success(f"{_format_number(amount)} {from_unit} = {_format_number(result)} {to_unit}")
    return f"{amount} {from_unit} = {result} {to_unit}"


def _render_basic_calculator() -> str:
    st.markdown("#### 基礎計算工具")
    cols = st.columns(3)
    left = cols[0].number_input("數值 A", value=10.0, format="%.8f")
    operator = cols[1].selectbox("運算", ["+", "-", "×", "÷", "A^B", "√A"])
    right = cols[2].number_input("數值 B", value=2.0, format="%.8f", disabled=operator == "√A")

    if operator == "+":
        result = left + right
        formula = f"{left} + {right}"
    elif operator == "-":
        result = left - right
        formula = f"{left} - {right}"
    elif operator == "×":
        result = left * right
        formula = f"{left} * {right}"
    elif operator == "÷":
        result = left / right if right != 0 else math.nan
        formula = f"{left} / {right}"
    elif operator == "A^B":
        result = left**right
        formula = f"{left}^{right}"
    else:
        result = math.sqrt(left) if left >= 0 else math.nan
        formula = f"sqrt({left})"

    if math.isnan(result):
        st.error("此輸入無法計算，請檢查除數或根號內數值。")
    else:
        st.success(f"{formula} = {_format_number(result)}")
    return f"{formula} = {result}"


def _render_ohms_law() -> str:
    st.markdown("#### 歐姆定律")
    cols = st.columns(2)
    voltage = cols[0].number_input("電壓 V", value=12.0, format="%.6f")
    resistance = cols[1].number_input("電阻 Ω", min_value=0.000001, value=100.0, format="%.6f")

    current = voltage / resistance
    power = voltage * current
    st.metric("電流 I", f"{_format_number(current)} A")
    st.metric("功率 P", f"{_format_number(power)} W")
    return f"V={voltage} V, R={resistance} ohm, I={current} A, P={power} W"


def _render_beam_bending() -> str:
    st.markdown("#### 簡支梁中央集中載重")
    cols = st.columns(3)
    load = cols[0].number_input("集中載重 P (N)", min_value=0.0, value=1000.0, format="%.6f")
    span = cols[1].number_input("跨距 L (m)", min_value=0.000001, value=2.0, format="%.6f")
    inertia = cols[2].number_input("慣性矩 I (m⁴)", min_value=0.000000001, value=0.000001, format="%.9f")
    elastic_modulus = st.number_input("彈性模數 E (Pa)", min_value=0.000001, value=200_000_000_000.0, format="%.3f")

    max_moment = load * span / 4
    max_deflection = load * span**3 / (48 * elastic_modulus * inertia)
    metric_cols = st.columns(2)
    metric_cols[0].metric("最大彎矩", f"{_format_number(max_moment)} N·m")
    metric_cols[1].metric("中央撓度", f"{_format_number(max_deflection)} m")
    return f"P={load} N, L={span} m, E={elastic_modulus} Pa, I={inertia} m4, Mmax={max_moment} Nm, deflection={max_deflection} m"


def _render_stress_strain() -> str:
    st.markdown("#### 應力應變")
    cols = st.columns(3)
    force = cols[0].number_input("軸向力 F (N)", value=1000.0, format="%.6f")
    area = cols[1].number_input("截面積 A (m²)", min_value=0.000000001, value=0.0001, format="%.9f")
    length = cols[2].number_input("原長 L (m)", min_value=0.000001, value=1.0, format="%.6f")
    elongation = st.number_input("伸長量 ΔL (m)", value=0.001, format="%.9f")

    stress = force / area
    strain = elongation / length
    modulus = stress / strain if strain != 0 else math.nan

    metric_cols = st.columns(3)
    metric_cols[0].metric("應力 σ", f"{_format_number(stress)} Pa")
    metric_cols[1].metric("應變 ε", _format_number(strain))
    if math.isnan(modulus):
        metric_cols[2].metric("彈性模數 E", "無法計算")
    else:
        metric_cols[2].metric("彈性模數 E", f"{_format_number(modulus)} Pa")
    return f"F={force} N, A={area} m2, L={length} m, dL={elongation} m, stress={stress} Pa, strain={strain}, E={modulus} Pa"


def _render_geometry() -> str:
    st.markdown("#### 幾何計算")
    shape = st.selectbox("形狀", ["圓形", "矩形", "圓柱", "長方體"])

    if shape == "圓形":
        radius = st.number_input("半徑 r", min_value=0.0, value=5.0, format="%.6f")
        area = math.pi * radius**2
        perimeter = 2 * math.pi * radius
        st.metric("面積", _format_number(area))
        st.metric("周長", _format_number(perimeter))
        return f"circle r={radius}, area={area}, perimeter={perimeter}"

    if shape == "矩形":
        cols = st.columns(2)
        width = cols[0].number_input("寬 W", min_value=0.0, value=4.0, format="%.6f")
        height = cols[1].number_input("高 H", min_value=0.0, value=3.0, format="%.6f")
        area = width * height
        perimeter = 2 * (width + height)
        st.metric("面積", _format_number(area))
        st.metric("周長", _format_number(perimeter))
        return f"rectangle W={width}, H={height}, area={area}, perimeter={perimeter}"

    if shape == "圓柱":
        cols = st.columns(2)
        radius = cols[0].number_input("半徑 r", min_value=0.0, value=2.0, format="%.6f")
        height = cols[1].number_input("高度 H", min_value=0.0, value=6.0, format="%.6f")
        volume = math.pi * radius**2 * height
        surface = 2 * math.pi * radius * (radius + height)
        st.metric("體積", _format_number(volume))
        st.metric("表面積", _format_number(surface))
        return f"cylinder r={radius}, H={height}, volume={volume}, surface={surface}"

    cols = st.columns(3)
    width = cols[0].number_input("長 L", min_value=0.0, value=4.0, format="%.6f")
    depth = cols[1].number_input("寬 W", min_value=0.0, value=3.0, format="%.6f")
    height = cols[2].number_input("高 H", min_value=0.0, value=2.0, format="%.6f")
    volume = width * depth * height
    surface = 2 * (width * depth + width * height + depth * height)
    st.metric("體積", _format_number(volume))
    st.metric("表面積", _format_number(surface))
    return f"box L={width}, W={depth}, H={height}, volume={volume}, surface={surface}"


def _render_triangle() -> str:
    st.markdown("#### 三角函數")
    cols = st.columns(2)
    angle = cols[0].number_input("角度 θ (degree)", value=30.0, format="%.6f")
    hypotenuse = cols[1].number_input("斜邊長", min_value=0.0, value=10.0, format="%.6f")
    radians = math.radians(angle)
    opposite = hypotenuse * math.sin(radians)
    adjacent = hypotenuse * math.cos(radians)

    metric_cols = st.columns(2)
    metric_cols[0].metric("對邊", _format_number(opposite))
    metric_cols[1].metric("鄰邊", _format_number(adjacent))
    return f"theta={angle} deg, hypotenuse={hypotenuse}, opposite={opposite}, adjacent={adjacent}"


def render_main() -> str:
    st.markdown("#### 工程計算機")
    st.write("選擇計算類型，輸入數值後立即得到結果。")

    mode = st.tabs(["基礎計算", "單位換算", "歐姆定律", "梁彎曲", "應力應變", "幾何計算", "三角函數"])
    with mode[0]:
        basic_result = _render_basic_calculator()
    with mode[1]:
        result = _render_unit_converter()
    with mode[2]:
        ohm_result = _render_ohms_law()
    with mode[3]:
        beam_result = _render_beam_bending()
    with mode[4]:
        stress_result = _render_stress_strain()
    with mode[5]:
        geometry_result = _render_geometry()
    with mode[6]:
        triangle_result = _render_triangle()

    extra = format_extra_context(
        "工程計算機",
        基礎計算=basic_result,
        單位換算=result,
        歐姆定律=ohm_result,
        梁彎曲=beam_result,
        應力應變=stress_result,
        幾何計算=geometry_result,
        三角函數=triangle_result,
    )
    return extra


page_shell(
    "工程計算機",
    "常用工程單位換算與基礎公式計算。",
    render_main,
    page_name="工程計算機",
)
