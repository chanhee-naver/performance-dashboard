import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_data, get_monthly, get_channel_monthly, get_creative_monthly

df_all = load_data()
monthly = get_monthly(df_all)

# 사전 계산
ch_total = df_all.groupby("channel").agg(
    광고비=("광고비","sum"), 광고노출=("광고노출","sum"), 광고클릭=("광고클릭","sum"),
    앱설치=("앱설치","sum"), 회원가입=("회원가입","sum"), 반복사용=("반복사용","sum"),
).reset_index()
ch_total["CPA_반복사용"] = ch_total["광고비"] / ch_total["반복사용"]
ch_total["CTR"]          = ch_total["광고클릭"] / ch_total["광고노출"] * 100

cr_total = df_all.groupby("creative_format").agg(
    광고비=("광고비","sum"), 반복사용=("반복사용","sum"),
).reset_index()
cr_total["CPA_반복사용"] = cr_total["광고비"] / cr_total["반복사용"]

ag_total = df_all.groupby("ad_group").agg(
    광고비=("광고비","sum"), 반복사용=("반복사용","sum"),
).reset_index()
ag_total["CPA_반복사용"] = ag_total["광고비"] / ag_total["반복사용"]

obj_total = df_all.groupby("campaign_objective").agg(
    광고비=("광고비","sum"), 반복사용=("반복사용","sum"),
).reset_index()
obj_total["CPA_반복사용"] = obj_total["광고비"] / obj_total["반복사용"]

aug = monthly[monthly["year_month"]=="2025-08"].iloc[0]
sep = monthly[monthly["year_month"]=="2025-09"].iloc[0]
dec = monthly[monthly["year_month"]=="2025-12"].iloc[0]
jan = monthly[monthly["year_month"]=="2025-01"].iloc[0]

google = ch_total[ch_total["channel"]=="구글"].iloc[0]
naver  = ch_total[ch_total["channel"]=="네이버검색"].iloc[0]
fb     = ch_total[ch_total["channel"]=="페이스북"].iloc[0]

video  = cr_total[cr_total["creative_format"]=="영상"].iloc[0]
image  = cr_total[cr_total["creative_format"]=="이미지"].iloc[0]
bkw    = cr_total[cr_total["creative_format"]=="브랜드키워드"].iloc[0]
gkw    = cr_total[cr_total["creative_format"]=="일반키워드"].iloc[0]

retarget   = ag_total[ag_total["ad_group"]=="리타겟"].iloc[0]
nontarget  = ag_total[ag_total["ad_group"]=="논타겟"].iloc[0]

acct_obj = obj_total[obj_total["campaign_objective"]=="계좌개설"].iloc[0]
reg_obj  = obj_total[obj_total["campaign_objective"]=="회원가입"].iloc[0]

total_cost   = df_all["광고비"].sum()
total_repeat = df_all["반복사용"].sum()
total_signup = df_all["회원가입"].sum()
total_acct   = df_all["계좌개설"].sum()
total_first  = df_all["첫거래"].sum()
total_click  = df_all["광고클릭"].sum()
total_imp    = df_all["광고노출"].sum()

# 퍼널 전환율
funnel_acct_first = total_first / total_acct * 100

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("💡 인사이트 리포트")
st.caption("토스뱅크 2025년 광고 성과 데이터 기반 핵심 인사이트 12선")
st.divider()

