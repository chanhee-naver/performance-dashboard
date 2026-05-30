import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

from app.utils.loader   import load_joined, filter_date
from app.utils.formatter import fmt_krw, fmt_roas, fmt_pct, fmt_num
from app.utils.sidebar  import render_sidebar
from app.utils.style    import inject_css, insight_card
from app.utils.insights import generate_insights
from app.components.kpi_cards import render_kpi_row
from app.components.charts    import (
    bar_by_channel, bar_roas_by_channel,
    line_daily_ratio, gap_heatmap, gap_trend,
)

st.set_page_config(
    page_title="퍼포먼스 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.title("📊 퍼포먼스 대시보드")

start, end, channels = render_sidebar()

df_all = load_joined()
df = filter_date(df_all, start, end)
if channels:
    df = df[df["channel"].isin(channels)]

st.markdown(
    f'<span class="date-badge">📅 {start.strftime("%Y.%m.%d")} – {end.strftime("%Y.%m.%d")}'
    f'&emsp;|&emsp;{len(df):,}행&emsp;|&emsp;채널 {len(df["channel"].unique())}개</span>',
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("선택한 기간·채널에 데이터가 없습니다.")
    st.stop()

# ── KPI 계산 ──────────────────────────────────────────────────────────────────
total_cost      = df["ch_cost"].sum()
total_af_rev    = df["af_revenue"].sum()
total_af_signup = df["af_signups"].sum()
total_af_purch  = df["af_purchases"].sum()
total_impr      = df["ch_impressions"].sum()
total_clicks    = df["ch_clicks"].sum()

roas_af = total_af_rev    / total_cost      if total_cost      else 0
cpr     = total_cost      / total_af_signup if total_af_signup else 0
cpa     = total_cost      / total_af_purch  if total_af_purch  else 0
ctr     = total_clicks    / total_impr * 100 if total_impr     else 0

render_kpi_row([
    {"label": "총 광고비",        "value": fmt_krw(total_cost)},
    {"label": "ROAS (AF)",        "value": fmt_roas(roas_af)},
    {"label": "CPR (회원가입당)", "value": fmt_krw(cpr)},
    {"label": "CPA (구매당)",     "value": fmt_krw(cpa)},
    {"label": "CTR",              "value": fmt_pct(ctr)},
    {"label": "AF 구매수",        "value": fmt_num(total_af_purch)},
])

st.divider()

# ── 탭 ────────────────────────────────────────────────────────────────────────
tab_insight, tab_channel, tab_gap = st.tabs([
    "🔎 인사이트", "📊 채널 요약", "🔍 갭 현황",
])

# ── 탭1: 자동 인사이트 ────────────────────────────────────────────────────────
with tab_insight:
    insights = generate_insights(df)
    if insights:
        html = "".join(insight_card(i["icon"], i["text"], i["level"]) for i in insights)
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("분석 기간이 짧거나 이상 패턴이 감지되지 않았습니다.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 채널 × 목적별 ROAS 히트맵
    st.subheader("캠페인 목적별 ROAS (AF)")
    pivot = (
        df.groupby(["channel", "campaign_goal"], as_index=False)
        .agg(cost=("ch_cost", "sum"), rev=("af_revenue", "sum"))
    )
    pivot["roas"] = (pivot["rev"] / pivot["cost"].replace(0, None)).round(2)
    pivot_tbl = pivot.pivot(index="campaign_goal", columns="channel", values="roas").fillna(0)
    st.dataframe(pivot_tbl, use_container_width=True)

# ── 탭2: 채널 요약 ───────────────────────────────────────────────────────────
with tab_channel:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_by_channel(df, "ch_cost", "채널별 광고비"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_roas_by_channel(df), use_container_width=True)

    st.plotly_chart(
        line_daily_ratio(df, "af_revenue", "ch_cost", "ROAS(AF) 일별 트렌드"),
        use_container_width=True,
    )

    summary = (
        df.groupby("channel", as_index=False)
        .agg(
            광고비=("ch_cost", "sum"),
            AF회원가입=("af_signups", "sum"),
            AF구매=("af_purchases", "sum"),
            AF매출=("af_revenue", "sum"),
        )
    )
    summary["ROAS_AF"] = (summary["AF매출"] / summary["광고비"].replace(0, None)).round(2)
    summary["CPR"]     = (summary["광고비"] / summary["AF회원가입"].replace(0, None)).round(0)

    disp = summary.copy()
    for col, fn in [("광고비", fmt_krw), ("AF매출", fmt_krw), ("CPR", fmt_krw),
                    ("AF회원가입", fmt_num), ("AF구매", fmt_num), ("ROAS_AF", fmt_roas)]:
        disp[col] = disp[col].apply(fn)
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ── 탭3: 갭 현황 ─────────────────────────────────────────────────────────────
with tab_gap:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(gap_heatmap(df), use_container_width=True)
    with col2:
        st.plotly_chart(gap_trend(df), use_container_width=True)

    ch_gap = (
        df.groupby("channel", as_index=False)
        .agg(ch_rev=("ch_revenue", "sum"), af_rev=("af_revenue", "sum"))
    )
    ch_gap["gap"] = ch_gap["af_rev"] / ch_gap["ch_rev"].replace(0, None) * 100

    for _, row in ch_gap.iterrows():
        g = row["gap"]
        if pd.isna(g):
            continue
        if g < 60:
            st.error(f"⚠️ {row['channel']} 매출 갭 {g:.0f}% — 어트리뷰션 링크 점검 필요")
        elif g < 80:
            st.warning(f"🟡 {row['channel']} 매출 갭 {g:.0f}% — 캠페인 설정 확인 권장")
        else:
            st.success(f"✅ {row['channel']} 매출 갭 {g:.0f}% — 정상")
