import os
import math
import base64
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
        .ud-legend-box {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 16px;
            background: rgba(255, 255, 255, 0.96);
            border: 1.5px solid #D1D5DB;
            border-radius: 10px;
            padding: 8px 16px;
            margin-top: 4px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }
        .ud-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.88rem;
            font-weight: 700;
            color: #111827;
        }
    </style>
""", unsafe_allow_html=True)

PALETTES = {
    "기본": {
        "colors": {
            "1호선": "#F06A00", "2호선": "#68A832", "3호선": "#B8860B",
            "4호선": "#0054A6", "경전철": "#7E52A0", "동해선": "#38BDF8"
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
            "1호선": "#F59E0B", "2호선": "#005AB5", "3호선": "#7DD3FC",
            "4호선": "#1E1B4B", "경전철": "#C026D3", "동해선": "#0284C7"
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
            "1호선": "#B80D48", "2호선": "#007A87", "3호선": "#E85D8F",
            "4호선": "#111111", "경전철": "#5C0931", "동해선": "#38B6C7"
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
            "1호선": "#111111", "2호선": "#333333", "3호선": "#525252",
            "4호선": "#707070", "경전철": "#222222", "동해선": "#454545"
        },
        "outline": "#000000",
        "badge_bg": "#F1F3F5",
        "badge_text": "#212529",
        "badge_border": "#CED4DA",
        "bg": "#FFFFFF",
        "text": "#111111"
    }
}

LINE_SHAPES = {
    "1호선": "circle",
    "2호선": "square",
    "3호선": "triangle-down",
    "4호선": "triangle-up",
    "경전철": "pentagon",
    "동해선": "diamond"
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
    "2호선": ((36, 58), (36, 24), (39, 21), (63, 21), (66, 18), (66, 11), (69, 9), (80, 9), (83, 11), (83, 32), (91, 32), (94, 35), (105, 35), (108, 38), (108, 43)),
    "3호선": ((24, 38), (27, 40), (48, 40), (51, 38), (51, 31), (54, 29), (80, 29), (83, 27)),
    "4호선": ((51, 36), (54, 40), (80, 40), (83, 42), (83, 58)),
    "경전철": ((12, 58), (12, 43), (15, 41), (24, 38), (24, 26), (27, 24), (34, 24), (36, 26)),
    "동해선": ((51, 24), (51, 32), (54, 35), (58, 35), (61, 37), (91, 37), (94, 35), (97, 38), (97, 55), (100, 57), (114, 57))
}

STATIONS = {
    "다대포해수욕장": (12, 18, "1호선", "4개", False, "top center", "1", ("1호선",), (
        ("1호선", "기점 -> 다대포해수욕장(095) -> 다대포항"),
    )),
    "서면": (58, 21, "1호선 · 2호선", "15개", True, "bottom right", "", ("1호선", "2호선"), (
        ("1호선", "범내골 -> 서면(119) -> 부전"),
        ("2호선", "전포 -> 서면(219) -> 부암"),
    )),
    "연산": (58, 29, "1호선 · 3호선", "17개", True, "bottom right", "", ("1호선", "3호선"), (
        ("1호선", "시청 -> 연산(123) -> 교대"),
        ("3호선", "물만골 -> 연산(305) -> 거제"),
    )),
    "교대": (58, 35, "1호선 · 동해선", "8개", True, "middle right", "", ("1호선", "동해선"), (
        ("1호선", "연산 -> 교대(124) -> 동래"),
        ("동해선", "거제 -> 교대(K113) -> 동래"),
    )),
    "동래": (58, 40, "1호선 · 4호선", "4개", True, "top left", "", ("1호선", "4호선"), (
        ("1호선", "교대 -> 동래(125) -> 명륜"),
        ("4호선", "미남 -> 동래(402) -> 수안"),
    )),
    "노포": (58, 58, "1호선", "3개", False, "middle left", "1", ("1호선",), (
        ("1호선", "범어사 -> 노포(134) -> 종점"),
    )),
    "양산": (36, 58, "2호선", "4개", False, "middle right", "2", ("2호선",), (
        ("2호선", "남양산 -> 양산(243) -> 종점"),
    )),
    "덕천": (36, 40, "2호선 · 3호선", "12개", True, "bottom right", "", ("2호선", "3호선"), (
        ("2호선", "구명 -> 덕천(233) -> 수정"),
        ("3호선", "숙등 -> 덕천(313) -> 구포"),
    )),
    "사상": (36, 26, "2호선 · 부산김해경전철", "6개", True, "bottom left", "", ("2호선", "경전철"), (
        ("2호선", "감전 -> 사상(227) -> 덕포"),
        ("부산김해경전철", "기점 -> 사상(1) -> 괘법르네시떼"),
    )),
    "수영": (83, 27, "2호선 · 3호선", "17개", True, "middle right", "", ("2호선", "3호선"), (
        ("2호선", "광안 -> 수영(208) -> 민락"),
        ("3호선", "기점 -> 수영(301) -> 망미"),
    )),
    "벡스코": (94, 35, "2호선 · 동해선", "9개", True, "bottom right", "", ("2호선", "동해선"), (
        ("2호선", "센텀시티 -> 벡스코(205) -> 동백"),
        ("동해선", "센텀 -> 벡스코(K119) -> 신해운대"),
    )),
    "장산": (108, 43, "2호선", "14개", False, "top center", "2", ("2호선",), (
        ("2호선", "기점 -> 장산(201) -> 중동"),
    )),
    "대저": (24, 38, "3호선 · 부산김해경전철", "3개", True, "top left", "", ("3호선", "경전철"), (
        ("3호선", "체육공원 -> 대저(317) -> 종점"),
        ("부산김해경전철", "등구 -> 대저(7) -> 평강"),
    )),
    "미남": (51, 36, "3호선 · 4호선", "14개", True, "middle left", "", ("3호선", "4호선"), (
        ("3호선", "만덕 -> 미남(309) -> 사직"),
        ("4호선", "기점 -> 미남(401) -> 동래"),
    )),
    "거제": (51, 31, "3호선 · 동해선", "8개", True, "middle left", "", ("3호선", "동해선"), (
        ("3호선", "종합운동장 -> 거제(306) -> 연산"),
        ("동해선", "거제해맞이 -> 거제(K112) -> 교대"),
    )),
    "안평": (83, 58, "4호선", "4개", False, "middle right", "4", ("4호선",), (
        ("4호선", "고촌 -> 안평(414) -> 종점"),
    )),
    "가야대": (12, 58, "부산김해경전철", "2개", False, "middle right", "경", ("경전철",), (
        ("부산김해경전철", "장신대 -> 가야대(21) -> 종점"),
    )),
    "부전": (51, 24, "동해선 (1호선 인근)", "2개", False, "middle left", "동", ("동해선",), (
        ("동해선", "기점 -> 부전(K110) -> 거제해맞이"),
    )),
    "태화강": (114, 57, "동해선", "2개", False, "top center", "동", ("동해선",), (
        ("동해선", "개운포 -> 태화강(K132) -> 종점"),
    )),
}

colors = current_palette.get("colors")
outline_color = current_palette.get("outline")

def sample_line_uniform(coords, step=1.15):
    px, py, angles = [], [], []
    accum = 0.0
    next_mark = step * 0.5
    for i in range(len(coords) - 1):
        x1, y1 = coords.__getitem__(i)
        x2, y2 = coords.__getitem__(i + 1)
        dx = x2 - x1
        dy = y2 - y1
        seg_len = math.hypot(dx, dy)
        if seg_len == 0:
            continue
        ang = math.degrees(math.atan2(dy, dx))
        while next_mark <= accum + seg_len:
            t = (next_mark - accum) / seg_len
            px.append(x1 + dx * t)
            py.append(y1 + dy * t)
            angles.append(ang)
            next_mark += step
        accum += seg_len
    return px, py, angles

def load_transfer_svg_base64():
    if not os.path.exists("images"):
        return None
    svg_files = tuple(f for f in os.listdir("images") if f.lower().endswith(".svg"))
    if not svg_files:
        return None
    target_path = os.path.join("images", svg_files.__getitem__(0))
    with open(target_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"

def get_station_border_color(station_tuple):
    first_line = station_tuple.__getitem__(7).__getitem__(0)
    return colors.get(first_line, "#111111")

def get_station_symbol(station_tuple):
    if station_tuple.__getitem__(4):
        return "circle"
    first_line = station_tuple.__getitem__(7).__getitem__(0)
    return LINE_SHAPES.get(first_line, "circle")

def build_legend_html():
    c1 = colors.get("1호선")
    c2 = colors.get("2호선")
    c3 = colors.get("3호선")
    c4 = colors.get("4호선")
    ck = colors.get("경전철")
    cd = colors.get("동해선")
    items = (
        ("1호선", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{c1}" stroke-width="7" stroke-linecap="round"/>
            <circle cx="27" cy="10" r="7" fill="#FFFFFF" stroke="{c1}" stroke-width="2.5"/>
            <text x="27" y="13.2" text-anchor="middle" font-size="9" font-weight="800" fill="#111">1</text>
        </svg>"""),
        ("2호선", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{c2}" stroke-width="7" stroke-linecap="round"/>
            <path d="M8 14 L13 6 M16 14 L21 6 M34 14 L39 6 M42 14 L47 6" stroke="#FFFFFF" stroke-width="2"/>
            <rect x="20" y="3" width="14" height="14" fill="#FFFFFF" stroke="{c2}" stroke-width="2.5"/>
            <text x="27" y="13.2" text-anchor="middle" font-size="9" font-weight="800" fill="#111">2</text>
        </svg>"""),
        ("3호선", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{c3}" stroke-width="7" stroke-linecap="round"/>
            <path d="M9 6 V14 M15 6 V14 M39 6 V14 M45 6 V14" stroke="#FFFFFF" stroke-width="2"/>
            <polygon points="19,4 35,4 27,17" fill="#FFFFFF" stroke="{c3}" stroke-width="2.3"/>
            <text x="27" y="11.5" text-anchor="middle" font-size="8" font-weight="800" fill="#111">3</text>
        </svg>"""),
        ("4호선", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{c4}" stroke-width="7" stroke-linecap="round"/>
            <path d="M13 14 L8 6 M21 14 L16 6 M39 14 L34 6 M47 14 L42 6" stroke="#FFFFFF" stroke-width="2"/>
            <polygon points="27,3 35,16 19,16" fill="#FFFFFF" stroke="{c4}" stroke-width="2.3"/>
            <text x="27" y="14.5" text-anchor="middle" font-size="8" font-weight="800" fill="#111">4</text>
        </svg>"""),
        ("부산김해경전철", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{ck}" stroke-width="7" stroke-linecap="round"/>
            <line x1="3" y1="10" x2="51" y2="10" stroke="#FFFFFF" stroke-width="2.2"/>
            <polygon points="27,2 35,8 32,17 22,17 19,8" fill="#FFFFFF" stroke="{ck}" stroke-width="2.3"/>
            <text x="27" y="13.2" text-anchor="middle" font-size="8" font-weight="800" fill="#111">경</text>
        </svg>"""),
        ("동해선", f"""<svg width="54" height="20" viewBox="0 0 54 20">
            <line x1="2" y1="10" x2="52" y2="10" stroke="{outline_color}" stroke-width="10" stroke-linecap="round"/>
            <line x1="2" y1="10" x2="52" y2="10" stroke="{cd}" stroke-width="7" stroke-linecap="round"/>
            <circle cx="9" cy="10" r="2" fill="#FFFFFF"/><circle cx="15" cy="10" r="2" fill="#FFFFFF"/>
            <circle cx="39" cy="10" r="2" fill="#FFFFFF"/><circle cx="45" cy="10" r="2" fill="#FFFFFF"/>
            <polygon points="27,2 35,10 27,18 19,10" fill="#FFFFFF" stroke="{cd}" stroke-width="2.3"/>
            <text x="27" y="13" text-anchor="middle" font-size="8" font-weight="800" fill="#111">동</text>
        </svg>"""),
    )
    html_parts = ['<div class="ud-legend-box">']
    for label, svg_code in items:
        html_parts.append(f'<div class="ud-legend-item">{svg_code}<span>{label}</span></div>')
    html_parts.append('</div>')
    return "".join(html_parts)

