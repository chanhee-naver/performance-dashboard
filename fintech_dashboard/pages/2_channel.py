import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from data_loader import load_data, get_channel_monthly

df_all = load_data()

with st.sidebar:
    st.markdown("### 🔧 필터")
    kpi_option = st.selectbox(
        "비교 KPI",
        ["CPA_반복사용", "CPA_회원가입", "CPA_계좌개설", "CTR", "CPI", "CPM"],
    )

st.title("📡 채널별 성과 분석")
st.caption("구글 / 페이스북 / 네이버검색 채널 간 KPI 비교")
st.divider()

ch_m = get_channel_monthly(df_all)

# ── 채널별 월별 선택 KPI 추이 ─────────────────────────────────────────────────
with st.container(border=True):
    st.subheader(f"📈 채널별 월별 {kpi_option} 추이")
    fig = go.Figure()
    colors = {"구글": "#4285F4", "페이스북": "#1877F2", "네이버검색": "#03C75A"}
    for ch, color in colors.items():
        d = ch_m[ch_m["channel"] == ch].sort_values("year_month")
        fig.add_trace(go.Scatter(
            x=d["year_month"], y=d[kpi_option],
            name=ch, mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=8),
        ))
    fig.update_layout(
        height=350, legend=dict(orientation="h", y=-0.2),
        yaxis_title=kpi_option,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig)

st.divider()

# ── 채널별 연간 KPI 비교 바 차트 ─────────────────────────────────────────────
ch_total = df_all.groupby("channel").agg(
    광고비=("광고비", "sum"), 광고노출=("광고노출", "sum"),
    광고클릭=("광고클릭", "sum"), 앱설치=("앱설치", "sum"),
    회원가입=("회원가입", "sum"), 반복사용=("반복사용", "sum"),
).reset_index()
ch_total["CTR"]         = ch_total["광고클릭"] / ch_total["광고노출"] * 100
ch_total["CPI"]         = ch_total["광고비"] / ch_total["앱설치"]
ch_total["CPM"]         = ch_total["광고비"] / ch_total["광고노출"] * 1000
ch_total["CPA_회원가입"] = ch_total["광고비"] / ch_total["회원가입"]
ch_total["CPA_반복사용"] = ch_total["광고비"] / ch_total["반복사용"]
ch_total["CPA_계좌개설"] = ch_total["광고비"] / ch_total.get("계좌개설", ch_total["회원가입"])

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("**채널별 CPA 비교 (반복사용당)**")
        fig2 = go.Figure(go.Bar(
            x=ch_total["channel"],
            y=ch_total["CPA_반복사용"],
            marker_color=[colors.get(c, "#888") for c in ch_total["channel"]],
            text=[f"₩{v:,.0f}" for v in ch_total["CPA_반복사용"]],
            textposition="outside",
        ))
        fig2.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0),
                           yaxis_title="CPA_반복사용 (원)",
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2)

with col2:
    with st.container(border=True):
        st.markdown("**채널별 광고비 vs 반복사용 파이 비교**")
        fig3 = go.Figure()
        fig3.add_trace(go.Pie(
            labels=ch_total["channel"], values=ch_total["광고비"],
            name="광고비", hole=0.4, domain={"x": [0, 0.48]},
            marker_colors=list(colors.values()),
            title="광고비 비중",
        ))
        fig3.add_trace(go.Pie(
            labels=ch_total["channel"], values=ch_total["반복사용"],
            name="반복사용", hole=0.4, domain={"x": [0.52, 1]},
            marker_colors=list(colors.values()),
            title="반복사용 비중",
        ))
        fig3.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0),
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3)

st.divider()

# ── 채널별 월별 광고비 스택 바 ───────────────────────────────────────────────
with st.container(border=True):
    st.subheader("💰 채널별 월별 광고비 분포")
    pivot_cost = ch_m.pivot(index="year_month", columns="channel", values="광고비").fillna(0)
    fig4 = go.Figure()
    for ch, color in colors.items():
        if ch in pivot_cost.columns:
            fig4.add_trace(go.Bar(
                x=pivot_cost.index, y=pivot_cost[ch] / 1e8,
                name=ch, marker_color=color,
            ))
    fig4.update_layout(
        barmode="stack", height=320,
        yaxis_title="광고비(억원)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig4)

# ── 채널별 상세 테이블 ────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 채널별 연간 KPI 상세")

disp = ch_total[["channel", "광고비", "광고노출", "광고클릭", "앱설치",
                  "회원가입", "반복사용", "CTR", "CPI", "CPM", "CPA_회원가입", "CPA_반복사용"]].copy()
disp.columns = ["채널", "광고비(억)", "노출(억)", "클릭", "앱설치",
                "회원가입", "반복사용", "CTR(%)", "CPI(원)", "CPM(원)", "CPA_가입(원)", "CPA_반복(원)"]
for c in ["광고비(억)", "노출(억)"]:
    disp[c] = (disp[c] / 1e8).round(1)
for c in ["CPI(원)", "CPM(원)", "CPA_가입(원)", "CPA_반복(원)"]:
    disp[c] = disp[c].round(0).astype(int)
disp["CTR(%)"] = disp["CTR(%)"].round(3)

st.dataframe(
    disp.style.background_gradient(subset=["CPA_반복(원)"], cmap="RdYlGn_r"),
    hide_index=True,
)

# 효율 인사이트 박스
st.divider()
col_ins1, col_ins2 = st.columns(2)

best_ch = ch_total.loc[ch_total["CPA_반복사용"].idxmin(), "channel"]
worst_ch = ch_total.loc[ch_total["CPA_반복사용"].idxmax(), "channel"]
best_val = ch_total["CPA_반복사용"].min()
worst_val = ch_total["CPA_반복사용"].max()

with col_ins1:
    st.success(f"✅ **최고 효율 채널**: {best_ch} — CPA_반복사용 ₩{best_val:,.0f}")
with col_ins2:
    st.error(f"⚠️ **최저 효율 채널**: {worst_ch} — CPA_반복사용 ₩{worst_val:,.0f} ({worst_val/best_val:.1f}배 비효율)")
