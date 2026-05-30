import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.utils.loader import load_braze_campaigns, load_braze_users, load_braze_purchases
from app.utils.formatter import fmt_num, fmt_pct, fmt_krw
from app.utils.style import inject_css
from app.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="Braze CRM", page_icon="📱", layout="wide")
inject_css()
st.title("📱 Braze CRM 분석")

_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=36, b=10),
)

with st.sidebar:
    st.markdown("## 🔍 필터")
    campaigns_df = load_braze_campaigns()
    if campaigns_df.empty:
        st.error("Braze 캠페인 데이터 없음")
        st.stop()

    months = sorted(campaigns_df["sent_at"].dt.strftime("%Y-%m").unique().tolist())
    sel_month = st.selectbox("월", ["전체"] + months)

    segments = sorted(campaigns_df["target_segment"].unique().tolist())
    sel_seg = st.multiselect("세그먼트", options=segments, default=segments)

df = campaigns_df.copy()
if sel_month != "전체":
    df = df[df["sent_at"].dt.strftime("%Y-%m") == sel_month]
if sel_seg:
    df = df[df["target_segment"].isin(sel_seg)]

if df.empty:
    st.warning("데이터 없음")
    st.stop()

# ── 전체 KPI ──────────────────────────────────────────────────────────────────
total_sent      = len(df)
total_delivered = df["delivered"].sum()
total_opened    = df["opened"].sum()
total_clicked   = df["clicked"].sum()
total_converted = df["converted"].sum()
total_rev       = df["conversion_value"].sum()

deliver_rate = total_delivered / total_sent      * 100 if total_sent      else 0
open_rate    = total_opened    / total_delivered * 100 if total_delivered else 0
click_rate   = total_clicked   / total_delivered * 100 if total_delivered else 0
cvr          = total_converted / total_delivered * 100 if total_delivered else 0

render_kpi_row([
    {"label": "총 발송수",  "value": fmt_num(total_sent)},
    {"label": "도달률",     "value": fmt_pct(deliver_rate)},
    {"label": "오픈율",     "value": fmt_pct(open_rate)},
    {"label": "클릭율",     "value": fmt_pct(click_rate)},
    {"label": "전환율(CVR)","value": fmt_pct(cvr)},
    {"label": "전환 매출",  "value": fmt_krw(total_rev)},
])
st.divider()

tab1, tab2, tab3 = st.tabs(["캠페인 성과", "세그먼트 분석", "유저 세그먼트"])

# ── 탭1: 캠페인 성과 ──────────────────────────────────────────────────────────
with tab1:
    canvas_agg = (
        df.groupby(["canvas_name", "target_segment"], as_index=False)
        .agg(
            발송=("delivered", "count"),
            도달=("delivered", "sum"),
            오픈=("opened", "sum"),
            클릭=("clicked", "sum"),
            전환=("converted", "sum"),
            전환매출=("conversion_value", "sum"),
        )
    )
    canvas_agg["오픈율"] = (canvas_agg["오픈"] / canvas_agg["도달"].replace(0, None) * 100).round(1)
    canvas_agg["클릭율"] = (canvas_agg["클릭"] / canvas_agg["도달"].replace(0, None) * 100).round(1)
    canvas_agg["CVR"]    = (canvas_agg["전환"] / canvas_agg["도달"].replace(0, None) * 100).round(1)
    canvas_agg = canvas_agg.sort_values("전환매출", ascending=False)

    st.dataframe(canvas_agg, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            canvas_agg.head(10), x="canvas_name", y="오픈율",
            color="target_segment", title="캠페인별 오픈율 Top 10",
            labels={"canvas_name": "", "오픈율": "오픈율 (%)"},
        )
        fig.update_layout(**_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            canvas_agg.head(10), x="canvas_name", y="CVR",
            color="target_segment", title="캠페인별 전환율(CVR) Top 10",
            labels={"canvas_name": "", "CVR": "CVR (%)"},
        )
        fig.update_layout(**_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

# ── 탭2: 세그먼트 분석 ────────────────────────────────────────────────────────
with tab2:
    seg_agg = (
        df.groupby("target_segment", as_index=False)
        .agg(
            발송=("delivered", "count"),
            도달=("delivered", "sum"),
            오픈=("opened", "sum"),
            전환=("converted", "sum"),
            전환매출=("conversion_value", "sum"),
        )
    )
    seg_agg["오픈율"] = (seg_agg["오픈"] / seg_agg["도달"].replace(0, None) * 100).round(1)
    seg_agg["CVR"]    = (seg_agg["전환"] / seg_agg["도달"].replace(0, None) * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            seg_agg.sort_values("CVR", ascending=False),
            x="target_segment", y="CVR",
            title="세그먼트별 전환율",
            color="CVR", color_continuous_scale="blues",
            labels={"target_segment": "세그먼트", "CVR": "CVR (%)"},
        )
        fig.update_layout(**_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            seg_agg.sort_values("전환매출", ascending=False),
            x="target_segment", y="전환매출",
            title="세그먼트별 전환 매출",
            color="전환매출", color_continuous_scale="greens",
            labels={"target_segment": "세그먼트", "전환매출": "전환매출 (원)"},
        )
        fig.update_layout(**_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    # 메시지 톤 분석
    if "_tone_truth" in df.columns:
        st.subheader("메시지 톤 × 전환율")
        tone_agg = (
            df.groupby("_tone_truth", as_index=False)
            .agg(도달=("delivered", "sum"), 전환=("converted", "sum"))
        )
        tone_agg["CVR"] = (tone_agg["전환"] / tone_agg["도달"].replace(0, None) * 100).round(1)
        fig = px.bar(
            tone_agg.sort_values("CVR", ascending=False),
            x="_tone_truth", y="CVR",
            title="메시지 톤별 CVR",
            labels={"_tone_truth": "톤", "CVR": "CVR (%)"},
        )
        fig.update_layout(**_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

# ── 탭3: 유저 세그먼트 ────────────────────────────────────────────────────────
with tab3:
    users = load_braze_users()
    if users.empty:
        st.info("유저 스냅샷 데이터 없음")
    else:
        if "_segment_truth" in users.columns:
            seg_cnt = users["_segment_truth"].value_counts().reset_index()
            seg_cnt.columns = ["세그먼트", "유저수"]
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(seg_cnt, names="세그먼트", values="유저수",
                             title="유저 세그먼트 분포", hole=0.4)
                fig.update_layout(**_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("세그먼트별 구매 현황")
                purch_seg = (
                    users.groupby("_segment_truth", as_index=False)
                    .agg(
                        유저수=("external_id", "count"),
                        평균구매수=("purchase_count_90d", "mean"),
                        평균매출=("purchase_amount_90d", "mean"),
                    )
                )
                purch_seg["평균구매수"] = purch_seg["평균구매수"].round(1)
                purch_seg["평균매출"]   = purch_seg["평균매출"].round(0).apply(fmt_krw)
                st.dataframe(purch_seg, use_container_width=True, hide_index=True)