@st.dialog("🚉 역 상세 정보 안내", width="small")
def show_station_popup(station_name):
    x, y, line_info, exits, is_transfer, _, _, _, route_flows = STATIONS.get(station_name)

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
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        showlegend=False,
        line=dict(color=outline_color, width=10.5),
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="lines",
        showlegend=False,
        line=dict(color=colors.get(line_name), width=7.5),
        hoverinfo="skip"
    ))

p2_x, p2_y, p2_ang = sample_line_uniform(LINES_PATH.get("2호선"), step=1.15)
fig.add_trace(go.Scatter(
    x=p2_x, y=p2_y, mode="markers", showlegend=False, hoverinfo="skip",
    marker=dict(symbol="line-ns", size=6.8, angle=tuple(-a + 45 for a in p2_ang), line=dict(color="#FFFFFF", width=2.2))
))

p3_x, p3_y, p3_ang = sample_line_uniform(LINES_PATH.get("3호선"), step=1.1)
fig.add_trace(go.Scatter(
    x=p3_x, y=p3_y, mode="markers", showlegend=False, hoverinfo="skip",
    marker=dict(symbol="line-ns", size=6.2, angle=tuple(-a for a in p3_ang), line=dict(color="#FFFFFF", width=2.2))
))

p4_x, p4_y, p4_ang = sample_line_uniform(LINES_PATH.get("4호선"), step=1.15)
fig.add_trace(go.Scatter(
    x=p4_x, y=p4_y, mode="markers", showlegend=False, hoverinfo="skip",
    marker=dict(symbol="line-ns", size=6.8, angle=tuple(-a - 45 for a in p4_ang), line=dict(color="#FFFFFF", width=2.2))
))