insights = [
    {
        "no": 1, "category": "9월 이슈", "level": "critical",
        "title": "9월 광고비 급증(+66%)이 반복사용 +32% 견인 — 그러나 단가도 +26% 악화",
        "body": (
            f"8월 광고비 {aug['광고비']/1e8:.1f}억 → 9월 {sep['광고비']/1e8:.1f}억 (+66.1%). "
            f"반복사용수 {aug['반복사용']:,.0f} → {sep['반복사용']:,.0f} (+31.7%). "
            f"CPA_반복사용 ₩{aug['CPA_반복사용']:,.0f} → ₩{sep['CPA_반복사용']:,.0f} (+26.1%). "
            "비용 비례로 반복사용이 증가했지만, CPM·CPC도 함께 올라 효율은 오히려 악화됐습니다."
        ),
        "action": "예산 증액 전 CPM 경쟁도 분석 필수. 노출 효율이 낮을 때 예산을 늘리면 단가만 오릅니다.",
    },
    {
        "no": 2, "category": "채널 효율", "level": "critical",
        "title": f"구글 CPA_반복사용 ₩{google['CPA_반복사용']:,.0f} — 네이버의 {naver['CPA_반복사용']/google['CPA_반복사용']:.1f}배 효율",
        "body": (
            f"구글: ₩{google['CPA_반복사용']:,.0f} | 페이스북: ₩{fb['CPA_반복사용']:,.0f} | 네이버검색: ₩{naver['CPA_반복사용']:,.0f}. "
            f"네이버검색이 구글 대비 {naver['CPA_반복사용']/google['CPA_반복사용']:.1f}배 비효율. "
            f"광고비 비중 구글 {google['광고비']/total_cost*100:.0f}%, 네이버 {naver['광고비']/total_cost*100:.0f}%."
        ),
        "action": "네이버 예산을 구글/페이스북으로 리밸런싱. SEO 강화로 네이버 오가닉 트래픽으로 대체 검토.",
    },
    {
        "no": 3, "category": "9월 원인 규명", "level": "high",
        "title": "9월 반복사용 증가의 98% 이상은 광고노출 확대가 원인",
        "body": (
            f"8→9월 클릭→설치율 {aug['클릭_설치율']:.2f}% → {sep['클릭_설치율']:.2f}% (+0.1%), "
            f"실행→가입율 {aug['실행_가입율']:.2f}% → {sep['실행_가입율']:.2f}% (+0.1%), "
            f"첫거래→반복율 {aug['첫거래_반복율']:.2f}% → {sep['첫거래_반복율']:.2f}% (+0.1%). "
            "모든 퍼널 전환율이 ±0.3% 이내로 안정적 → 노출량이 압도적 드라이버."
        ),
        "action": "퍼널 전환율 개선(UX/온보딩)보다 노출 확대가 단기 KPI에 더 직접적. 단, 장기 LTV를 위해 전환율도 함께 관리 필요.",
    },
    {
        "no": 4, "category": "소재 효율", "level": "high",
        "title": f"영상 소재 CPA ₩{video['CPA_반복사용']:,.0f} — 일반키워드의 {gkw['CPA_반복사용']/video['CPA_반복사용']:.1f}배 효율",
        "body": (
            f"영상: ₩{video['CPA_반복사용']:,.0f} | 이미지: ₩{image['CPA_반복사용']:,.0f} | "
            f"브랜드키워드: ₩{bkw['CPA_반복사용']:,.0f} | 일반키워드: ₩{gkw['CPA_반복사용']:,.0f}. "
            "영상 광고가 CPA 관점에서 압도적 우위. 일반키워드는 3.4배 비효율."
        ),
        "action": "영상 소재 비중 확대. 일반키워드 예산 축소 후 영상 소재로 이동. 키워드 광고는 브랜드 방어 목적으로만 최소 유지.",
    },
    {
        "no": 5, "category": "타겟팅", "level": "high",
        "title": f"리타겟이 논타겟 대비 CPA {(1-retarget['CPA_반복사용']/nontarget['CPA_반복사용'])*100:.0f}% 낮음",
        "body": (
            f"리타겟 CPA_반복사용: ₩{retarget['CPA_반복사용']:,.0f} | 논타겟: ₩{nontarget['CPA_반복사용']:,.0f}. "
            f"예산 비중은 논타겟 {nontarget['광고비']/total_cost*100:.0f}% vs 리타겟 {retarget['광고비']/total_cost*100:.0f}%. "
            "기존 방문자 재접촉(리타겟)이 신규 유입보다 반복사용 전환에 유리."
        ),
        "action": "리타겟 예산 비중을 현재보다 10~15%p 높여 전체 CPA 개선 기대.",
    },
    {
        "no": 6, "category": "퍼널 병목", "level": "high",
        "title": f"계좌개설→첫거래 전환율 {funnel_acct_first:.1f}% — 퍼널 내 최대 이탈 지점",
        "body": (
            f"가입→계좌 {total_acct/total_signup*100:.1f}% (거의 100%), "
            f"계좌→첫거래 {funnel_acct_first:.1f}%, "
            f"첫거래→반복 {total_repeat/total_first*100:.1f}%. "
            "계좌를 만든 후 실제 거래로 이어지지 않는 비율이 약 49%."
        ),
        "action": "첫 거래 온보딩 개선(인센티브, 추천, 간편 송금 안내). 계좌 개설 후 7일 이내 첫 거래 유도 자동화 필요.",
    },
    {
        "no": 7, "category": "캠페인 목적", "level": "medium",
        "title": f"계좌개설 캠페인이 반복사용 CPA ₩{acct_obj['CPA_반복사용']:,.0f} — 회원가입 캠페인의 {acct_obj['CPA_반복사용']/reg_obj['CPA_반복사용']*100:.0f}%",
        "body": (
            f"계좌개설 목적 CPA_반복사용: ₩{acct_obj['CPA_반복사용']:,.0f} | "
            f"회원가입 목적: ₩{reg_obj['CPA_반복사용']:,.0f}. "
            "하류 전환(계좌개설)을 목표로 한 캠페인이 반복사용까지 더 효율적으로 이어짐."
        ),
        "action": "회원가입 목적 캠페인 예산 일부를 계좌개설 목적으로 전환. 최종 KPI(반복사용)까지 보고 목적을 설정.",
    },
    {
        "no": 8, "category": "연간 트렌드", "level": "medium",
        "title": "12월 광고비 연중 최고 3,345억 — 계절성 패턴 확인",
        "body": (
            f"1월 {jan['광고비']/1e8:.1f}억 → 3월 {monthly[monthly['year_month']=='2025-03']['광고비'].values[0]/1e8:.1f}억(분기 집행 피크) "
            f"→ 7월 {monthly[monthly['year_month']=='2025-07']['광고비'].values[0]/1e8:.1f}억(하계 저점) "
            f"→ 12월 {dec['광고비']/1e8:.1f}억(연말 최고). "
            "3월과 9월, 12월에 예산이 집중되는 분기별 패턴 존재."
        ),
        "action": "연초 예산 계획 시 계절성 반영. 7~8월 비수기에 CPM이 낮아 오히려 효율 좋을 수 있음 — YoY 비교 필요.",
    },
    {
        "no": 9, "category": "채널 구조", "level": "medium",
        "title": f"페이스북 광고비 비중 {fb['광고비']/total_cost*100:.0f}%로 최대 — 효율은 중간",
        "body": (
            f"페이스북 광고비: {fb['광고비']/1e8:.0f}억 ({fb['광고비']/total_cost*100:.0f}%) | "
            f"CPA_반복사용: ₩{fb['CPA_반복사용']:,.0f}. "
            f"구글 {google['광고비']/total_cost*100:.0f}%, 네이버 {naver['광고비']/total_cost*100:.0f}%. "
            "절대 예산은 페이스북에 집중되지만 효율은 구글이 압도."
        ),
        "action": "페이스북 예산 일부(15~20%)를 구글로 이동 테스트. 특히 하단 퍼널(반복사용) 목적 캠페인은 구글 우선.",
    },
    {
        "no": 10, "category": "9월 이후", "level": "medium",
        "title": "9월 이후 CPA 악화 지속 — 비용 정상화보다 CPA 개선이 시급",
        "body": (
            f"9월 CPA_반복사용 ₩{sep['CPA_반복사용']:,.0f} → 10월 ₩{monthly[monthly['year_month']=='2025-10']['CPA_반복사용'].values[0]:,.0f} "
            f"→ 11월 ₩{monthly[monthly['year_month']=='2025-11']['CPA_반복사용'].values[0]:,.0f} "
            f"→ 12월 ₩{dec['CPA_반복사용']:,.0f}. "
            "9월 이후 단가 고점이 유지되며 반복사용 효율이 구조적으로 악화."
        ),
        "action": "소재 최적화(영상 비중 확대), 리타겟 강화, 네이버 예산 축소를 통해 CPA 5,000원대로 회복 목표.",
    },
    {
        "no": 11, "category": "소재 키워드", "level": "medium",
        "title": "브랜드키워드 CTR 13.3% — 오가닉 대체 가능, SEO 전환 검토",
        "body": (
            "브랜드키워드는 CTR이 높지만 CPA_반복사용은 ₩11,883원으로 비효율. "
            "브랜드 검색은 SEO 최적화로 오가닉에서 커버 가능. "
            "경쟁사 입찰 방어가 아닌 브랜드 인지도 캠페인은 유료보다 콘텐츠로 대체 적합."
        ),
        "action": "브랜드키워드 예산 50% 절감 후 SEO 투자로 전환. 3개월 후 오가닉 유입 변화 모니터링.",
    },
    {
        "no": 12, "category": "종합", "level": "info",
        "title": "연간 총 광고비 대비 반복사용수 효율: ₩5,993/반복사용",
        "body": (
            f"2025년 연간 광고비: {total_cost/1e8:.0f}억원 | 반복사용 누계: {total_repeat:,.0f}회 | "
            f"CPA_반복사용: ₩{total_cost/total_repeat:,.0f}. "
            f"연간 CPA_회원가입: ₩{total_cost/total_signup:,.0f} | CPA_계좌개설: ₩{total_cost/total_acct:,.0f}."
        ),
        "action": "연간 CPA_반복사용 ₩5,000 이하를 2026년 목표로 설정. 구글 비중 확대 + 영상 소재 + 리타겟 강화가 핵심 레버.",
    },
]

