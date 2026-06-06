import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from data_loader import load_data, get_monthly

df_all = load_data()

# ── 사이드바 필터 ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 필터")
    channels = st.multiselect(
        "채널", df_all["channel"].unique().tolist(),
        default=df_all["channel"].unique().tolist()
    )
    months = st.multiselect(
        "월 선택", sorted(df_all["year_month"].unique()),
        default=sorted(df_all["year_month"].unique())
    )

df = df_all[df_all["channel"].isin(channels) & df_all["year_month"].isin(months)]
monthly = get_monthly(df)

# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.title("📊 토스뱅크 광고 성과 대시보드")
st.caption(f"분석 기간: 2025년 1월 ~ 12월 | 총 {len(df):,}행 | 채널 {df['channel'].nunique()}개")

st.divider()

# ── KPI 카드 ──────────────────────────────────────────────────────────────────
total_cost     = df["광고비"].sum()
total_imp      = df["광고노출"].sum()
total_click    = df["광고클릭"].sum()
total_install  = df["앱설치"].sum()
total_signup   = df["회원가입"].sum()
total_account  = df["계좌개설"].sum()
total_repeat   = df["반복사용"].sum()

cpa_repeat  = total_cost / total_repeat if total_repeat else 0
cpa_signup  = total_cost / total_signup if total_signup else 0
ctr         = total_click / total_imp * 100 if total_imp else 0
cpi         = total_cost / total_install if total_install else 0

# MoM for last month
last_m = monthly.iloc[-1]
prev_m = monthly.iloc[-2] if len(monthly) >= 2 else last_m

def delta_pct(cur, prev):
    if prev and prev != 0:
        return f"{(cur/prev - 1)*100:+.1f}%"
    return None

col1, col2, col3, col4, col5, col6 = st.columns(6)
monthly_costs = monthly["광고비"].tolist()
monthly_repeat = monthly["반복사용"].tolist()

with col1:
    st.metric("💰 연간 광고비", f"{total_cost/1e8:.1f}억원",
              delta=delta_pct(last_m["광고비"], prev_m["광고비"]),
              border=True)
with col2:
    st.metric("👁️ 총 노출수", f"{total_imp/1e8:.1f}억회",
              border=True)
with col3:
    st.metric("🖱️ CTR", f"{ctr:.2f}%",
              border=True)
with col4:
    st.metric("📱 CPI (앱설치당)", f"₩{cpi:,.0f}",
              delta=delta_pct(last_m["CPI"], prev_m["CPI"]),
              border=True)
with col5:
    st.metric("👤 CPA 회원가입", f"₩{cpa_signup:,.0f}",
              delta=delta_pct(last_m["CPA_회원가입"], prev_m["CPA_회원가입"]),
              border=True)
with col6:
    st.metric("🔁 CPA 반복사용", f"₩{cpa_repeat:,.0f}",
              delta=delta_pct(last_m["CPA_반복사용"], prev_m["CPA_반복사용"]),
              border=True)

st.divider()

# ── 월별 광고비 & 반복사용 추이 ───────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    with st.container(border=True):
        st.subheader("📈 월별 광고비 & 반복사용수 추이")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly["year_month"], y=monthly["광고비"] / 1e8,
            name="광고비(억원)", marker_color="#4F9CF9",
            yaxis="y1", opacity=0.8,
        ))
        fig.add_trace(go.Scatter(
            x=monthly["year_month"], y=monthly["반복사용"],
            name="반복사용수", mode="lines+markers",
            line=dict(color="#FF6B6B", width=3),
            marker=dict(size=8),
            yaxis="y2",
        ))
        fig.update_layout(
            yaxis=dict(title="광고비(억원)", side="left"),
            yaxis2=dict(title="반복사용수", side="right", overlaying="y"),
            legend=dict(x=0.01, y=0.99),
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig)

with col_right:
    with st.container(border=True):
        st.subheader("💸 월별 CPA 트렌드 (반복사용당)")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=monthly["year_month"], y=monthly["CPA_반복사용"],
            mode="lines+markers+text",
            text=[f"₩{v:,.0f}" for v in monthly["CPA_반복사용"]],
            textposition="top center",
            textfont=dict(size=10),
            line=dict(color="#F5A623", width=3),
            marker=dict(size=8, color=[
                "#FF4444" if v > 6000 else "#44BB44" for v in monthly["CPA_반복사용"]
            ]),
            fill="tozeroy",
            fillcolor="rgba(245,166,35,0.1)",
        ))
        fig2.add_hline(y=monthly["CPA_반복사용"].mean(),
                       line_dash="dash", line_color="gray",
                       annotation_text=f"평균 {monthly['CPA_반복사용'].mean():,.0f}원",
                       annotation_position="right")
        fig2.update_layout(
            height=320,
            yaxis=dict(title="CPA_반복사용 (원)"),
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2)

