import os
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="wide", page_title="부산 도시철도 유니버설 노선도")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 0rem;
            padding-left: 1.8rem;
            padding-right: 1.8rem;
        }
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

PALETTES = {
    "기본": {
        "colors": {
            "1호선": "#F06A00", "2호선": "#81BF48", "3호선": "#BB8C00",
            "4호선": "#217DCB", "경전철": "#875CAC", "동해선": "#0054A6"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "부산교통공사 공식 지정 색상입니다. 일반 삼색형 색각(L·M·S 추상체 정상) 기준의 표준 노선도입니다."
    },
    "적록색맹용": {
        "colors": {
            "1호선": "#E69F00", "2호선": "#56B4E9", "3호선": "#0072B2",
            "4호선": "#CC79A7", "경전철": "#332288", "동해선": "#009E73"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "L·M 추상체 결핍(적록색맹) 대응 팔레트입니다. 혼동되기 쉬운 적·녹 계열을 배제하고 파랑-노랑 보색 대비와 명도 차이를 극대화했습니다."
    },
    "청황색맹용": {
        "colors": {
            "1호선": "#D55E00", "2호선": "#009E73", "3호선": "#CC79A7",
            "4호선": "#111111", "경전철": "#882255", "동해선": "#44AA99"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "S 추상체 결핍(청황색맹) 대응 팔레트입니다. 파랑-노랑 축의 혼동을 막기 위해 진홍(Magenta)과 청록(Cyan) 계열의 대비를 적용했습니다."
    },
    "전색맹용": {
        "colors": {
            "1호선": "#111111", "2호선": "#444444", "3호선": "#757575",
            "4호선": "#9E9E9E", "경전철": "#2B2B2B", "동해선": "#5E5E5E"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "추상체 기능 저하(전색맹) 대응 팔레트입니다. 색상 대신 단계별 명도(Luminance) 대비와 선 패턴(실선·점선·파선)으로 노선을 구분합니다."
    }
}

LINE_DASH = {
    "기본": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "적록색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "청황색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "전색맹용": {"1호선": "solid", "2호선": "dash", "3호선": "dot", "4호선": "dashdot", "경전철": "longdash", "동해선": "longdashdot"},
}

if "color_mode" not in st.session_state:
    st.session_state.color_mode = "기본"
if "selected_station" not in st.session_state:
    st.session_state.selected_station = "서면"

col_title, col_b1, col_b2, col_b3 = st.columns((6.1, 1.3, 1.3, 1.3))
with col_title:
    st.markdown(f"### 🚇 부산 도시철도 유니버설 노선도 &nbsp; `현재 모드: {st.session_state.color_mode}`")

all_modes = ("기본", "적록색맹용", "청황색맹용", "전색맹용")
available_modes = tuple(m for m in all_modes if m != st.session_state.color_mode)

for col, mode_name in zip((col_b1, col_b2, col_b3), available_modes):
    with col:
        if st.button(mode_name, use_container_width=True):
            st.session_state.color_mode = mode_name
            st.rerun()

LINES_PATH = {
    "1호선": ((10, 22), (10, 8), (12, 6), (48, 6), (50, 8), (50, 85)),
    "2호선": ((30, 85), (30, 32), (33, 29), (53, 29), (55, 27), (55, 14), (57, 12), (68, 12), (70, 14), (70, 50), (88, 50), (90, 52), (90, 56)),
    "3호선": ((21, 50), (23, 52), (45, 52), (47, 50), (47, 45), (50, 42), (68, 42), (70, 40)),
    "4호선": ((45, 48), (47, 50), (68, 50), (70, 52), (70, 85)),
    "경전철": ((11, 85), (11, 56), (13, 54), (20, 50), (20, 35), (22, 33), (28, 33), (30, 35)),
    "동해선": ((48, 35), (50, 37), (50, 48), (52, 50), (76, 50), (78, 52), (78, 82), (80, 84), (92, 84))
}

STATIONS = {
    "다대포해수욕장": (10, 22, "1호선", "095", "4개", False, "middle left"),
    "서면": (50, 29, "1호선 · 2호선", "119 / 219", "15개", True, "bottom right"),
    "연산": (50, 42, "1호선 · 3호선", "123 / 305", "17개", True, "bottom right"),
    "교대": (50, 48, "1호선 · 동해선", "124 / K113", "8개", True, "top right"),
    "동래": (50, 52, "1호선 · 4호선", "125 / 402", "4개", True, "top left"),
    "노포": (50, 85, "1호선", "134", "3개", False, "middle left"),
    "양산": (30, 85, "2호선", "243", "4개", False, "middle right"),
    "덕천": (30, 52, "2호선 · 3호선", "233 / 313", "12개", True, "bottom right"),
    "사상": (30, 35, "2호선 · 부산김해경전철", "227 / 1", "6개", True, "bottom left"),
    "수영": (70, 40, "2호선 · 3호선", "208 / 301", "17개", True, "middle right"),
    "벡스코": (78, 50, "2호선 · 동해선", "205 / K119", "9개", True, "bottom right"),
    "장산": (90, 56, "2호선", "201", "14개", False, "top left"),
    "대저": (21, 50, "3호선 · 부산김해경전철", "317 / 7", "3개", True, "middle left"),
    "미남": (45, 52, "3호선 · 4호선", "309 / 401", "14개", True, "top left"),
    "거제": (47, 45, "3호선 · 동해선", "306 / K112", "8개", True, "middle left"),
    "안평": (70, 85, "4호선", "414", "4개", False, "middle right"),
    "가야대": (11, 85, "부산김해경전철", "21", "2개", False, "middle right"),
    "부전": (48, 35, "동해선 (1호선 인근)", "K110", "2개", False, "middle left"),
    "태화강": (92, 84, "동해선", "K132", "2개", False, "top center"),
}

current_palette = PALETTES.get(st.session_state.color_mode)
colors = current_palette.get("colors")
dashes = LINE_DASH.get(st.session_state.color_mode)

def get_station_border_color(station_tuple):
    is_transfer = station_tuple.__getitem__(5)
    if is_transfer:
        return "#111111"
    first_line = station_tuple.__getitem__(2).split(" ").__getitem__(0)
    if first_line == "부산김해경전철":
        first_line = "경전철"
    return colors.get(first_line, "#111111")

col_map, col_info = st.columns((7.6, 2.4))

with col_map:
    fig = go.Figure()

    for line_name, coords in LINES_PATH.items():
        xs = tuple(x for x, y in coords)
        ys = tuple(y for x, y in coords)
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            name=line_name,
            line=dict(color=colors.get(line_name), width=7.5, dash=dashes.get(line_name)),
            hoverinfo="skip"
        ))

    st_names = tuple(STATIONS.keys())
    st_xs = tuple(STATIONS.get(s).__getitem__(0) for s in st_names)
    st_ys = tuple(STATIONS.get(s).__getitem__(1) for s in st_names)
    st_sizes = tuple(16 if STATIONS.get(s).__getitem__(5) else 12 for s in st_names)
    st_border_colors = tuple(get_station_border_color(STATIONS.get(s)) for s in st_names)
    st_positions = tuple(STATIONS.get(s).__getitem__(6) for s in st_names)

    fig.add_trace(go.Scatter(
        x=st_xs, y=st_ys,
        mode="markers+text",
        name="주요 역 (클릭)",
        text=st_names,
        textposition=st_positions,
        textfont=dict(size=12, color=current_palette.get("text"), family="Malgun Gothic, AppleGothic, sans-serif"),
        marker=dict(
            size=st_sizes,
            color="#FFFFFF",
            line=dict(color=st_border_colors, width=3.5)
        ),
        hovertemplate="<b>%{text}역</b><br>클릭하여 상세정보 보기<extra></extra>"
    ))

    fig.update_layout(
        plot_bgcolor=current_palette.get("bg"),
        paper_bgcolor=current_palette.get("bg"),
        xaxis=dict(visible=False, range=(0, 100), fixedrange=False),
        yaxis=dict(visible=False, range=(0, 95), fixedrange=False, scaleanchor="x", scaleratio=1),
        height=720,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=0.01,
            xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#DDDDDD",
            borderwidth=1
        ),
        dragmode="pan"
    )

    clicked = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=720,
        key=f"map_{st.session_state.color_mode}"
    )

    if clicked:
        first_click = clicked.__getitem__(0)
        cx, cy = first_click.get("x"), first_click.get("y")
        closest = min(st_names, key=lambda s: (STATIONS.get(s).__getitem__(0) - cx)**2 + (STATIONS.get(s).__getitem__(1) - cy)**2)
        if st.session_state.selected_station != closest:
            st.session_state.selected_station = closest
            st.rerun()

with col_info:
    sel = st.session_state.selected_station
    x, y, line_info, st_num, exits, is_transfer, _ = STATIONS.get(sel)

    st.markdown(f"#### 📍 {sel}역")
    if is_transfer:
        st.caption("🔄 핵심 환승역")
    else:
        st.caption("🚉 기점 / 종점")

    img_path = None
    for ext in ("jpg", "png", "jpeg"):
        candidate = os.path.join("images", f"{sel}.{ext}")
        if os.path.exists(candidate):
            img_path = candidate
            break

    if img_path:
        st.image(img_path, use_container_width=True)
    else:
        st.image(
            f"https://placehold.co{sel}+Station",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown(f"**• 운행 노선:** {line_info}")
    st.markdown(f"**• 역 번호:** {st_num}")
    st.markdown(f"**• 출구 개수:** {exits}")
    st.markdown("---")

    st.markdown(f"**🎨 {st.session_state.color_mode} 설계 기준**")
    st.info(current_palette.get("desc"))
    st.caption("💡 노선도의 원(역)을 클릭하면 정보가 바뀌며, 마우스 휠로 확대·축소할 수 있습니다.")
