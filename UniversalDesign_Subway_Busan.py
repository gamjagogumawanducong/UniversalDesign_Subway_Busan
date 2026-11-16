import os
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="부산 도시철도 유니버설 노선도")

# Streamlit 상단 툴바에 가려지지 않도록 padding-top을 3.6rem으로 확보
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

# 2. 색각 유형별 컬러 팔레트 및 색채학적 설계 근거
PALETTES = {
    "기본": {
        "colors": {
            "1호선": "#F06A00", "2호선": "#81BF48", "3호선": "#BB8C00",
            "4호선": "#217DCB", "경전철": "#875CAC", "동해선": "#0054A6"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "부산교통공사 공식 지정 색상 (L·M·S 추상체 정상 삼색형 색각 기준)"
    },
    "적록색맹용": {
        "colors": {
            "1호선": "#E69F00", "2호선": "#56B4E9", "3호선": "#0072B2",
            "4호선": "#CC79A7", "경전철": "#332288", "동해선": "#009E73"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "L·M 추상체 결핍(적록색맹) 대응: 적·녹 혼동을 배제한 파랑-노랑 대비 및 명도 차이 적용"
    },
    "청황색맹용": {
        "colors": {
            "1호선": "#D55E00", "2호선": "#009E73", "3호선": "#CC79A7",
            "4호선": "#111111", "경전철": "#882255", "동해선": "#44AA99"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "S 추상체 결핍(청황색맹) 대응: 파랑-노랑 축 혼동을 피하는 진홍(Magenta)-청록(Cyan) 대비 적용"
    },
    "전색맹용": {
        "colors": {
            "1호선": "#111111", "2호선": "#444444", "3호선": "#757575",
            "4호선": "#9E9E9E", "경전철": "#2B2B2B", "동해선": "#5E5E5E"
        },
        "bg": "#FFFFFF",
        "text": "#111111",
        "desc": "전색맹(추상체 기능 저하) 대응: 20% 이상 벌린 단계별 명도(Luminance) 대비 + 선 패턴(실선·점선) 구분"
    }
}

LINE_DASH = {
    "기본": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "적록색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "청황색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "전색맹용": {"1호선": "solid", "2호선": "dash", "3호선": "dot", "4호선": "dashdot", "경전철": "longdash", "동해선": "longdashdot"},
}

# 3. 세션 상태 초기화
if "color_mode" not in st.session_state:
    st.session_state.color_mode = "기본"
if "last_click_id" not in st.session_state:
    st.session_state.last_click_id = None

# 4. 상단 바: 제목 + 현재 색각 설계 요약 + 우측 상단 동적 전환 버튼 3개
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

# 5. 노트북 가로 화면(16:9)에 맞는 노선 좌표
LINES_PATH = {
    "1호선": ((12, 18), (12, 8), (15, 6), (55, 6), (58, 8), (58, 58)),
    "2호선": ((36, 58), (36, 24), (39, 21), (63, 21), (66, 18), (66, 12), (69, 10), (80, 10), (83, 12), (83, 36), (105, 36), (108, 39), (108, 43)),
    "3호선": ((24, 36), (27, 38), (51, 38), (54, 36), (54, 32), (58, 29), (80, 29), (83, 27)),
    "4호선": ((51, 34), (54, 36), (80, 36), (83, 38), (83, 58)),
    "경전철": ((12, 58), (12, 41), (15, 39), (24, 36), (24, 26), (27, 24), (34, 24), (36, 26)),
    "동해선": ((55, 24), (58, 26), (58, 34), (61, 36), (91, 36), (94, 38), (94, 55), (97, 57), (112, 57))
}

# 6. 주요 역(Vertex) 데이터
# 형식: "역이름": (x, y, 호선목록, 출구수, 환승여부, 라벨위치, (노선별 진행방향 및 역번호 튜플))
STATIONS = {
    # 1호선
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
    "교대": (58, 34, "1호선 · 동해선", "8개", True, "top right", (
        ("1호선", "연산 -> 교대(124) -> 동래"),
        ("동해선", "거제 -> 교대(K113) -> 동래"),
    )),
    "동래": (58, 38, "1호선 · 4호선", "4개", True, "top left", (
        ("1호선", "교대 -> 동래(125) -> 명륜"),
        ("4호선", "미남 -> 동래(402) -> 수안"),
    )),
    "노포": (58, 58, "1호선", "3개", False, "middle left", (
        ("1호선", "범어사 -> 노포(134) -> 종점"),
    )),

    # 2호선
    "양산": (36, 58, "2호선", "4개", False, "middle right", (
        ("2호선", "남양산 -> 양산(243) -> 종점"),
    )),
    "덕천": (36, 38, "2호선 · 3호선", "12개", True, "bottom right", (
        ("2호선", "구명 -> 덕천(233) -> 수정"),
        ("3호선", "숙등 -> 덕천(313) -> 구포"),
    )),
    "사상": (36, 26, "2호선 · 부산김해경전철", "6개", True, "bottom left", (
        ("2호선", "감전 -> 사상(227) -> 덕포"),
        ("부산김해경전철", "기점 -> 사상(1) -> 괘법르네시떼"),
    )),
    "수영": (83, 27, "2호선 · 3호선", "17개", True, "middle right", (
        ("2호선", "민락 -> 수영(208) -> 광안"),
        ("3호선", "기점 -> 수영(301) -> 망미"),
    )),
    "벡스코": (94, 36, "2호선 · 동해선", "9개", True, "bottom right", (
        ("2호선", "센텀시티 -> 벡스코(205) -> 동백"),
        ("동해선", "센텀 -> 벡스코(K119) -> 신해운대"),
    )),
    "장산": (108, 43, "2호선", "14개", False, "top center", (
        ("2호선", "기점 -> 장산(201) -> 중동"),
    )),

    # 3호선
    "대저": (24, 36, "3호선 · 부산김해경전철", "3개", True, "middle left", (
        ("3호선", "체육공원 -> 대저(317) -> 종점"),
        ("부산김해경전철", "등구 -> 대저(7) -> 평강"),
    )),
    "미남": (51, 38, "3호선 · 4호선", "14개", True, "top left", (
        ("3호선", "사직 -> 미남(309) -> 만덕"),
        ("4호선", "기점 -> 미남(401) -> 동래"),
    )),
    "거제": (54, 32, "3호선 · 동해선", "8개", True, "middle left", (
        ("3호선", "연산 -> 거제(306) -> 종합운동장"),
        ("동해선", "거제해맞이 -> 거제(K112) -> 교대"),
    )),

    # 4호선
    "안평": (83, 58, "4호선", "4개", False, "middle right", (
        ("4호선", "고촌 -> 안평(414) -> 종점"),
    )),

    # 부산김해경전철
    "가야대": (12, 58, "부산김해경전철", "2개", False, "middle right", (
        ("부산김해경전철", "장신대 -> 가야대(21) -> 종점"),
    )),

    # 동해선
    "부전": (55, 24, "동해선 (1호선 인근)", "2개", False, "middle left", (
        ("동해선", "기점 -> 부전(K110) -> 거제해맞이"),
    )),
    "태화강": (112, 57, "동해선", "2개", False, "top center", (
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

# 7. 나무위키 주석 스타일의 팝업 다이얼로그 정의
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

# 8. 화면 전체 너비(100%)로 벡터 노선도 렌더링 (스크롤 없이 한눈에)
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
    xaxis=dict(visible=False, range=(2, 122), fixedrange=False),
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
first_click = clicked.getitem(0)
cx, cy = first_click.get("x"), first_click.get("y")
click_token = f"{cx}{cy}{st.session_state.color_mode}"
closest = min(st_names, key=lambda s: (STATIONS.get(s).getitem(0) - cx)2 + (STATIONS.get(s).getitem(1) - cy)2)
if st.session_state.last_click_id != click_token:
st.session_state.last_click_id = click_token
show_station_popup(closest)

