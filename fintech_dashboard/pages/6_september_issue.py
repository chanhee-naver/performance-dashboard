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

DATA_DIR = Path(__file__).parent.parent / "data"

@st.cache_data
def load_repeat_driver():
    return pd.read_csv(DATA_DIR / "sep_repeat_driver_decomposition.csv")

@st.cache_data
def load_cpa_driver():
    return pd.read_csv(DATA_DIR / "sep_cpa_driver_decomposition.csv")

@st.cache_data
def load_segments():
    return pd.read_csv(DATA_DIR / "sep_segment_changes.csv")

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

st.info("📌 **핵심 결론**: 다른 전환율은 ±0.2% 이내로 안정적. **광고노출 +31.8%**가 반복사용 +31.7% 증가의 핵심 드라이버.")

st.divider()

# ── Waterfall: 반복사용 증가 원인 분해 ──────────────────────────────────────
with st.container(border=True):
    st.subheader("📊 반복사용 증가 원인 분해 (로그 기여도)")
    st.caption("각 퍼널 단계가 반복사용수 MoM 증가에 기여한 비율 — 광고노출이 98.9% 기여")

    scope_tab = st.selectbox(
        "분석 범위",
        ["전체", "계좌개설", "회원가입"],
        key="wf_scope",
    )

    try:
        repeat_df = load_repeat_driver()
        wf_data = repeat_df[repeat_df["scope"] == scope_tab].copy()

        label_map = {
            "광고노출": "광고노출",
            "CTR": "CTR",
            "클릭설치율": "클릭→설치율",
            "설치실행율": "설치→실행율",
            "실행가입율": "실행→가입율",
            "가입계좌개설율": "가입→계좌율",
            "계좌첫거래율": "계좌→첫거래율",
            "첫거래반복사용율": "첫거래→반복율",
        }
        wf_data["label"] = wf_data["metric"].map(label_map).fillna(wf_data["metric"])
        wf_data = wf_data.sort_values("contribution_pct", ascending=False)

        measures = []
        texts = []
        for _, r in wf_data.iterrows():
            measures.append("relative")
            pct = r["contribution_pct"] * 100
            texts.append(f"{pct:+.1f}%")

        fig_wf = go.Figure(go.Waterfall(
            name="기여도",
            orientation="v",
            measure=measures,
            x=wf_data["label"].tolist(),
            y=(wf_data["contribution_pct"] * 100).tolist(),
            text=texts,
            textposition="outside",
            connector=dict(line=dict(color="rgba(100,100,100,0.4)", width=1, dash="dot")),
            increasing=dict(marker=dict(color="#4F9CF9")),
            decreasing=dict(marker=dict(color="#FF6B6B")),
        ))
        fig_wf.add_hline(y=0, line_width=1, line_color="rgba(150,150,150,0.5)")
        fig_wf.update_layout(
            height=400,
            yaxis_title="기여도 (%)",
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_wf)

        dom_driver = wf_data.iloc[0]
        st.caption(
            f"💡 **{scope_tab} 범위**: "
            f"'{dom_driver['label']}' 단계가 반복사용 증가의 "
            f"**{dom_driver['contribution_pct']*100:.1f}%**를 설명합니다."
        )
    except Exception as e:
        st.warning(f"원인분해 데이터 로드 실패: {e}")

st.divider()

