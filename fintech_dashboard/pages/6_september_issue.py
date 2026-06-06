import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_data, get_monthly, get_channel_monthly, get_creative_monthly, get_adgroup_monthly

df_all = load_data()
monthly = get_monthly(df_all)
ch_m = get_channel_monthly(df_all)
cr_m = get_creative_monthly(df_all)
ag_m = get_adgroup_monthly(df_all)

AUG = "2025-08"
SEP = "2025-09"

st.title("🔍 9월 이슈 드릴다운")
st.caption("8월 대비 9월 반복사용수·단가 급변 원인 심층 분석")
st.divider()

# ── 핵심 변화 요약 ────────────────────────────────────────────────────────────
aug = monthly[monthly["year_month"] == AUG].iloc[0]
sep = monthly[monthly["year_month"] == SEP].iloc[0]

st.subheader("⚡ 8월 → 9월 핵심 지표 변화")

def delta_card(label, aug_val, sep_val, fmt="num"):
    chg = (sep_val / aug_val - 1) * 100 if aug_val else 0
    if fmt == "krw":
        aug_str = f"₩{aug_val:,.0f}"
        sep_str = f"₩{sep_val:,.0f}"
    elif fmt == "pct":
        aug_str = f"{aug_val:.2f}%"
        sep_str = f"{sep_val:.2f}%"
    elif fmt == "M":
        aug_str = f"{aug_val/1e6:.1f}M"
        sep_str = f"{sep_val/1e6:.1f}M"
    elif fmt == "억":
        aug_str = f"{aug_val/1e8:.1f}억"
        sep_str = f"{sep_val/1e8:.1f}억"
    else:
        aug_str = f"{aug_val:,.0f}"
        sep_str = f"{sep_val:,.0f}"
    return label, aug_str, sep_str, chg

metrics = [
    delta_card("광고비", aug["광고비"], sep["광고비"], "억"),
    delta_card("광고노출", aug["광고노출"], sep["광고노출"], "M"),
    delta_card("CPM", aug["CPM"], sep["CPM"], "krw"),
    delta_card("CPC", aug["CPC"], sep["CPC"], "krw"),
    delta_card("반복사용수", aug["반복사용"], sep["반복사용"], "num"),
    delta_card("CPA_반복사용", aug["CPA_반복사용"], sep["CPA_반복사용"], "krw"),
]

cols = st.columns(6)
for i, (label, aug_val, sep_val, chg) in enumerate(metrics):
    with cols[i]:
        with st.container(border=True):
            st.metric(
                label,
                sep_val,
                delta=f"{chg:+.1f}% MoM",
                help=f"8월: {aug_val}",
            )

st.divider()

# ── 8월 vs 9월 분해 테이블 ────────────────────────────────────────────────────
st.subheader("📋 8월 vs 9월 전환율 비교 (PDF 핵심 분석)")

compare_metrics = [
    ("광고노출", "광고노출", 1e6, "M"),
    ("CTR(%)", "CTR", 1, "%"),
    ("클릭→설치(%)", "클릭_설치율", 1, "%"),
    ("설치→실행(%)", "설치_실행율", 1, "%"),
    ("실행→가입(%)", "실행_가입율", 1, "%"),
    ("가입→계좌(%)", "가입_계좌율", 1, "%"),
    ("계좌→첫거래(%)", "계좌_첫거래율", 1, "%"),
    ("첫거래→반복(%)", "첫거래_반복율", 1, "%"),
    ("반복사용수", "반복사용", 1, "num"),
]

table_rows = []
for label, col, scale, fmt in compare_metrics:
    a_val = aug[col] / scale
    s_val = sep[col] / scale
    mom = (s_val / a_val - 1) * 100 if a_val else 0
    if fmt == "M":
        a_str = f"{a_val:.1f}M"
        s_str = f"{s_val:.1f}M"
    elif fmt == "%":
        a_str = f"{a_val:.2f}%"
        s_str = f"{s_val:.2f}%"
    else:
        a_str = f"{a_val:,.0f}"
        s_str = f"{s_val:,.0f}"
    dominant = "⭐ 핵심 드라이버" if abs(mom) > 10 else ""
    table_rows.append({"지표": label, "8월": a_str, "9월": s_str,
                       "MoM": f"{mom:+.1f}%", "판단": dominant})

tbl_df = pd.DataFrame(table_rows)
st.dataframe(
    tbl_df.style.applymap(
        lambda v: "background-color: #ffe0e0" if "+" in str(v) and float(str(v).replace("+","").replace("%","")) > 10 else
                  "background-color: #e0ffe0" if "-" in str(v) else "",
        subset=["MoM"]
    ),
    hide_index=True,
)

st.info("📌 **결론**: 다른 전환율은 ±0.2% 이내로 안정적. **광고노출 +31.8%**가 반복사용 +31.7% 증가의 핵심 드라이버.")

st.divider()

# ── 채널별 9월 변화 분석 ──────────────────────────────────────────────────────
st.subheader("📡 채널별 9월 변화 분석")

