import os
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="부산 도시철도 유니버설 노선도")

st.components.v1.html('<script src="https://plot.ly"></script>', height=0)

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
        a[data-testid="stHeaderActionElements"],
        .stMarkdown a.anchor-link {
            display: none !important;
        }
        .header-wrap {
            display: flex;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
        }
        .header-title {
            font-size: 1.85rem;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.25;
        }
        .mode-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 15px;
            border-radius: 999px;
            font-size: 0.92rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .mode-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

PALETTES = {
    "기본": {
        "colors": {
            "1호선": "#F06A00", "2호선": "#81BF48", "3호선": "#BB8C00",
            "4호선": "#0054A6", "경전철": "#875CAC", "동해선": "#217DCB"
        },
        "outline": "#1F2937",
        "badge_bg": "#FFF4E6",
        "badge_text": "#D9480F",
        "badge_border": "#FFD8A8",
        "bg": "#FFFFFF",
        "text": "#111111"
    },
    "적록색맹용": {
        "colors": {
            "1호선": "#E69F00", "2호선": "#004C99", "3호선": "#56B4E9",
            "4호선": "#111844", "경전철": "#C88A04", "동해선": "#80C8F0"
        },
        "outline": "#111111",
        "badge_bg": "#E7F5FF",
        "badge_text": "#1864AB",
        "badge_border": "#A5D8FF",
        "bg": "#FFFFFF",
        "text": "#111111"
    },
    "청황색맹용": {
        "colors": {
            "1호선": "#B80D48", "2호선": "#007A87", "3호선": "#F06292",
            "4호선": "#111111", "경전철": "#5C0931", "동해선": "#4DD0E1"
        },
        "outline": "#111111",
        "badge_bg": "#FFF0F6",
        "badge_text": "#A61E4D",
        "badge_border": "#FCC2D7",
        "bg": "#FFFFFF",
        "text": "#111111"
    },
    "전색맹용": {
        "colors": {
            "1호선": "#111111", "2호선": "#3B3B3B", "3호선": "#666666",
            "4호선": "#8C8C8C", "경전철": "#242424", "동해선": "#525252"
        },
        "outline": "#000000",
        "badge_bg": "#F1F3F5",
        "badge_text": "#212529",
        "badge_border": "#CED4DA",
        "bg": "#FFFFFF",
        "text": "#111111"
    }
}

LINE_DASH = {
    "기본": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "적록색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "청황색맹용": {"1호선": "solid", "2호선": "solid", "3호선": "solid", "4호선": "solid", "경전철": "solid", "동해선": "solid"},
    "전색맹용": {
        "1호선": "solid",
        "2호선": "16px,6px",
        "3호선": "4px,5px",
        "4호선": "16px,5px,4px,5px",
        "경전철": "26px,7px",
        "동해선": "10px,4px,3px,4px,3px,4px"
    },
}

if "color_mode" not in st.session_state:
    st.session_state.color_mode = "기본"
if "last_click_id" not in st.session_state:
    st.session_state.last_click_id = None

col_title, col_b1, col_b2, col_b3 = st.columns((6.4, 1.2, 1.2, 1.2))
current_palette = PALETTES.get(st.session_state.color_mode)

with col_title:
    st.markdown(f"""
        <div class="header-wrap">
            <div class="header-title">🚇 부산 도시철도 유니버설 노선도</div>
            <span class="mode-badge" style="background-color:{current_palette.get('badge_bg')}; color:{current_palette.get('badge_text')}; border:1.5px solid {current_palette.get('badge_border')};">
                <span class="mode-dot" style="background-color:{current_palette.get('badge_text')};"></span>
                {st.session_state.color_mode} 모드
            </span>
        </div>
    """, unsafe_allow_html=True)

all_modes = ("기본", "적록색맹용", "청황색맹용", "전색맹용")
available_modes = tuple(m for m in all_modes if m != st.session_state.color_mode)

for col, mode_name in zip((col_b1, col_b2, col_b3), available_modes):
    with col:
        if st.button(mode_name, use_container_width=True):
            st.session_state.color_mode = mode_name
            st.rerun()