kj_coords = LINES_PATH.get("경전철")
fig.add_trace(go.Scatter(
    x=tuple(x for x, y in kj_coords), y=tuple(y for x, y in kj_coords),
    mode="lines", showlegend=False, hoverinfo="skip",
    line=dict(color="#FFFFFF", width=2.2)
))

pd_x, pd_y, _ = sample_line_uniform(LINES_PATH.get("동해선"), step=1.25)
fig.add_trace(go.Scatter(
    x=pd_x, y=pd_y, mode="markers", showlegend=False, hoverinfo="skip",
    marker=dict(symbol="circle", size=4.2, color="#FFFFFF")
))

st_names = tuple(STATIONS.keys())
st_xs = tuple(STATIONS.get(s).__getitem__(0) for s in st_names)
st_ys = tuple(STATIONS.get(s).__getitem__(1) for s in st_names)
st_positions = tuple(STATIONS.get(s).__getitem__(5) for s in st_names)
single_badges = tuple(STATIONS.get(s).__getitem__(6) for s in st_names)
st_symbols = tuple(get_station_symbol(STATIONS.get(s)) for s in st_names)

fig.add_trace(go.Scatter(
    x=st_xs, y=st_ys,
    mode="markers+text",
    showlegend=False,
    text=st_names,
    textposition=st_positions,
    textfont=dict(size=12, color=current_palette.get("text"), family="Malgun Gothic, AppleGothic, sans-serif"),
    marker=dict(
        symbol=st_symbols,
        size=tuple(20 if STATIONS.get(s).__getitem__(4) else 18 for s in st_names),
        color=tuple("rgba(0,0,0,0)" if STATIONS.get(s).__getitem__(4) else "#FFFFFF" for s in st_names),
        line=dict(
            color=tuple("rgba(0,0,0,0)" if STATIONS.get(s).__getitem__(4) else get_station_border_color(STATIONS.get(s)) for s in st_names),
            width=3.2
        )
    ),
    hovertemplate="<b>%{text}역</b> (클릭하여 정보 열기)<extra></extra>"
))

