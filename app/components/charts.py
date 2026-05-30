from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

CHANNEL_COLORS = {
    "구글": "#4285F4",
    "메타": "#1877F2",
    "네이버": "#03C75A",
}

_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(orientation="h", y=-0.15),
    font=dict(size=12),
)


def _apply(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT)
    return fig


def bar_by_channel(df: pd.DataFrame, y: str, title: str = "") -> go.Figure:
    agg = df.groupby("channel", as_index=False)[y].sum()
    fig = px.bar(
        agg, x="channel", y=y, color="channel",
        color_discrete_map=CHANNEL_COLORS, title=title,
        labels={y: "", "channel": ""},
    )
    return _apply(fig)


def bar_roas_by_channel(df: pd.DataFrame) -> go.Figure:
    agg = df.groupby("channel", as_index=False).agg(
        ch_cost=("ch_cost", "sum"),
        af_revenue=("af_revenue", "sum"),
    )
    agg["roas_af"] = agg["af_revenue"] / agg["ch_cost"].replace(0, None)
    fig = px.bar(
        agg, x="channel", y="roas_af", color="channel",
        color_discrete_map=CHANNEL_COLORS, title="채널별 ROAS(AF)",
        labels={"roas_af": "", "channel": ""},
    )
    return _apply(fig)


def line_daily(df: pd.DataFrame, y: str, title: str = "") -> go.Figure:
    daily = df.groupby(["date", "channel"], as_index=False)[y].sum()
    fig = px.line(
        daily, x="date", y=y, color="channel",
        color_discrete_map=CHANNEL_COLORS, title=title,
        labels={y: "", "date": ""},
    )
    return _apply(fig)


def line_daily_ratio(df: pd.DataFrame, num: str, denom: str, title: str = "") -> go.Figure:
    daily = df.groupby("date", as_index=False).agg(n=(num, "sum"), d=(denom, "sum"))
    daily["ratio"] = daily["n"] / daily["d"].replace(0, None)
    fig = px.line(daily, x="date", y="ratio", title=title, labels={"ratio": "", "date": ""})
    fig.update_traces(line_color="#4C9BE8", line_width=2)
    return _apply(fig)


def scatter_creative(df: pd.DataFrame) -> go.Figure:
    grp = (
        df.groupby(["creative", "channel", "creative_type"], as_index=False)
        .agg(ctr=("ctr", "mean"), roas_af=("roas_af", "mean"),
             ch_cost=("ch_cost", "sum"), af_purchases=("af_purchases", "sum"))
        .dropna(subset=["ctr", "roas_af"])
    )
    fig = px.scatter(
        grp, x="ctr", y="roas_af", size="ch_cost", color="channel",
        color_discrete_map=CHANNEL_COLORS,
        hover_data=["creative", "af_purchases"],
        size_max=40,
        labels={"ctr": "CTR (%)", "roas_af": "ROAS (AF)"},
        title="소재 효율 분포 (CTR × ROAS, 원 크기 = 광고비)",
    )
    return _apply(fig)


def gap_heatmap(df: pd.DataFrame) -> go.Figure:
    agg = df.groupby("channel", as_index=False).agg(
        signup=("signup_gap_pct", "mean"),
        purchase=("purchase_gap_pct", "mean"),
        revenue=("revenue_gap_pct", "mean"),
    ).fillna(0)

    channels = agg["channel"].tolist()
    z = [agg["signup"].tolist(), agg["purchase"].tolist(), agg["revenue"].tolist()]
    text = [[f"{v:.0f}%" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z, x=channels,
        y=["회원가입 갭", "구매 갭", "매출 갭"],
        colorscale=[[0, "#c62828"], [0.6, "#f9a825"], [0.8, "#388e3c"], [1, "#1b5e20"]],
        zmin=0, zmax=100,
        text=text, texttemplate="%{text}",
    ))
    fig.update_layout(title="채널별 어트리뷰션 갭 (높을수록 AF ≈ 플랫폼)", **_LAYOUT)
    return fig


def gap_trend(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby(["date", "channel"], as_index=False).agg(
        af_rev=("af_revenue", "sum"), ch_rev=("ch_revenue", "sum")
    )
    daily["gap"] = daily["af_rev"] / daily["ch_rev"].replace(0, None) * 100
    fig = px.line(
        daily, x="date", y="gap", color="channel",
        color_discrete_map=CHANNEL_COLORS,
        labels={"gap": "매출 갭 (%)", "date": ""},
        title="채널별 매출 갭 트렌드",
    )
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="정상(80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="주의(60%)")
    return _apply(fig)