LINES_PATH = {
    "1호선": ((12, 18), (12, 8), (15, 6), (55, 6), (58, 8), (58, 58)),
    "2호선": ((36, 58), (36, 24), (39, 21), (63, 21), (66, 18), (66, 11), (69, 9), (80, 9), (83, 11), (83, 32), (91, 32), (94, 34), (94, 36), (105, 36), (108, 39), (108, 43)),
    "3호선": ((24, 38), (27, 40), (51, 40), (54, 38), (54, 32), (58, 29), (80, 29), (83, 27)),
    "4호선": ((51, 36), (54, 40), (80, 40), (83, 42), (83, 58)),
    "경전철": ((12, 58), (12, 43), (15, 41), (24, 38), (24, 26), (27, 24), (34, 24), (36, 26)),
    "동해선": ((55, 24), (58, 26), (58, 35), (61, 37), (91, 37), (94, 36), (97, 39), (97, 55), (100, 57), (114, 57))
}

STATIONS = {
    "다대포해수욕장": (12, 18, "1호선", "4개", False, "top center", "1", (
        ("1호선", "기점 -> 다대포해수욕장(095) -> 다대포항"),
    )),
    "서면": (58, 21, "1호선 · 2호선", "15개", True, "bottom right", "환", (
        ("1호선", "범내골 -> 서면(119) -> 부전"),
        ("2호선", "전포 -> 서면(219) -> 부암"),
    )),
    "연산": (58, 29, "1호선 · 3호선", "17개", True, "bottom right", "환", (
        ("1호선", "시청 -> 연산(123) -> 교대"),
        ("3호선", "물만골 -> 연산(305) -> 거제"),
    )),
    "교대": (58, 35, "1호선 · 동해선", "8개", True, "middle right", "환", (
        ("1호선", "연산 -> 교대(124) -> 동래"),
        ("동해선", "거제 -> 교대(K113) -> 동래"),
    )),
    "동래": (58, 40, "1호선 · 4호선", "4개", True, "top left", "환", (
        ("1호선", "교대 -> 동래(125) -> 명륜"),
        ("4호선", "미남 -> 동래(402) -> 수안"),
    )),
    "노포": (58, 58, "1호선", "3개", False, "middle left", "1", (
        ("1호선", "범어사 -> 노포(134) -> 종점"),
    )),
    "양산": (36, 58, "2호선", "4개", False, "middle right", "2", (
        ("2호선", "남양산 -> 양산(243) -> 종점"),
    )),
    "덕천": (36, 40, "2호선 · 3호선", "12개", True, "bottom right", "환", (
        ("2호선", "구명 -> 덕천(233) -> 수정"),
        ("3호선", "숙등 -> 덕천(313) -> 구포"),
    )),
    "사상": (36, 26, "2호선 · 부산김해경전철", "6개", True, "bottom left", "환", (
        ("2호선", "감전 -> 사상(227) -> 덕포"),
        ("부산김해경전철", "기점 -> 사상(1) -> 괘법르네시떼"),
    )),
    "수영": (83, 27, "2호선 · 3호선", "17개", True, "middle right", "환", (
        ("2호선", "광안 -> 수영(208) -> 민락"),
        ("3호선", "기점 -> 수영(301) -> 망미"),
    )),
    "벡스코": (94, 36, "2호선 · 동해선", "9개", True, "bottom right", "환", (
        ("2호선", "센텀시티 -> 벡스코(205) -> 동백"),
        ("동해선", "센텀 -> 벡스코(K119) -> 신해운대"),
    )),
    "장산": (108, 43, "2호선", "14개", False, "top center", "2", (
        ("2호선", "기점 -> 장산(201) -> 중동"),
    )),
    "대저": (24, 38, "3호선 · 부산김해경전철", "3개", True, "middle left", "환", (
        ("3호선", "체육공원 -> 대저(317) -> 종점"),
        ("부산김해경전철", "등구 -> 대저(7) -> 평강"),
    )),
    "미남": (51, 36, "3호선 · 4호선", "14개", True, "bottom left", "환", (
        ("3호선", "사직 -> 미남(309) -> 만덕"),
        ("4호선", "기점 -> 미남(401) -> 동래"),
    )),
    "거제": (54, 32, "3호선 · 동해선", "8개", True, "middle left", "환", (
        ("3호선", "연산 -> 거제(306) -> 종합운동장"),
        ("동해선", "거제해맞이 -> 거제(K112) -> 교대"),
    )),
    "안평": (83, 58, "4호선", "4개", False, "middle right", "4", (
        ("4호선", "고촌 -> 안평(414) -> 종점"),
    )),
    "가야대": (12, 58, "부산김해경전철", "2개", False, "middle right", "경", (
        ("부산김해경전철", "장신대 -> 가야대(21) -> 종점"),
    )),
    "부전": (55, 24, "동해선 (1호선 인근)", "2개", False, "middle left", "동", (
        ("동해선", "기점 -> 부전(K110) -> 거제해맞이"),
    )),
    "태화강": (114, 57, "동해선", "2개", False, "top center", "동", (
        ("동해선", "개운포 -> 태화강(K132) -> 종점"),
    )),
}