fig.add_trace(go.Scatter(
    x=st_xs, y=st_ys,
    mode="text",
    showlegend=False,
    text=single_badges,
    textposition="middle center",
    textfont=dict(size=8.5, color="#111111", family="Malgun Gothic, AppleGothic, sans-serif"),
    hoverinfo="skip"
))

transfer_svg_uri = load_transfer_svg_base64()
transfer_images = []
if transfer_svg_uri:
    for s in st_names:
        st_data = STATIONS.get(s)
        if st_data.__getitem__(4):
            sx = st_data.__getitem__(0)
            sy = st_data.__getitem__(1)
            transfer_images.append(dict(
                source=transfer_svg_uri,
                xref="x", yref="y",
                x=sx, y=sy,
                sizex=2.1, sizey=2.1,
                xanchor="center", yanchor="middle",
                layer="above"
            ))

fig.update_layout(
    plot_bgcolor=current_palette.get("bg"),
    paper_bgcolor=current_palette.get("bg"),
    images=transfer_images,
    xaxis=dict(visible=False, range=(2, 124), fixedrange=False),
    yaxis=dict(visible=False, range=(2, 64), fixedrange=False, scaleanchor="x", scaleratio=0.52),
    height=510,
    margin=dict(l=5, r=5, t=5, b=5),
    hovermode="closest",
    hoverdistance=15,
    clickmode="event+select",
    showlegend=False,
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

st.markdown(build_legend_html(), unsafe_allow_html=True)

st.components.v1.html("""
<script>
(function() {
    const doc = window.parent.document;
    function lockIconSize() {
        const plots = doc.querySelectorAll('.js-plotly-plot');
        plots.forEach(gd => {
            if (!gd || !gd._fullLayout || !gd._fullLayout.images) return;
            const xa = gd._fullLayout.xaxis;
            const ya = gd._fullLayout.yaxis;
            if (!xa || !ya) return;
            const spanX = Math.abs(xa.range.at(1) - xa.range.at(0));
            const spanY = Math.abs(ya.range.at(1) - ya.range.at(0));
            if (spanX === 0 || spanY === 0) return;
            const pxPerX = xa._length / spanX;
            const pxPerY = ya._length / spanY;
            const targetPx = 20;
            const newSizeX = targetPx / pxPerX;
            const newSizeY = targetPx / pxPerY;
            const imgs = gd.layout.images;
            if (imgs && imgs.length > 0 && Math.abs(imgs.at(0).sizex - newSizeX) > 0.001) {
                const updated = imgs.map(im => Object.assign({}, im, {sizex: newSizeX, sizey: newSizeY}));
                window.parent.Plotly.relayout(gd, {images: updated});
            }
        });
    }
    setInterval(lockIconSize, 250);
})();
</script>
""", height=0)

if selection and selection.selection and selection.selection.points:
    pt = selection.selection.points.__getitem__(0)
    if pt.get("curve_number") == 17:
        idx = pt.get("point_index")
        chosen_station = st_names.__getitem__(idx)
        click_token = f"{chosen_station}_{st.session_state.color_mode}_{pt}"
        if st.session_state.last_click_id != click_token:
            st.session_state.last_click_id = click_token
            show_station_popup(chosen_station)
