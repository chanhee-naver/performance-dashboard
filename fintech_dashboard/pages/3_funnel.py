import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from data_loader import load_data, get_monthly, get_channel_monthly

df_all = load_data()
monthly = get_monthly(df_all)
ch_m = get_channel_monthly(df_all)

st.title("🔽 퍼널 전환율 분석")
st.caption("광고클릭 → 앱설치 → 앱실행 → 회원가입 → 계좌개설 → 첫거래 → 반복사용")
st.divider()

# ── 전환율 정의 ───────────────────────────────────────────────────────────────
funnel_steps = [
    ("클릭→설치", "클릭_설치율", "#4F9CF9"),
    ("설치→실행", "설치_실행율", "#5BA8FF"),
    ("실행→가입", "실행_가입율", "#F5A623"),
    ("가입→계좌", "가입_계좌율", "#FF6B6B"),
    ("계좌→첫거래", "계좌_첫거래율", "#B47FFF"),
    ("첫거래→반복", "첫거래_반복율", "#44BB44"),
]

# ── 연간 평균 전환율 KPI ──────────────────────────────────────────────────────
st.subheader("📊 연간 평균 전환율 (전체 기간)")

total = df_all.agg({
    "광고클릭": "sum", "앱설치": "sum", "앱실행": "sum",
    "회원가입": "sum", "계좌개설": "sum", "첫거래": "sum", "반복사용": "sum"
})

rates = {
    "클릭→설치": total["앱설치"] / total["광고클릭"] * 100,
    "설치→실행": total["앱실행"] / total["앱설치"] * 100,
    "실행→가입": total["회원가입"] / total["앱실행"] * 100,
    "가입→계좌": total["계좌개설"] / total["회원가입"] * 100,
    "계좌→첫거래": total["첫거래"] / total["계좌개설"] * 100,
    "첫거래→반복": total["반복사용"] / total["첫거래"] * 100,
}
colors_map = dict(zip(rates.keys(), ["#4F9CF9","#5BA8FF","#F5A623","#FF6B6B","#B47FFF","#44BB44"]))

cols = st.columns(len(rates))
for i, (label, rate) in enumerate(rates.items()):
    with cols[i]:
        st.metric(label, f"{rate:.2f}%", border=True)

st.divider()

# ── 월별 전환율 추이 ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("📈 월별 전환율 추이")
    selected_steps = st.multiselect(
        "표시할 전환율 선택",
        [s[0] for s in funnel_steps],
        default=["클릭→설치", "실행→가입", "계좌→첫거래", "첫거래→반복"],
        key="funnel_select",
    )

    col_key_map = dict(zip([s[0] for s in funnel_steps], [s[1] for s in funnel_steps]))
    color_key_map = dict(zip([s[0] for s in funnel_steps], [s[2] for s in funnel_steps]))

    fig = go.Figure()
    for step in selected_steps:
        col = col_key_map[step]
        if col in monthly.columns:
            fig.add_trace(go.Scatter(
                x=monthly["year_month"], y=monthly[col],
                name=step, mode="lines+markers",
                line=dict(color=color_key_map[step], width=2),
                marker=dict(size=6),
            ))
    fig.update_layout(
        height=360, legend=dict(orientation="h", y=-0.2),
        yaxis_title="전환율(%)",
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig)

st.divider()

# ── 월별 전환율 히트맵 ────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🗓️ 월별 전환율 히트맵")
    rate_cols = [s[1] for s in funnel_steps]
    rate_labels = [s[0] for s in funnel_steps]

    heatmap_df = monthly[["year_month"] + rate_cols].set_index("year_month")
    heatmap_df.columns = rate_labels

    fig_hm = go.Figure(go.Heatmap(
        z=heatmap_df.T.values,
        x=heatmap_df.index.tolist(),
        y=rate_labels,
        colorscale="Blues",
        text=np.round(heatmap_df.T.values, 1).astype(str),
        texttemplate="%{text}%",
        textfont={"size": 11},
        showscale=True,
    ))
    fig_hm.update_layout(
        height=320, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hm)

st.divider()

# ── 채널별 퍼널 비교 ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("📡 채널별 퍼널 전환율 비교 (연간)")
    ch_total = df_all.groupby("channel").agg(
        광고클릭=("광고클릭", "sum"), 앱설치=("앱설치", "sum"),
        앱실행=("앱실행", "sum"), 회원가입=("회원가입", "sum"),
        계좌개설=("계좌개설", "sum"), 첫거래=("첫거래", "sum"),
        반복사용=("반복사용", "sum"),
    ).reset_index()
    ch_total["클릭→설치"] = ch_total["앱설치"] / ch_total["광고클릭"] * 100
    ch_total["실행→가입"] = ch_total["회원가입"] / ch_total["앱실행"] * 100
    ch_total["계좌→첫거래"] = ch_total["첫거래"] / ch_total["계좌개설"] * 100
    ch_total["첫거래→반복"] = ch_total["반복사용"] / ch_total["첫거래"] * 100

    display_rates = ["클릭→설치", "실행→가입", "계좌→첫거래", "첫거래→반복"]
    ch_colors = {"구글": "#4285F4", "페이스북": "#1877F2", "네이버검색": "#03C75A"}

    fig_ch = go.Figure()
    for _, row in ch_total.iterrows():
        ch = row["channel"]
        fig_ch.add_trace(go.Bar(
            name=ch, x=display_rates,
            y=[row[r] for r in display_rates],
            marker_color=ch_colors.get(ch, "#888"),
        ))
    fig_ch.update_layout(
        barmode="group", height=320, yaxis_title="전환율(%)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_ch)

# ── 병목 인사이트 ──────────────────────────────────────────────────────────────
st.divider()
min_step = min(rates, key=rates.get)
st.warning(
    f"⚠️ **퍼널 최대 병목**: `{min_step}` — 전환율 **{rates[min_step]:.1f}%**\n\n"
    "계좌 개설 후 첫 거래로 이어지지 않는 비율이 가장 높습니다. "
    "온보딩 경험, 리텐션 푸시, 첫 거래 인센티브 강화를 검토하세요."
)
