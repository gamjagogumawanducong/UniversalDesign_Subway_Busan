import os
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="wide", page_title="부산 도시철도 유니버설 노선도")

st.markdown("""
    <style>
        .block-container {
            padding-top: 3.6rem;
            padding-bottom: 0.5rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
            max-width: 100%;
        }
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.4rem;
        }
    </style>
""", unsafe_allow_html=True)

# 4호선(#0054A6)과 동해선(#217DCB) 공식 색상 반영 및 색각 모드별 고명도대비 팔레트
PALETTES = {
    "기본": {
        "colors": {
            "1호선": "#F06A00", "2호선": "#81BF48", "3호선": "#BB8C00",
            "4호선": "#0054A6", "경전철": "#875CAC", "동해선": "#217DCB"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "부산교통공사 공식 지정 색상 (L·M·S 추상체 정상 삼색형 색각 기준)"
    },
    "적록색맹용": {
        "colors": {
            "1호선": "#E69F00",  # 고명도 황색 (L*=68)
            "2호선": "#005AB5",  # 저명도 진청색 (L*=38)
            "3호선": "#56B4E9",  # 중명도 하늘색 (L*=70)
            "4호선": "#1A237E",  # 초저명도 남색 (L*=20)
            "경전철": "#D4A017", # 중명도 황토색 (L*=65)
            "동해선": "#88CCEE"  # 고명도 담청색 (L*=78)
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "L·M 추상체 결핍 대응: 파랑-노랑 보색 축 + 교차 노선 간 명도(L*) 30% 이상 차등 설계"
    },
    "청황색맹용": {
        "colors": {
            "1호선": "#C2185B",  # 중저명도 진홍/마젠타 (L*=42)
            "2호선": "#00838F",  # 중명도 딥 시안 (L*=50)
            "3호선": "#F48FB1",  # 고명도 라이트 핑크 (L*=72)
            "4호선": "#111111",  # 최저명도 블랙 (L*=10)
            "경전철": "#6A1B4D", # 저명도 딥 버건디 (L*=28)
            "동해선": "#4DD0E1"  # 고명도 밝은 시안 (L*=78)
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "S 추상체 결핍 대응: 청황 축 배제 후 마젠타-시안 대비 + 동해선/2호선 명도 격차 극대화"
    },
    "전색맹용": {
        "colors": {
            "1호선": "#111111",  # 명도 10% (검정)
            "2호선": "#484848",  # 명도 30% (진회색)
            "3호선": "#767676",  # 명도 50% (중간회색)
            "4호선": "#9E9E9E",  # 명도 65% (밝은회색)
            "경전철": "#2E2E2E", # 명도 20% (암회색)
            "동해선": "#616161"  # 명도 40% (회색)
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "전색맹 대응: 채도 0% 무채색 명도 단계화 + 선 패턴(실선·점선·파선) 이중 부호화 적용"
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
if "last_click_id" not in st.session_state:
    st.session_state.last_click_id = None

col_title, col_b1, col_b2, col_b3 = st.columns((6.4, 1.2, 1.2, 1.2))
current_palette = PALETTES.get(st.session_state.color_mode)

with col_title:
    st.markdown(f"#### 🚇 부산 도시철도 유니버설 노선도 &nbsp; `현재: {st.session_state.color_mode}`")
    st.caption(f"🎨 {current_palette.get('desc')}")

all_modes = ("기본", "적록색맹용", "청황색맹용", "전색맹용")
available_modes = tuple(m for m in all_modes if m != st.session_state.color_mode)

for col, mode_name in zip((col_b1, col_b2, col_b3), available_modes):
    with col:
        if st.button(mode_name, use_container_width=True):
            st.session_state.color_mode = mode_name
            st.rerun()

# 공식 노선도 구조 반영: 2호선(수영-민락-센텀시티-벡스코)과 동해선 분리 및 4호선 안평 종점 정확히 일치
LINES_PATH = {
    "1호선": ((12, 18), (12, 8), (15, 6), (55, 6), (58, 8), (58, 58)),
    "2호선": ((36, 58), (36, 24), (39, 21), (63, 21), (66, 18), (66, 11), (69, 9), (80, 9), (83, 11), (83, 32), (91, 32), (94, 34), (94, 36), (105, 36), (108, 39), (108, 43)),
    "3호선": ((24, 38), (27, 40), (51, 40), (54, 38), (54, 32), (58, 29), (80, 29), (83, 27)),
    "4호선": ((51, 36), (54, 40), (80, 40), (83, 42), (83, 58)),
    "경전철": ((12, 58), (12, 43), (15, 41), (24, 38), (24, 26), (27, 24), (34, 24), (36, 26)),
    "동해선": ((55, 24), (58, 26), (58, 35), (61, 37), (91, 37), (94, 36), (97, 39), (97, 55), (100, 57), (114, 57))
}

STATIONS = {
    "다대포해수욕장": (12, 18, "1호선", "4개", False, "top center", (
        ("1호선", "기점 -> 다대포해수욕장(095) -> 다대포항"),
    )),
    "서면": (58, 21, "1호선 · 2호선", "15개", True, "bottom right", (
        ("1호선", "범내골 -> 서면(119) -> 부전"),
        ("2호선", "전포 -> 서면(219) -> 부암"),
    )),
    "연산": (58, 29, "1호선 · 3호선", "17개", True, "bottom right", (
        ("1호선", "시청 -> 연산(123) -> 교대"),
        ("3호선", "물만골 -> 연산(305) -> 거제"),
    )),
    "교대": (58, 35, "1호선 · 동해선", "8개", True, "middle right", (
        ("1호선", "연산 -> 교대(124) -> 동래"),
        ("동해선", "거제 -> 교대(K113) -> 동래"),
    )),
    "동래": (58, 40, "1호선 · 4호선", "4개", True, "top left", (
        ("1호선", "교대 -> 동래(125) -> 명륜"),
        ("4호선", "미남 -> 동래(402) -> 수안"),
    )),
    "노포": (58, 58, "1호선", "3개", False, "middle left", (
        ("1호선", "범어사 -> 노포(134) -> 종점"),
    )),
    "양산": (36, 58, "2호선", "4개", False, "middle right", (
        ("2호선", "남양산 -> 양산(243) -> 종점"),
    )),
    "덕천": (36, 40, "2호선 · 3호선", "12개", True, "bottom right", (
        ("2호선", "구명 -> 덕천(233) -> 수정"),
        ("3호선", "숙등 -> 덕천(313) -> 구포"),
    )),
    "사상": (36, 26, "2호선 · 부산김해경전철", "6개", True, "bottom left", (
        ("2호선", "감전 -> 사상(227) -> 덕포"),
        ("부산김해경전철", "기점 -> 사상(1) -> 괘법르네시떼"),
    )),
    "수영": (83, 27, "2호선 · 3호선", "17개", True, "middle right", (
        ("2호선", "광안 -> 수영(208) -> 민락"),
        ("3호선", "기점 -> 수영(301) -> 망미"),
    )),
    "벡스코": (94, 36, "2호선 · 동해선", "9개", True, "bottom right", (
        ("2호선", "센텀시티 -> 벡스코(205) -> 동백"),
        ("동해선", "센텀 -> 벡스코(K119) -> 신해운대"),
    )),
    "장산": (108, 43, "2호선", "14개", False, "top center", (
        ("2호선", "기점 -> 장산(201) -> 중동"),
    )),
    "대저": (24, 38, "3호선 · 부산김해경전철", "3개", True, "middle left", (
        ("3호선", "체육공원 -> 대저(317) -> 종점"),
        ("부산김해경전철", "등구 -> 대저(7) -> 평강"),
    )),
    "미남": (51, 36, "3호선 · 4호선", "14개", True, "bottom left", (
        ("3호선", "사직 -> 미남(309) -> 만덕"),
        ("4호선", "기점 -> 미남(401) -> 동래"),
    )),
    "거제": (54, 32, "3호선 · 동해선", "8개", True, "middle left", (
        ("3호선", "연산 -> 거제(306) -> 종합운동장"),
        ("동해선", "거제해맞이 -> 거제(K112) -> 교대"),
    )),
    "안평": (83, 58, "4호선", "4개", False, "middle right", (
        ("4호선", "고촌 -> 안평(414) -> 종점"),
    )),
    "가야대": (12, 58, "부산김해경전철", "2개", False, "middle right", (
        ("부산김해경전철", "장신대 -> 가야대(21) -> 종점"),
    )),
    "부전": (55, 24, "동해선 (1호선 인근)", "2개", False, "middle left", (
        ("동해선", "기점 -> 부전(K110) -> 거제해맞이"),
    )),
    "태화강": (114, 57, "동해선", "2개", False, "top center", (
        ("동해선", "개운포 -> 태화강(K132) -> 종점"),
    )),
}

colors = current_palette.get("colors")
dashes = LINE_DASH.get(st.session_state.color_mode)

def get_station_border_color(station_tuple):
    is_transfer = station_tuple.__getitem__(4)
    if is_transfer:
        return "#111111"
    first_line = station_tuple.__getitem__(2).split(" ").__getitem__(0)
    if first_line == "부산김해경전철":
        first_line = "경전철"
    return colors.get(first_line, "#111111")

@st.dialog("🚉 역 상세 정보 안내", width="small")
def show_station_popup(station_name):
    x, y, line_info, exits, is_transfer, _, route_flows = STATIONS.get(station_name)

    badge = "🔄 핵심 환승역" if is_transfer else "🚩 기점 / 종점"
    st.markdown(f"### {station_name}역 &nbsp; `{badge}`")

    img_path = None
    for ext in ("jpg", "png", "jpeg"):
        candidate = os.path.join("images", f"{station_name}.{ext}")
        if os.path.exists(candidate):
            img_path = candidate
            break

    if img_path:
        st.image(img_path, use_container_width=True)
    else:
        st.image(
            f"https://placehold.co{station_name}+Station",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown(f"**• 운행 노선:** {line_info}")
    st.markdown("**• 방면 및 역 번호:**")
    for line_label, flow_text in route_flows:
        st.markdown(f"&nbsp;&nbsp;&nbsp;- **{line_label}**: `{flow_text}`")
    st.markdown(f"**• 출구 개수:** {exits}")

fig = go.Figure()

for line_name, coords in LINES_PATH.items():
    xs = tuple(x for x, y in coords)
    ys = tuple(y for x, y in coords)
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        name=line_name,
        line=dict(color=colors.get(line_name), width=7, dash=dashes.get(line_name)),
        hoverinfo="skip"
    ))

st_names = tuple(STATIONS.keys())
st_xs = tuple(STATIONS.get(s).__getitem__(0) for s in st_names)
st_ys = tuple(STATIONS.get(s).__getitem__(1) for s in st_names)
st_sizes = tuple(15 if STATIONS.get(s).__getitem__(4) else 12 for s in st_names)
st_border_colors = tuple(get_station_border_color(STATIONS.get(s)) for s in st_names)
st_positions = tuple(STATIONS.get(s).__getitem__(5) for s in st_names)

fig.add_trace(go.Scatter(
    x=st_xs, y=st_ys,
    mode="markers+text",
    name="역 선택 (클릭)",
    text=st_names,
    textposition=st_positions,
    textfont=dict(size=12, color=current_palette.get("text"), family="Malgun Gothic, AppleGothic, sans-serif"),
    marker=dict(
        size=st_sizes,
        color="#FFFFFF",
        line=dict(color=st_border_colors, width=3.2)
    ),
    hovertemplate="<b>%{text}역</b> (클릭하여 정보 열기)<extra></extra>"
))

fig.update_layout(
    plot_bgcolor=current_palette.get("bg"),
    paper_bgcolor=current_palette.get("bg"),
    xaxis=dict(visible=False, range=(2, 124), fixedrange=False),
    yaxis=dict(visible=False, range=(2, 64), fixedrange=False),
    height=530,
    margin=dict(l=5, r=5, t=5, b=5),
    hovermode="closest",
    hoverdistance=15,
    legend=dict(
        orientation="h",
        yanchor="bottom", y=0.01,
        xanchor="left", x=0.01,
        bgcolor="rgba(255,255,255,0.92)",
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
    override_height=530,
    key=f"map_{st.session_state.color_mode}"
)

if clicked:
    first_click = clicked.__getitem__(0)
    cx, cy = first_click.get("x"), first_click.get("y")
    click_token = f"{cx}_{cy}_{st.session_state.color_mode}"
    closest = min(st_names, key=lambda s: (STATIONS.get(s).__getitem__(0) - cx)**2 + (STATIONS.get(s).__getitem__(1) - cy)**2)
    if st.session_state.last_click_id != click_token:
        st.session_state.last_click_id = click_token
        show_station_popup(closest)