aug_ch = ch_m[ch_m["year_month"] == AUG].copy()
sep_ch = ch_m[ch_m["year_month"] == SEP].copy()
merged = aug_ch.merge(sep_ch, on="channel", suffixes=("_aug", "_sep"))
merged["노출_MoM"] = (merged["광고노출_sep"] / merged["광고노출_aug"] - 1) * 100
merged["반복_Delta"] = merged["반복사용_sep"] - merged["반복사용_aug"]
merged["CPA_aug"] = merged["광고비_aug"] / merged["반복사용_aug"]
merged["CPA_sep"] = merged["광고비_sep"] / merged["반복사용_sep"]
merged["CPA_MoM"] = (merged["CPA_sep"] / merged["CPA_aug"] - 1) * 100

col_ch1, col_ch2 = st.columns(2)
ch_colors = {"구글": "#4285F4", "페이스북": "#1877F2", "네이버검색": "#03C75A"}

with col_ch1:
    with st.container(border=True):
        st.markdown("**채널별 광고노출 MoM (%)**")
        fig = go.Figure(go.Bar(
            x=merged["channel"], y=merged["노출_MoM"],
            marker_color=[ch_colors.get(c, "#888") for c in merged["channel"]],
            text=[f"{v:+.1f}%" for v in merged["노출_MoM"]],
            textposition="outside",
        ))
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=30, b=0),
                          yaxis_title="MoM 변화율(%)",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

with col_ch2:
    with st.container(border=True):
        st.markdown("**채널별 반복사용당 CPA (8월 vs 9월)**")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="8월", x=merged["channel"], y=merged["CPA_aug"],
            marker_color="rgba(100,150,255,0.7)",
        ))
        fig2.add_trace(go.Bar(
            name="9월", x=merged["channel"], y=merged["CPA_sep"],
            marker_color=[ch_colors.get(c, "#888") for c in merged["channel"]],
        ))
        fig2.update_layout(barmode="group", height=280,
                           margin=dict(l=0, r=0, t=30, b=0), yaxis_title="CPA (원)",
                           legend=dict(orientation="h", y=-0.3),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2)

st.divider()

# ── 소재별 9월 변화 ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🎨 소재 형식별 9월 노출 변화 (광고비 가중)")

    aug_cr = cr_m[cr_m["year_month"] == AUG].copy()
    sep_cr = cr_m[cr_m["year_month"] == SEP].copy()
    merged_cr = aug_cr.merge(sep_cr, on="creative_format", suffixes=("_aug", "_sep"))
    merged_cr["노출_Delta"] = merged_cr["광고노출_sep"] - merged_cr["광고노출_aug"]
    merged_cr["노출_MoM"]   = (merged_cr["광고노출_sep"] / merged_cr["광고노출_aug"] - 1) * 100
    merged_cr["CPA_aug"] = merged_cr["광고비_aug"] / merged_cr["반복사용_aug"]
    merged_cr["CPA_sep"] = merged_cr["광고비_sep"] / merged_cr["반복사용_sep"]

    fmt_colors = {"영상": "#4F9CF9", "이미지": "#F5A623", "브랜드키워드": "#FF6B6B", "일반키워드": "#B47FFF"}
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="CPA 8월(원)", x=merged_cr["creative_format"], y=merged_cr["CPA_aug"],
        marker_color="rgba(100,150,255,0.7)",
    ))
    fig3.add_trace(go.Bar(
        name="CPA 9월(원)", x=merged_cr["creative_format"], y=merged_cr["CPA_sep"],
        marker_color=[fmt_colors.get(f, "#888") for f in merged_cr["creative_format"]],
    ))
    fig3.update_layout(barmode="group", height=320,
                       yaxis_title="CPA_반복사용(원)",
                       legend=dict(orientation="h", y=-0.2),
                       margin=dict(l=0, r=0, t=10, b=0),
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3)

    st.caption(
        f"영상: MoM +{merged_cr[merged_cr['creative_format']=='영상']['노출_MoM'].values[0]:.1f}% | "
        f"이미지: MoM +{merged_cr[merged_cr['creative_format']=='이미지']['노출_MoM'].values[0]:.1f}%"
    )

# ── 결론 ──────────────────────────────────────────────────────────────────────
st.divider()
with st.container(border=True):
    st.subheader("📌 9월 이슈 결론 및 시사점")
    st.markdown("""
| 항목 | 결론 |
|------|------|
| **원인** | 8월 대비 광고비 +66% 투입 → 광고노출 +31.8% |
| **퍼널 전환율** | 모든 단계 ±0.3% 이내 — 광고 효율성은 유지 |
| **CPM 상승** | +27.8% → 경쟁 강도 증가 또는 지면 품질 저하 |
| **채널 전반 확대** | 특정 채널이 아닌 3개 채널 공통 증액 (+30~34%) |
| **효율 악화** | 비용 효율(CPA) +26.1% → 더 많이 쓰고 더 비싸게 달성 |
| **시사점** | 예산 확대 시 CPM 효율 먼저 검토; 영상 소재 비중 ↑ + 네이버 키워드 최적화 필요 |
    """)
