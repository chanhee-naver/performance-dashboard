import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_data, get_monthly

df_all = load_data()
monthly = get_monthly(df_all)

st.title("🌲 Metric Hierarchy")
st.caption("반복사용수 = 광고노출 × CTR × 클릭→설치율 × 설치→실행율 × 실행→가입율 × 가입→계좌율 × 계좌→첫거래율 × 첫거래→반복율")
st.divider()

# ── 월 선택 ───────────────────────────────────────────────────────────────────
selected_month = st.selectbox(
    "분석 월 선택",
    monthly["year_month"].tolist(),
    index=len(monthly) - 1,
)
prev_idx = monthly[monthly["year_month"] == selected_month].index[0]
row = monthly.loc[prev_idx]
prev_row = monthly.loc[prev_idx - 1] if prev_idx > 0 else row

# ── 분해 지표 ─────────────────────────────────────────────────────────────────
total_imp     = row["광고노출"]
ctr           = row["CTR"] / 100
click_install = row["클릭_설치율"] / 100
install_run   = row["설치_실행율"] / 100
run_signup    = row["실행_가입율"] / 100
signup_acct   = row["가입_계좌율"] / 100
acct_first    = row["계좌_첫거래율"] / 100
first_repeat  = row["첫거래_반복율"] / 100
repeat_actual = row["반복사용"]

repeat_model = (total_imp * ctr * click_install * install_run *
                run_signup * signup_acct * acct_first * first_repeat)

# MoM 델타
def mom_delta(cur_row, prev_row, col):
    c, p = cur_row[col], prev_row[col]
    return f"{(c/p-1)*100:+.1f}%" if p and p != 0 else "-"

# ── 핵심 KPI 행 ───────────────────────────────────────────────────────────────
st.subheader(f"📅 {selected_month} 핵심 드라이버")

cols_a = st.columns(4)
metrics = [
    ("광고노출", f"{total_imp/1e6:.1f}M회", mom_delta(row, prev_row, "광고노출")),
    ("CTR", f"{ctr*100:.3f}%", mom_delta(row, prev_row, "CTR")),
    ("CPA_반복사용", f"₩{row['CPA_반복사용']:,.0f}", mom_delta(row, prev_row, "CPA_반복사용")),
    ("반복사용수", f"{repeat_actual:,.0f}", mom_delta(row, prev_row, "반복사용")),
]
for i, (label, val, delta) in enumerate(metrics):
    with cols_a[i]:
        st.metric(label, val, delta=delta, border=True)

st.divider()

# ── Sankey 다이어그램 ─────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🌊 퍼널 Sankey 다이어그램")

    nodes = ["광고클릭", "앱설치", "앱실행", "회원가입", "계좌개설", "첫거래", "반복사용",
             "미설치", "미실행", "미가입", "미계좌", "미첫거래", "미반복"]
    node_colors = (
        ["#4F9CF9"] * 7 +  # funnel nodes
        ["rgba(200,200,200,0.4)"] * 6  # drop nodes
    )

    clicks    = int(row["광고클릭"])
    installs  = int(row["앱설치"])
    runs      = int(row["앱실행"])
    signups   = int(row["회원가입"])
    accounts  = int(row["계좌개설"])
    firsts    = int(row["첫거래"])
    repeats   = int(row["반복사용"])

    drops = [
        clicks - installs, installs - runs, runs - signups,
        signups - accounts, accounts - firsts, firsts - repeats,
    ]

    src  = [0, 1, 2, 3, 4, 5,  0, 1, 2, 3, 4, 5]
    tgt  = [1, 2, 3, 4, 5, 6,  7, 8, 9,10,11,12]
    val  = [installs, runs, signups, accounts, firsts, repeats] + [max(0, d) for d in drops]

    fig_sankey = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20, thickness=20,
            label=nodes,
            color=node_colors,
        ),
        link=dict(
            source=src, target=tgt, value=val,
            color=["rgba(79,156,249,0.4)"] * 6 + ["rgba(200,50,50,0.15)"] * 6,
        ),
    ))
    fig_sankey.update_layout(
        height=450, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_sankey)