colors = current_palette.get("colors")
dashes = LINE_DASH.get(st.session_state.color_mode)
outline_color = current_palette.get("outline")

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
    x, y, line_info, exits, is_transfer, _, _, route_flows = STATIONS.get(station_name)

    badge = "🔄 환승역" if is_transfer else "🚩 기점 / 종점"
    st.markdown(f"<div style='font-size:1.35rem; font-weight:800; margin-bottom:0.5rem;'>{station_name}역 &nbsp; <span style='font-size:0.85rem; background:#F1F3F5; padding:3px 8px; border-radius:6px;'>{badge}</span></div>", unsafe_allow_html=True)

    img_path = None
    for ext in ("jpg", "png", "jpeg", "JPG", "PNG", "JPEG"):
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
    outline_dash = dashes.get(line_name) if st.session_state.color_mode == "전색맹용" else "solid"
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        showlegend=False,
        line=dict(color=outline_color, width=9.5, dash=outline_dash),
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        name=line_name,
        line=dict(color=colors.get(line_name), width=6.5, dash=dashes.get(line_name)),
        hoverinfo="skip"
    ))

st_names = tuple(STATIONS.keys())
st_xs = tuple(STATIONS.get(s).__getitem__(0) for s in st_names)
st_ys = tuple(STATIONS.get(s).__getitem__(1) for s in st_names)
st_sizes = tuple(18 if STATIONS.get(s).__getitem__(4) else 16 for s in st_names)
st_border_colors = tuple(get_station_border_color(STATIONS.get(s)) for s in st_names)
st_positions = tuple(STATIONS.get(s).__getitem__(5) for s in st_names)
st_badges = tuple(STATIONS.get(s).__getitem__(6) for s in st_names)

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

fig.add_trace(go.Scatter(
    x=st_xs, y=st_ys,
    mode="text",
    showlegend=False,
    text=st_badges,
    textposition="middle center",
    textfont=dict(size=9, color="#111111", family="Malgun Gothic, AppleGothic, sans-serif"),
    hoverinfo="skip"
))

fig.update_layout(
    plot_bgcolor=current_palette.get("bg"),
    paper_bgcolor=current_palette.get("bg"),
    xaxis=dict(visible=False, range=(2, 124), fixedrange=False),
    yaxis=dict(visible=False, range=(2, 64), fixedrange=False),
    height=550,
    margin=dict(l=5, r=5, t=5, b=5),
    hovermode="closest",
    hoverdistance=15,
    clickmode="event+select",
    legend=dict(
        orientation="h",
        yanchor="bottom", y=0.01,
        xanchor="left", x=0.01,
        itemwidth=55,
        font=dict(size=12, family="Malgun Gothic, AppleGothic, sans-serif"),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#DDDDDD",
        borderwidth=1
    ),
    dragmode="pan"
)

plotly_config = {
    "scrollZoom": True,
    "displaylogo": False,
    "locale": "ko",
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]
}

selection = st.plotly_chart(
    fig,
    use_container_width=True,
    config=plotly_config,
    on_select="rerun",
    selection_mode="points",
    key=f"map_{st.session_state.color_mode}"
)

if selection and selection.selection and selection.selection.points:
    pt = selection.selection.points.__getitem__(0)
    if pt.get("curve_number") == 12:
        idx = pt.get("point_index")
        chosen_station = st_names.__getitem__(idx)
        click_token = f"{chosen_station}_{st.session_state.color_mode}_{pt}"
        if st.session_state.last_click_id != click_token:
            st.session_state.last_click_id = click_token
            show_station_popup(chosen_station)
