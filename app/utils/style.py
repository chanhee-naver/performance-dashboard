import streamlit as st

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

/* ── 전체 폰트 ──────────────────────────────────────────────────── */
html, body, [class*="css"], .stMarkdown, button, input, select, textarea {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── 배경 ─────────────────────────────────────────────────────── */
.stApp { background-color: #0d1117; }

/* ── KPI 메트릭 카드 ──────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 20px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
[data-testid="stMetric"]:hover {
    border-color: #03C75A;
    box-shadow: 0 4px 14px rgba(3,199,90,0.08);
}
[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
    color: #8b949e !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-size: clamp(1rem, 1.8vw, 1.4rem) !important;
    font-weight: 700 !important;
    color: #e6edf3 !important;
    letter-spacing: -0.01em;
    white-space: nowrap !important;
    overflow: visible !important;
}
[data-testid="stMetric"] div[data-testid="stMetricValue"] > div {
    overflow: visible !important;
    text-overflow: unset !important;
    white-space: nowrap !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── 탭 ─────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
    gap: 2px;
    background: transparent !important;
    border-bottom: 1px solid #21262d !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #e6edf3 !important;
    border-bottom: 2px solid #4C9BE8 !important;
}

/* ── 사이드바 ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebarContent"] { background-color: #0d1117 !important; }

/* ── 구분선 ─────────────────────────────────────────────────── */
hr { border-color: #21262d !important; }

/* ── 데이터프레임 ────────────────────────────────────────────── */
[data-testid="stDataFrame"] > div {
    border-radius: 10px !important;
    border: 1px solid #30363d !important;
    overflow: hidden;
}

/* ── 텍스트 인풋 ────────────────────────────────────────────── */
[data-testid="stTextInput"] input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.875rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #4C9BE8 !important;
    box-shadow: 0 0 0 3px rgba(76,155,232,0.12) !important;
}

/* ── 다운로드 버튼 ──────────────────────────────────────────── */
.stDownloadButton > button {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
}
.stDownloadButton > button:hover {
    border-color: #4C9BE8 !important;
    background: #1c2128 !important;
}

/* ── selectbox / multiselect ────────────────────────────────── */
[data-baseweb="select"] > div {
    background: #161b22 !important;
    border-color: #30363d !important;
    border-radius: 8px !important;
}

/* ── 페이지 타이틀 아래 캡션 ────────────────────────────────── */
.date-badge {
    display: inline-block;
    background: #1c2128;
    border: 1px solid #30363d;
    border-radius: 100px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #8b949e;
    margin-bottom: 16px;
    font-family: 'Pretendard', sans-serif;
}
</style>
"""

def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def insight_card(icon: str, text: str, level: str = "info") -> str:
    colors = {
        "success": "#3fb950",
        "warning": "#d29922",
        "error":   "#f85149",
        "info":    "#4C9BE8",
    }
    c = colors.get(level, "#4C9BE8")
    return (
        f'<div style="background:#161b22;border:1px solid #30363d;border-left:3px solid {c};'
        f'border-radius:10px;padding:12px 16px;margin-bottom:8px;'
        f'font-size:0.875rem;color:#e6edf3;line-height:1.6;">'
        f'{icon}&nbsp;&nbsp;{text}</div>'
    )