st.divider()

# ── Metric Tree (Treemap) ──────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🌳 Metric Hierarchy Tree (반복사용수 분해)")

    # Build contribution analysis
    # 반복사용 = 노출 * CTR * 클릭설치 * 설치실행 * 실행가입 * 가입계좌 * 계좌첫거래 * 첫거래반복
    # Contributions via ln decomposition (MoM)
    prev_repeat = prev_row["반복사용"]
    cur_repeat  = row["반복사용"]
    total_change = cur_repeat - prev_repeat

    driver_cols = {
        "광고노출":     "광고노출",
        "CTR":          "CTR",
        "클릭→설치율":  "클릭_설치율",
        "설치→실행율":  "설치_실행율",
        "실행→가입율":  "실행_가입율",
        "가입→계좌율":  "가입_계좌율",
        "계좌→첫거래율":"계좌_첫거래율",
        "첫거래→반복율":"첫거래_반복율",
    }

    contrib_data = []
    for label, col in driver_cols.items():
        c_val = row[col]
        p_val = prev_row[col]
        if p_val and p_val != 0:
            pct_change = (c_val / p_val - 1) * 100
        else:
            pct_change = 0
        contrib_data.append({"지표": label, "MoM변화율(%)": pct_change, "현재값": c_val})

    contrib_df = pd.DataFrame(contrib_data)

    labels = ["반복사용수"] + contrib_df["지표"].tolist()
    parents = [""] + ["반복사용수"] * len(contrib_df)
    values = [abs(total_change) if total_change != 0 else 1] + [max(abs(v), 0.001) for v in contrib_df["MoM변화율(%)"]]
    colors = ["#4F9CF9"] + [
        "#FF4444" if v > 0 else "#44BB44" if v < 0 else "#888"
        for v in contrib_df["MoM변화율(%)"]
    ]

    fig_tree = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        texttemplate="<b>%{label}</b><br>MoM: %{customdata:.1f}%",
        customdata=[0] + contrib_df["MoM변화율(%)"].tolist(),
        hovertemplate="<b>%{label}</b><br>MoM 변화율: %{customdata:.2f}%<extra></extra>",
    ))
    fig_tree.update_layout(
        height=400, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_tree)

    st.caption("🔴 빨간색 = MoM 증가(비용 증가 포함), 🟢 초록색 = MoM 감소")

st.divider()

# ── 전환율 MoM 비교 ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader(f"📊 {selected_month} vs 전월 드라이버 비교")
    rate_cols = {
        "광고노출(M)": ("광고노출", 1e6),
        "CTR(%)": ("CTR", 1),
        "클릭→설치(%)": ("클릭_설치율", 1),
        "설치→실행(%)": ("설치_실행율", 1),
        "실행→가입(%)": ("실행_가입율", 1),
        "가입→계좌(%)": ("가입_계좌율", 1),
        "계좌→첫거래(%)": ("계좌_첫거래율", 1),
        "첫거래→반복(%)": ("첫거래_반복율", 1),
    }
    compare_data = []
    for label, (col, scale) in rate_cols.items():
        compare_data.append({
            "지표": label,
            "전월": prev_row[col] / scale,
            "당월": row[col] / scale,
            "MoM": f"{(row[col]/prev_row[col]-1)*100:+.2f}%" if prev_row[col] else "-",
        })
    cmp_df = pd.DataFrame(compare_data)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name="전월", x=cmp_df["지표"], y=cmp_df["전월"],
                             marker_color="rgba(100,150,255,0.7)"))
    fig_bar.add_trace(go.Bar(name="당월", x=cmp_df["지표"], y=cmp_df["당월"],
                             marker_color="#4F9CF9"))
    fig_bar.update_layout(
        barmode="group", height=320, yaxis_title="수치",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar)

    st.dataframe(cmp_df, hide_index=True)
