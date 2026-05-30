import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import plotly.express as px

from app.utils.loader import load_joined, filter_date
from app.utils.formatter import fmt_krw, fmt_roas, fmt_pct, fmt_num
from app.utils.sidebar import render_sidebar
from app.utils.style import inject_css
from app.components.charts import bar_by_channel, bar_roas_by_channel, line_daily, line_daily_ratio, CHANNEL_COLORS

st.set_page_config(page_title="채널 성과", page_icon="📊", layout="wide")
inject_css()
st.title("📊 채널별 성과")

start, end, channels = render_sidebar()
df = load_joined()
df = filter_date(df, start, end)
if channels:
    df = df[df["channel"].isin(channels)]

if df.empty:
    st.warning("데이터 없음")
    st.stop()

tab1, tab2, tab3 = st.tabs(["채널 비교", "캠페인 드릴다운", "트렌드"])

# ── 탭1: 채널 비교 ─────────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_by_channel(df, "ch_cost", "채널별 광고비"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_roas_by_channel(df), use_container_width=True)

    summary = (
        df.groupby("channel", as_index=False)
        .agg(
            광고비=("ch_cost", "sum"),
            노출=("ch_impressions", "sum"),
            클릭=("ch_clicks", "sum"),
            AF회원가입=("af_signups", "sum"),
            AF구매=("af_purchases", "sum"),
            AF매출=("af_revenue", "sum"),
        )
    )
    summary["ROAS_AF"] = (summary["AF매출"] / summary["광고비"].replace(0, None)).round(2)
    summary["CTR"]     = (summary["클릭"] / summary["노출"].replace(0, None) * 100).round(2)
    summary["CPR"]     = (summary["광고비"] / summary["AF회원가입"].replace(0, None)).round(0)
    summary["CPA"]     = (summary["광고비"] / summary["AF구매"].replace(0, None)).round(0)

    disp = summary.copy()
    for col, fn in [
        ("광고비", fmt_krw), ("AF매출", fmt_krw), ("CPR", fmt_krw), ("CPA", fmt_krw),
        ("노출", fmt_num), ("클릭", fmt_num), ("AF회원가입", fmt_num), ("AF구매", fmt_num),
        ("ROAS_AF", fmt_roas), ("CTR", fmt_pct),
    ]:
        disp[col] = disp[col].apply(fn)

    st.subheader("채널별 KPI 요약")
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ── 탭2: 캠페인 드릴다운 ────────────────────────────────────────────────────────
with tab2:
    camp = (
        df.groupby(["channel", "campaign", "campaign_goal"], as_index=False)
        .agg(
            광고비=("ch_cost", "sum"),
            AF회원가입=("af_signups", "sum"),
            AF구매=("af_purchases", "sum"),
            AF매출=("af_revenue", "sum"),
        )
    )
    camp["ROAS_AF"] = (camp["AF매출"] / camp["광고비"].replace(0, None)).round(2)
    camp["CPR"]     = (camp["광고비"] / camp["AF회원가입"].replace(0, None)).round(0)
    camp["CPA"]     = (camp["광고비"] / camp["AF구매"].replace(0, None)).round(0)
    camp = camp.sort_values("광고비", ascending=False)

    channel_sel = st.selectbox("채널 선택", options=["전체"] + sorted(camp["channel"].unique().tolist()))
    if channel_sel != "전체":
        camp = camp[camp["channel"] == channel_sel]

    st.dataframe(camp, use_container_width=True, hide_index=True)

# ── 탭3: 트렌드 ─────────────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(line_daily(df, "ch_cost", "일별 광고비"), use_container_width=True)
    with col2:
        st.plotly_chart(line_daily_ratio(df, "af_revenue", "ch_cost", "ROAS(AF) 트렌드"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(line_daily(df, "af_signups", "AF 회원가입 트렌드"), use_container_width=True)
    with col4:
        st.plotly_chart(line_daily(df, "af_purchases", "AF 구매 트렌드"), use_container_width=True)
