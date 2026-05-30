from __future__ import annotations

import pandas as pd


def generate_insights(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    insights: list[dict] = []

    # 1. 주간 ROAS WoW 변화 (5% 이상)
    dates = sorted(df["date"].unique())
    if len(dates) >= 14:
        mid = dates[-8]
        recent = df[df["date"] > mid]
        prior  = df[df["date"] <= mid].tail(len(recent) * 3)  # 비슷한 기간

        def _roas(d: pd.DataFrame) -> float:
            cost = d["ch_cost"].sum()
            return d["af_revenue"].sum() / cost if cost > 0 else 0.0

        r_now, r_pre = _roas(recent), _roas(prior)
        if r_pre > 0:
            chg = (r_now - r_pre) / r_pre * 100
            if abs(chg) >= 5:
                up = chg > 0
                insights.append({
                    "icon": "📈" if up else "📉",
                    "text": (
                        f"주간 ROAS <b>{'상승' if up else '하락'} {abs(chg):.1f}%</b> "
                        f"— 최근 7일 {r_now:.2f}x vs 이전 {r_pre:.2f}x"
                    ),
                    "level": "success" if up else "warning",
                })

    # 2. 채널별 ROAS Top / Bottom
    ch = (
        df.groupby("channel", as_index=False)
        .agg(cost=("ch_cost", "sum"), rev=("af_revenue", "sum"))
    )
    ch["roas"] = ch["rev"] / ch["cost"].replace(0, None)
    ch = ch.dropna(subset=["roas"])
    if len(ch) >= 2:
        top = ch.loc[ch["roas"].idxmax()]
        bot = ch.loc[ch["roas"].idxmin()]
        insights.append({
            "icon": "🏆",
            "text": (
                f"ROAS 최고: <b>{top['channel']}</b> {top['roas']:.2f}x"
                f"&emsp;|&emsp;"
                f"최저: <b>{bot['channel']}</b> {bot['roas']:.2f}x"
            ),
            "level": "info",
        })

    # 3. AF 커버리지 이상치 (<70%)
    gap = (
        df.groupby("channel", as_index=False)
        .agg(ch_rev=("ch_revenue", "sum"), af_rev=("af_revenue", "sum"))
    )
    gap["pct"] = gap["af_rev"] / gap["ch_rev"].replace(0, None) * 100
    for _, row in gap.dropna(subset=["pct"]).iterrows():
        if row["pct"] < 70:
            insights.append({
                "icon": "⚠️",
                "text": (
                    f"<b>{row['channel']}</b> 매출 갭 <b>{row['pct']:.0f}%</b>"
                    f" — 어트리뷰션 링크 점검 필요 (기준: 70%)"
                ),
                "level": "error",
            })

    # 4. 일별 비용 스파이크 (평균 + 2σ)
    daily = df.groupby("date")["ch_cost"].sum()
    if len(daily) >= 7:
        mean, std = daily.mean(), daily.std()
        spikes = daily[daily > mean + 2 * std]
        if not spikes.empty:
            d = spikes.idxmax()
            v = spikes.max()
            insights.append({
                "icon": "💸",
                "text": (
                    f"비용 스파이크 감지: <b>{str(d)[:10]}</b> "
                    f"{int(v/10000):,}만원 (평균 대비 <b>+{(v/mean - 1)*100:.0f}%</b>)"
                ),
                "level": "warning",
            })

    # 5. 비용 대비 전환 효율 최고 캠페인
    camp = (
        df.groupby(["channel", "campaign"], as_index=False)
        .agg(cost=("ch_cost", "sum"), purch=("af_purchases", "sum"))
    )
    camp["cpa"] = camp["cost"] / camp["purch"].replace(0, None)
    camp = camp.dropna(subset=["cpa"]).query("purch >= 10")
    if not camp.empty:
        best = camp.loc[camp["cpa"].idxmin()]
        insights.append({
            "icon": "🎯",
            "text": (
                f"CPA 최저 캠페인: <b>{best['campaign']}</b> ({best['channel']})"
                f" — {int(best['cpa']):,}원/건"
            ),
            "level": "success",
        })

    return insights