# ── 채널별 연간 성과 요약 ─────────────────────────────────────────────────────
st.divider()
st.subheader("📡 채널별 연간 성과 요약")

ch_summary = df.groupby("channel").agg(
    광고비=("광고비", "sum"),
    광고노출=("광고노출", "sum"),
    광고클릭=("광고클릭", "sum"),
    앱설치=("앱설치", "sum"),
    회원가입=("회원가입", "sum"),
    반복사용=("반복사용", "sum"),
).reset_index()
ch_summary["CTR"]         = ch_summary["광고클릭"] / ch_summary["광고노출"] * 100
ch_summary["CPI"]         = ch_summary["광고비"] / ch_summary["앱설치"]
ch_summary["CPA_회원가입"] = ch_summary["광고비"] / ch_summary["회원가입"]
ch_summary["CPA_반복사용"] = ch_summary["광고비"] / ch_summary["반복사용"]
ch_summary["예산비중"]     = ch_summary["광고비"] / ch_summary["광고비"].sum() * 100
ch_summary["반복사용비중"] = ch_summary["반복사용"] / ch_summary["반복사용"].sum() * 100

col_a, col_b = st.columns([3, 2])

with col_a:
    with st.container(border=True):
        st.markdown("**채널별 광고비 vs 반복사용 비중 비교**")
        fig3 = go.Figure()
        channels_list = ch_summary["channel"].tolist()
        colors = ["#4F9CF9", "#FF6B6B", "#44BB44"]
        for i, row in ch_summary.iterrows():
            fig3.add_trace(go.Bar(
                name=row["channel"],
                x=["광고비 비중(%)", "반복사용 비중(%)"],
                y=[row["예산비중"], row["반복사용비중"]],
                marker_color=colors[i % len(colors)],
            ))
        fig3.update_layout(
            barmode="group", height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.2),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3)

with col_b:
    with st.container(border=True):
        st.markdown("**채널별 KPI 테이블**")
        disp = ch_summary[["channel", "광고비", "CTR", "CPI", "CPA_회원가입", "CPA_반복사용", "예산비중"]].copy()
        disp.columns = ["채널", "광고비(억)", "CTR(%)", "CPI(원)", "CPA_가입(원)", "CPA_반복(원)", "예산비중(%)"]
        disp["광고비(억)"] = (disp["광고비(억)"] / 1e8).round(1)
        disp["CTR(%)"] = disp["CTR(%)"].round(2)
        disp["CPI(원)"] = disp["CPI(원)"].round(0).astype(int)
        disp["CPA_가입(원)"] = disp["CPA_가입(원)"].round(0).astype(int)
        disp["CPA_반복(원)"] = disp["CPA_반복(원)"].round(0).astype(int)
        disp["예산비중(%)"] = disp["예산비중(%)"].round(1)
        st.dataframe(disp, hide_index=True, height=280)

# ── 연간 퍼널 요약 ────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔽 연간 전체 퍼널 요약")

funnel_data = {
    "단계": ["광고클릭", "앱설치", "앱실행", "회원가입", "계좌개설", "첫거래", "반복사용"],
    "수량": [
        df["광고클릭"].sum(), df["앱설치"].sum(), df["앱실행"].sum(),
        df["회원가입"].sum(), df["계좌개설"].sum(), df["첫거래"].sum(), df["반복사용"].sum()
    ]
}
funnel_df = pd.DataFrame(funnel_data)
funnel_df["전환율(%)"] = (funnel_df["수량"] / funnel_df["수량"].iloc[0] * 100).round(1)

col_funnel, col_table = st.columns([3, 2])
with col_funnel:
    with st.container(border=True):
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_df["단계"],
            x=funnel_df["수량"],
            textinfo="value+percent initial",
            marker=dict(color=["#4F9CF9", "#5BA8FF", "#6CB3FF", "#7DBEFF",
                                "#8EC9FF", "#9FD4FF", "#B0DFFF"]),
        ))
        fig_funnel.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_funnel)

with col_table:
    with st.container(border=True):
        st.markdown("**단계별 수량 & 누적 전환율**")
        disp2 = funnel_df.copy()
        disp2["수량"] = disp2["수량"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(disp2, hide_index=True, height=280)
