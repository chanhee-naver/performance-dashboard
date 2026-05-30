import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

from app.utils.loader   import load_joined, filter_date
from app.utils.formatter import fmt_krw, fmt_num
from app.utils.sidebar  import render_sidebar
from app.utils.style    import inject_css

st.set_page_config(page_title="Raw 데이터", page_icon="📋", layout="wide")
inject_css()

st.title("📋 Raw 데이터")

start, end, channels = render_sidebar()
df_all = load_joined()
df = filter_date(df_all, start, end)
if channels:
    df = df[df["channel"].isin(channels)]

if df.empty:
    st.warning("데이터 없음")
    st.stop()

# ── 요약 KPI ──────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("총 행수", fmt_num(len(df)))
c2.metric("총 광고비", fmt_krw(df["ch_cost"].sum()))
c3.metric("유니크 캠페인", fmt_num(df["campaign"].nunique()))

st.divider()

# ── 필터 ─────────────────────────────────────────────────────────────────────
col_search, col_ch, col_goal = st.columns([3, 1.5, 1.5])

with col_search:
    query = st.text_input("🔍 검색 (캠페인·그룹·소재 전체 검색)", placeholder="검색어 입력...")

with col_ch:
    ch_opts = ["전체"] + sorted(df["channel"].unique().tolist())
    ch_sel  = st.selectbox("채널", ch_opts, label_visibility="collapsed")

with col_goal:
    goal_opts = ["전체"] + sorted(df["campaign_goal"].dropna().unique().tolist())
    goal_sel  = st.selectbox("캠페인 목적", goal_opts, label_visibility="collapsed")

# ── 필터 적용 ─────────────────────────────────────────────────────────────────
view = df.copy()

if query:
    mask = (
        view["campaign"].str.contains(query, case=False, na=False) |
        view["adgroup"].str.contains(query, case=False, na=False)  |
        view["creative"].str.contains(query, case=False, na=False)
    )
    view = view[mask]

if ch_sel != "전체":
    view = view[view["channel"] == ch_sel]

if goal_sel != "전체":
    view = view[view["campaign_goal"] == goal_sel]

# ── 표시 컬럼 선택 ────────────────────────────────────────────────────────────
_ALL_COLS = list(view.columns)
_DEFAULT_COLS = [
    "date", "channel", "campaign", "campaign_goal", "adgroup", "creative",
    "ch_cost", "ch_impressions", "ch_clicks", "ch_signups", "ch_purchases",
    "af_signups", "af_purchases", "af_revenue",
    "roas_af", "ctr", "signup_gap_pct", "revenue_gap_pct",
]
_DEFAULT_COLS = [c for c in _DEFAULT_COLS if c in _ALL_COLS]

with st.expander("표시 컬럼 선택", expanded=False):
    selected_cols = st.multiselect(
        "컬럼",
        options=_ALL_COLS,
        default=_DEFAULT_COLS,
        label_visibility="collapsed",
    )

if not selected_cols:
    selected_cols = _DEFAULT_COLS

st.caption(f"{len(view):,}행 표시 중 / 전체 {len(df):,}행")

# ── 테이블 ───────────────────────────────────────────────────────────────────
st.dataframe(
    view[selected_cols].reset_index(drop=True),
    use_container_width=True,
    height=500,
)

# ── CSV 다운로드 ──────────────────────────────────────────────────────────────
csv_bytes = view[selected_cols].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
file_name = f"perf_data_{start}_{end}.csv"

st.download_button(
    label="⬇️ CSV 다운로드 (엑셀 호환)",
    data=csv_bytes,
    file_name=file_name,
    mime="text/csv",
    use_container_width=False,
)