# ── CPA 단가 변화 분해 ────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("💸 반복사용당 단가 변화 원인 분해")
    st.caption("광고비 증가(CPA 악화 요인) vs 반복사용 증가(CPA 개선 요인) 상쇄 관계")

    try:
        cpa_df = load_cpa_driver()
        scope_tab2 = st.selectbox(
            "분석 범위",
            ["전체", "계좌개설", "회원가입"],
            key="cpa_scope",
        )
        cpa_data = cpa_df[cpa_df["scope"] == scope_tab2].copy()

        fig_cpa = go.Figure()
        colors_cpa = {
            "광고비": "#FF6B6B",
            "반복사용": "#4F9CF9",
        }
        for _, r in cpa_data.iterrows():
            pct = r["contribution_pct"] * 100
            fig_cpa.add_trace(go.Bar(
                name=r["metric"],
                x=[r["metric"]],
                y=[pct],
                marker_color=colors_cpa.get(r["metric"], "#888"),
                text=[f"{pct:+.1f}%"],
                textposition="outside",
                width=0.5,
            ))

        fig_cpa.add_hline(y=0, line_width=1.5, line_color="rgba(150,150,150,0.6)")
        fig_cpa.update_layout(
            height=340,
            yaxis_title="단가 변화 기여도 (%)",
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            barmode="group",
        )
        st.plotly_chart(fig_cpa)

        cost_row = cpa_data[cpa_data["metric"] == "광고비"].iloc[0]
        rep_row  = cpa_data[cpa_data["metric"] == "반복사용"].iloc[0]
        st.markdown(
            f"- 광고비 +{cost_row['mom']*100:.1f}% → CPA **+{cost_row['contribution_pct']*100:.1f}%** 상승 압력  \n"
            f"- 반복사용 +{rep_row['mom']*100:.1f}% → CPA **{rep_row['contribution_pct']*100:.1f}%** 상쇄  \n"
            f"- 순 CPA 변화: **+{(cost_row['contribution_pct']+rep_row['contribution_pct'])*100:.1f}%**"
        )
    except Exception as e:
        st.warning(f"CPA 분해 데이터 로드 실패: {e}")

st.divider()

# ── 세그먼트 버블 산점도 ────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🫧 세그먼트별 효율 vs 반복사용 증분")
    st.caption("x축: 반복사용 증분(절대량) | y축: CPA_반복사용(9월) | 버블 크기: 광고노출 증분")

    try:
        seg_df = load_segments()
        seg_type = st.selectbox(
            "세그먼트 유형",
            ["전체", "channel", "creative_format", "ad_group", "campaign_objective"],
            format_func=lambda x: {
                "전체": "전체 보기",
                "channel": "채널",
                "creative_format": "소재 형식",
                "ad_group": "광고 그룹",
                "campaign_objective": "캠페인 목적",
            }.get(x, x),
            key="seg_type",
        )

        if seg_type == "전체":
            plot_df = seg_df.copy()
        else:
            plot_df = seg_df[seg_df["segment_type"] == seg_type].copy()

        type_color_map = {
            "channel": "#4285F4",
            "creative_format": "#F5A623",
            "ad_group": "#44BB44",
            "campaign_objective": "#B47FFF",
        }

        fig_bub = go.Figure()
        for seg_t in plot_df["segment_type"].unique():
            sub = plot_df[plot_df["segment_type"] == seg_t]
            fig_bub.add_trace(go.Scatter(
                x=sub["반복사용_delta"],
                y=sub["CPA_반복사용_target"],
                mode="markers+text",
                name={"channel": "채널", "creative_format": "소재",
                      "ad_group": "광고그룹", "campaign_objective": "목적"}.get(seg_t, seg_t),
                marker=dict(
                    size=np.sqrt(sub["광고노출_delta"] / sub["광고노출_delta"].max()) * 60 + 10,
                    color=type_color_map.get(seg_t, "#888"),
                    opacity=0.75,
                    line=dict(width=1.5, color="rgba(255,255,255,0.4)"),
                ),
                text=sub["segment"],
                textposition="top center",
                textfont=dict(size=11),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "반복사용 증분: %{x:,.0f}건<br>"
                    "CPA_반복사용(9월): ₩%{y:,.0f}<br>"
                    "<extra></extra>"
                ),
            ))

        fig_bub.update_layout(
            height=450,
            xaxis_title="반복사용 증분 (건)",
            yaxis_title="CPA_반복사용 9월 (원)",
            legend=dict(orientation="h", y=-0.15),
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bub)
        st.caption("🔵 왼쪽 하단 = 소규모 증분·저단가(효율), 오른쪽 상단 = 대규모 증분·고단가(볼륨 우선)")
    except Exception as e:
        st.warning(f"세그먼트 데이터 로드 실패: {e}")

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

    try:
        vid_row = merged_cr[merged_cr['creative_format']=='영상']['노출_MoM'].values[0]
        img_row = merged_cr[merged_cr['creative_format']=='이미지']['노출_MoM'].values[0]
        st.caption(f"영상: MoM +{vid_row:.1f}% | 이미지: MoM +{img_row:.1f}%")
    except IndexError:
        pass

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
