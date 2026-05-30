import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

from app.utils.loader import load_joined, filter_date
from app.utils.formatter import fmt_krw, fmt_roas, fmt_pct, fmt_num
from app.utils.sidebar import render_sidebar
from app.utils.style import inject_css
from app.components.charts import scatter_creative, bar_by_channel

st.set_page_config(page_title="소재 효율", page_icon="🎨", layout="wide")
inject_css()
st.title("🎨 소재 효율 분석")

start, end, channels = render_sidebar()
df = load_joined()
df = filter_date(df, start, end)
if channels:
    df = df[df["channel"].isin(channels)]

if df.empty:
    st.warning("데이터 없음")
    st.stop()

# ── 소재 타입 필터 ─────────────────────────────────────────────────────────────
creative_types = sorted(df["creative_type"].dropna().unique().tolist())
type_labels = {
    "VID": "🎬 동영상", "IMG": "🖼️ 이미지", "CRS": "🎠 카루셀",
    "TXT": "📝 텍스트", "BRD": "🔍 브랜드검색",
}
sel_types = st.multiselect(
    "소재 유형",
    options=creative_types,
    default=creative_types,
    format_func=lambda x: type_labels.get(x, x),
)
if sel_types:
    df = df[df["creative_type"].isin(sel_types)]

# ── 산점도 ─────────────────────────────────────────────────────────────────────
st.plotly_chart(scatter_creative(df), use_container_width=True)

# ── 소재 집계 ──────────────────────────────────────────────────────────────────
grp = (
    df.groupby(["creative", "channel", "creative_type"], as_index=False)
    .agg(
        광고비=("ch_cost", "sum"),
        노출=("ch_impressions", "sum"),
        클릭=("ch_clicks", "sum"),
        AF회원가입=("af_signups", "sum"),
        AF구매=("af_purchases", "sum"),
        AF매출=("af_revenue", "sum"),
    )
)
grp["ROAS_AF"] = (grp["AF매출"] / grp["광고비"].replace(0, None)).round(2)
grp["CTR"]     = (grp["클릭"] / grp["노출"].replace(0, None) * 100).round(2)
grp["CPA"]     = (grp["광고비"] / grp["AF구매"].replace(0, None)).round(0)
grp = grp.dropna(subset=["ROAS_AF"]).sort_values("ROAS_AF", ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 ROAS Top 10")
    top = grp.head(10).copy()
    for c, fn in [("광고비", fmt_krw), ("AF매출", fmt_krw), ("CPA", fmt_krw),
                  ("노출", fmt_num), ("AF구매", fmt_num),
                  ("ROAS_AF", fmt_roas), ("CTR", fmt_pct)]:
        top[c] = top[c].apply(fn)
    st.dataframe(
        top[["creative", "channel", "creative_type", "광고비", "ROAS_AF", "CTR", "AF구매", "CPA"]],
        use_container_width=True, hide_index=True,
    )

with col2:
    st.subheader("📉 ROAS Bottom 10")
    bottom = grp.tail(10).copy()
    for c, fn in [("광고비", fmt_krw), ("AF매출", fmt_krw), ("CPA", fmt_krw),
                  ("노출", fmt_num), ("AF구매", fmt_num),
                  ("ROAS_AF", fmt_roas), ("CTR", fmt_pct)]:
        bottom[c] = bottom[c].apply(fn)
    st.dataframe(
        bottom[["creative", "channel", "creative_type", "광고비", "ROAS_AF", "CTR", "AF구매", "CPA"]],
        use_container_width=True, hide_index=True,
    )

# ── 소재 유형별 비교 ─────────────────────────────────────────────────────────
st.subheader("소재 유형별 평균 ROAS(AF)")
type_agg = (
    df.groupby("creative_type", as_index=False)
    .agg(ch_cost=("ch_cost", "sum"), af_revenue=("af_revenue", "sum"))
)
type_agg["roas_af"] = type_agg["af_revenue"] / type_agg["ch_cost"].replace(0, None)
type_agg["소재유형"] = type_agg["creative_type"].map(lambda x: type_labels.get(x, x))

import plotly.express as px
fig = px.bar(
    type_agg.sort_values("roas_af", ascending=False),
    x="소재유형", y="roas_af",
    labels={"roas_af": "ROAS(AF)", "소재유형": ""},
    template="plotly_dark", color="roas_af",
    color_continuous_scale="blues",
)
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
