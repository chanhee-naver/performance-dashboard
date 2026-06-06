import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from data_loader import load_data, get_creative_monthly, get_adgroup_monthly

df_all = load_data()
cr_m = get_creative_monthly(df_all)
ag_m = get_adgroup_monthly(df_all)

st.title("🎨 소재 & 타겟팅 분석")
st.caption("소재 형식(영상/이미지/키워드) × 타겟팅(논타겟/리타겟) 성과 비교")
st.divider()

# ── 소재 형식별 연간 성과 ─────────────────────────────────────────────────────
cr_total = df_all.groupby("creative_format").agg(
    광고비=("광고비", "sum"), 광고노출=("광고노출", "sum"),
    광고클릭=("광고클릭", "sum"), 앱설치=("앱설치", "sum"),
    회원가입=("회원가입", "sum"), 반복사용=("반복사용", "sum"),
).reset_index()
cr_total["CTR"]         = cr_total["광고클릭"] / cr_total["광고노출"] * 100
cr_total["CPI"]         = cr_total["광고비"] / cr_total["앱설치"]
cr_total["CPA_회원가입"] = cr_total["광고비"] / cr_total["회원가입"]
cr_total["CPA_반복사용"] = cr_total["광고비"] / cr_total["반복사용"]
cr_total["예산비중"]     = cr_total["광고비"] / cr_total["광고비"].sum() * 100

# ── 타겟팅별 연간 성과 ────────────────────────────────────────────────────────
ag_total = df_all.groupby("ad_group").agg(
    광고비=("광고비", "sum"), 광고노출=("광고노출", "sum"),
    광고클릭=("광고클릭", "sum"), 앱설치=("앱설치", "sum"),
    회원가입=("회원가입", "sum"), 반복사용=("반복사용", "sum"),
).reset_index()
ag_total["CTR"]         = ag_total["광고클릭"] / ag_total["광고노출"] * 100
ag_total["CPA_회원가입"] = ag_total["광고비"] / ag_total["회원가입"]
ag_total["CPA_반복사용"] = ag_total["광고비"] / ag_total["반복사용"]

# ── KPI 요약 카드 ─────────────────────────────────────────────────────────────
cr_format_order = cr_total.sort_values("CPA_반복사용")
best_fmt = cr_format_order.iloc[0]
worst_fmt = cr_format_order.iloc[-1]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("최고 효율 소재", best_fmt["creative_format"],
              f"CPA ₩{best_fmt['CPA_반복사용']:,.0f}", border=True)
with col2:
    st.metric("최저 효율 소재", worst_fmt["creative_format"],
              f"CPA ₩{worst_fmt['CPA_반복사용']:,.0f}", border=True)
with col3:
    retarget = ag_total[ag_total["ad_group"]=="리타겟"].iloc[0]
    nontarget = ag_total[ag_total["ad_group"]=="논타겟"].iloc[0]
    st.metric("리타겟 CPA 우위", "리타겟",
              f"₩{retarget['CPA_반복사용']:,.0f} (-{(1-retarget['CPA_반복사용']/nontarget['CPA_반복사용'])*100:.0f}%)", border=True)
with col4:
    st.metric("논타겟 CPA", "논타겟",
              f"₩{nontarget['CPA_반복사용']:,.0f}", border=True)

st.divider()

# ── 소재 형식별 CPA 비교 ──────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
fmt_colors = {"영상": "#4F9CF9", "이미지": "#F5A623", "브랜드키워드": "#FF6B6B", "일반키워드": "#B47FFF"}

with col_a:
    with st.container(border=True):
        st.markdown("**소재 형식별 CPA_반복사용 (원)**")
        cr_sorted = cr_total.sort_values("CPA_반복사용")
        fig = go.Figure(go.Bar(
            y=cr_sorted["creative_format"],
            x=cr_sorted["CPA_반복사용"],
            orientation="h",
            marker_color=[fmt_colors.get(f, "#888") for f in cr_sorted["creative_format"]],
            text=[f"₩{v:,.0f}" for v in cr_sorted["CPA_반복사용"]],
            textposition="outside",
        ))
        fig.update_layout(height=280, margin=dict(l=0, r=60, t=10, b=0),
                          xaxis_title="CPA_반복사용 (원)",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

with col_b:
    with st.container(border=True):
        st.markdown("**소재 형식별 광고비 비중 & 반복사용 비중**")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="광고비 비중(%)", x=cr_total["creative_format"],
            y=cr_total["예산비중"],
            marker_color=[fmt_colors.get(f, "#888") for f in cr_total["creative_format"]],
            opacity=0.9,
        ))
        fig2.add_trace(go.Bar(
            name="반복사용 비중(%)", x=cr_total["creative_format"],
            y=cr_total["반복사용"] / cr_total["반복사용"].sum() * 100,
            marker_color=[fmt_colors.get(f, "#888") for f in cr_total["creative_format"]],
            opacity=0.5,
        ))
        fig2.update_layout(barmode="group", height=280,
                           margin=dict(l=0, r=0, t=10, b=0), yaxis_title="비중(%)",
                           legend=dict(orientation="h", y=-0.3),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2)

st.divider()

# ── 논타겟 vs 리타겟 월별 CPA 추이 ───────────────────────────────────────────
with st.container(border=True):
    st.subheader("📈 타겟팅별 월별 CPA_반복사용 추이")
    fig3 = go.Figure()
    target_colors = {"논타겟": "#F5A623", "리타겟": "#4F9CF9"}
    for ag, color in target_colors.items():
        d = ag_m[ag_m["ad_group"] == ag].sort_values("year_month")
        fig3.add_trace(go.Scatter(
            x=d["year_month"], y=d["CPA_반복사용"],
            name=ag, mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=8),
            fill="tozeroy",
            fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.1)"
                       if color.startswith("#") else "rgba(100,100,200,0.1)",
        ))
    fig3.update_layout(
        height=320, yaxis_title="CPA_반복사용 (원)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3)

st.divider()

# ── 소재 × 채널 CPA 매트릭스 ─────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🔢 채널 × 소재 형식 CPA_반복사용 매트릭스 (원)")
    ch_cr = df_all.groupby(["channel", "creative_format"]).agg(
        광고비=("광고비", "sum"), 반복사용=("반복사용", "sum")
    ).reset_index()
    ch_cr["CPA_반복사용"] = ch_cr["광고비"] / ch_cr["반복사용"].replace(0, np.nan)
    pivot = ch_cr.pivot(index="channel", columns="creative_format", values="CPA_반복사용").fillna(0)

    fig4 = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="RdYlGn_r",
        text=np.round(pivot.values, 0).astype(int).astype(str),
        texttemplate="₩%{text}",
        textfont={"size": 13},
        showscale=True,
    ))
    fig4.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="소재 형식",
        yaxis_title="채널",
    )
    st.plotly_chart(fig4)

# ── 인사이트 ──────────────────────────────────────────────────────────────────
st.divider()
st.info(
    "💡 **소재 인사이트**\n\n"
    f"- **영상 소재**가 CPA ₩{cr_total[cr_total['creative_format']=='영상']['CPA_반복사용'].values[0]:,.0f}로 가장 효율적\n"
    f"- **일반키워드**는 ₩{cr_total[cr_total['creative_format']=='일반키워드']['CPA_반복사용'].values[0]:,.0f}로 3.4배 비효율\n"
    f"- **리타겟**이 논타겟 대비 CPA {(1-retarget['CPA_반복사용']/nontarget['CPA_반복사용'])*100:.0f}% 낮음\n"
    "- 네이버 브랜드/일반 키워드 → SEO 강화로 오가닉 대체 검토 필요"
)