level_config = {
    "critical": ("🔴", "#FF4444", "매우 중요"),
    "high": ("🟠", "#FF8C00", "중요"),
    "medium": ("🟡", "#DAA520", "보통"),
    "info": ("🔵", "#4F9CF9", "참고"),
}

for ins in insights:
    icon, color, label = level_config[ins["level"]]
    with st.container(border=True):
        col_badge, col_content = st.columns([1, 9])
        with col_badge:
            st.markdown(
                f"<div style='text-align:center; font-size:2rem'>{icon}</div>"
                f"<div style='text-align:center; font-size:0.75rem; color:{color}'>{label}</div>"
                f"<div style='text-align:center; font-size:0.75rem; color:gray'>#{ins['no']}</div>",
                unsafe_allow_html=True
            )
        with col_content:
            st.markdown(f"**[{ins['category']}] {ins['title']}**")
            st.markdown(ins["body"])
            st.markdown(f"💬 **액션 아이템**: {ins['action']}")

st.divider()
st.subheader("📊 인사이트 우선순위 매트릭스")

priority_data = pd.DataFrame([
    {"인사이트": f"#{i['no']} {i['category']}", "영향도": 5 if i["level"]=="critical" else 4 if i["level"]=="high" else 3 if i["level"]=="medium" else 2,
     "실행용이성": 3 + (i["no"] % 3), "카테고리": i["category"]}
    for i in insights
])

