import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

from app.utils.loader import load_joined, filter_date
from app.utils.formatter import fmt_pct, gap_badge
from app.utils.sidebar import render_sidebar
from app.utils.style import inject_css
from app.components.kpi_cards import render_kpi_row
from app.components.charts import gap_heatmap, gap_trend

st.set_page_config(page_title="어트리뷰션 갭", page_icon="🔍", layout="wide")
inject_css()
st.title("🔍 어트리뷰션 갭 분석")
st.caption("AF 집계 / 플랫폼 집계 × 100  |  80% 이상 정상 · 60~79% 주의 · 60% 미만 경고")

start, end, channels = render_sidebar()
df = load_joined()
df = filter_date(df, start, end)
if channels:
    df = df[df["channel"].isin(channels)]

if df.empty:
    st.warning("데이터 없음")
    st.stop()

# ── 전체 갭 요약 카드 ──────────────────────────────────────────────────────────
total_ch_signup   = df["ch_signups"].sum()
total_af_signup   = df["af_signups"].sum()
total_ch_purch    = df["ch_purchases"].sum()
total_af_purch    = df["af_purchases"].sum()
total_ch_rev      = df["ch_revenue"].sum()
total_af_rev      = df["af_revenue"].sum()

signup_gap   = total_af_signup / total_ch_signup   * 100 if total_ch_signup   else 0
purchase_gap = total_af_purch  / total_ch_purch    * 100 if total_ch_purch    else 0
revenue_gap  = total_af_rev    / total_ch_rev      * 100 if total_ch_rev      else 0

render_kpi_row([
    {"label": "회원가입 갭",  "value": fmt_pct(signup_gap)},
    {"label": "구매 갭",      "value": fmt_pct(purchase_gap)},
    {"label": "매출 갭",      "value": fmt_pct(revenue_gap)},
])
st.divider()

# ── 히트맵 + 트렌드 ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(gap_heatmap(df), use_container_width=True)
with col2:
    st.plotly_chart(gap_trend(df), use_container_width=True)

# ── 이상 캠페인 알럿 ──────────────────────────────────────────────────────────
st.subheader("⚠️ 이상 캠페인 (매출 갭 < 60%)")
camp_gap = (
    df.groupby(["channel", "campaign"], as_index=False)
    .agg(ch_rev=("ch_revenue", "sum"), af_rev=("af_revenue", "sum"))
)
camp_gap["매출갭"] = camp_gap["af_rev"] / camp_gap["ch_rev"].replace(0, None) * 100
anomalies = camp_gap[camp_gap["매출갭"] < 60].sort_values("매출갭")

if anomalies.empty:
    st.success("이상 캠페인 없음")
else:
    for _, row in anomalies.iterrows():
        st.error(f"🔴 [{row['channel']}] {row['campaign']} — 매출 갭 {row['매출갭']:.0f}%")

# ── 전체 채널×캠페인 갭 테이블 ────────────────────────────────────────────────
st.subheader("채널 × 캠페인 갭 상세")
tbl = (
    df.groupby(["channel", "campaign"], as_index=False)
    .agg(
        ch_signups=("ch_signups", "sum"),
        af_signups=("af_signups", "sum"),
        ch_purchases=("ch_purchases", "sum"),
        af_purchases=("af_purchases", "sum"),
        ch_revenue=("ch_revenue", "sum"),
        af_revenue=("af_revenue", "sum"),
    )
)
tbl["회원가입갭"] = (tbl["af_signups"]   / tbl["ch_signups"].replace(0, None)   * 100).round(1)
tbl["구매갭"]    = (tbl["af_purchases"] / tbl["ch_purchases"].replace(0, None) * 100).round(1)
tbl["매출갭"]    = (tbl["af_revenue"]   / tbl["ch_revenue"].replace(0, None)   * 100).round(1)

tbl["회원가입갭_뱃지"] = tbl["회원가입갭"].apply(gap_badge)
tbl["구매갭_뱃지"]    = tbl["구매갭"].apply(gap_badge)
tbl["매출갭_뱃지"]    = tbl["매출갭"].apply(gap_badge)

display = tbl[["channel", "campaign", "회원가입갭_뱃지", "구매갭_뱃지", "매출갭_뱃지"]].rename(columns={
    "channel": "채널", "campaign": "캠페인",
    "회원가입갭_뱃지": "회원가입 갭", "구매갭_뱃지": "구매 갭", "매출갭_뱃지": "매출 갭",
})
st.dataframe(display, use_container_width=True, hide_index=True)