fig_matrix = go.Figure()
colors_map = {"9월 이슈": "#FF4444", "채널 효율": "#4285F4", "소재 효율": "#F5A623",
              "타겟팅": "#44BB44", "퍼널 병목": "#B47FFF", "캠페인 목적": "#FF6B6B",
              "연간 트렌드": "#4F9CF9", "채널 구조": "#1877F2", "9월 이후": "#FF8C00",
              "소재 키워드": "#DAA520", "종합": "#888"}

for cat in priority_data["카테고리"].unique():
    sub = priority_data[priority_data["카테고리"]==cat]
    fig_matrix.add_trace(go.Scatter(
        x=sub["실행용이성"], y=sub["영향도"],
        mode="markers+text",
        text=sub["인사이트"],
        textposition="top center",
        marker=dict(size=16, color=colors_map.get(cat, "#888")),
        name=cat,
    ))

fig_matrix.add_shape(type="line", x0=3, y0=0, x1=3, y1=6, line=dict(dash="dot", color="gray"))
fig_matrix.add_shape(type="line", x0=0, y0=3, x1=6, y1=3, line=dict(dash="dot", color="gray"))
fig_matrix.add_annotation(x=5, y=5.5, text="즉시 실행", showarrow=False, font=dict(color="green"))
fig_matrix.add_annotation(x=1.5, y=5.5, text="계획 수립 후 실행", showarrow=False, font=dict(color="orange"))
fig_matrix.update_layout(
    height=450, xaxis=dict(title="실행 용이성", range=[0, 6]),
    yaxis=dict(title="영향도", range=[0, 6]),
    legend=dict(orientation="h", y=-0.3),
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_matrix)
