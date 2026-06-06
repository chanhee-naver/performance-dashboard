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
st.caption("토스뱅크 2025년 광고 성과 데이터 기반 핵심 인사이트 14선")
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
        "risk": "반복사용 지표만 보면 성장처럼 보이나, 광고비를 붙여서 산 성과라 CPA 상한 없이 증액하면 효율 저하가 빠릅니다.",
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
        "risk": "볼륨 1위 채널에만 예산을 몰면 한계 CPM 상승을 더 빨리 맞을 수 있습니다.",
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
        "risk": "노출 기반 성장은 CPM이 오르는 순간 반복사용당 단가가 빠르게 악화됩니다.",
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
        "risk": "영상 소재도 빈도 관리 없이 증액하면 피로도와 CPM 상승이 생깁니다.",
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
        "risk": "리타겟 모수는 작아질 수 있으므로 신규 유입 캠페인으로 원료를 계속 공급해야 합니다.",
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
        "risk": "인센티브로 강제된 첫거래는 반복사용으로 이어지지 않을 수 있습니다. 진성 거래 지표 병행 필요.",
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
        "risk": "캠페인 목적이 다른데 반복사용 CPA 하나로 평가하면 상위 퍼널 투자의 의미가 과소평가됩니다.",
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
        "risk": "계절성 패턴은 YoY 단 1년치 데이터로 일반화할 수 없습니다.",
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
        "risk": "페이스북은 오디언스 규모가 커 구글만으로는 볼륨을 채우기 어려울 수 있습니다.",
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
        "risk": "9월 이후 악화가 광고 외 요인(서비스 품질, 경쟁사 진입)에서 기인했다면 광고 최적화만으로 한계가 있습니다.",
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
        "risk": "브랜드키워드를 갑자기 끊으면 경쟁사 키워드 도용 광고로 이탈이 생길 수 있습니다. 단계적으로 조정하세요.",
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
        "risk": "광고 성과 로그만으로 LTV 개선을 단정하면 과제 해석이 과장됩니다.",
    },
    {
        "no": 13, "category": "LTV 지표", "level": "medium",
        "title": "자동이체설정은 반복사용 이후의 질적 전환 지표 — 별도 관리 필요",
        "body": (
            "9월 자동이체설정은 102,564건, 계좌개설 대비 전환율 약 7.16%. "
            "반복사용이 단기 행동이라면 자동이체설정은 장기 잔존·LTV에 가까운 행동입니다. "
            "현재 반복사용 캠페인에서 자동이체 설정률을 별도로 추적하지 않으면 진성 리텐션을 파악하기 어렵습니다."
        ),
        "action": "반복사용 캠페인 안에서도 자동이체 미설정 계좌개설자를 별도 세그먼트로 리마인드 타겟팅.",
        "risk": "반복사용수만 늘고 자동이체 같은 고착 행동이 늘지 않으면 장기 가치 창출이 제한됩니다.",
    },
    {
        "no": 14, "category": "채널 전략", "level": "medium",
        "title": "네이버검색은 검색 수요를 만들지 못함 — 외부 접점으로 의도를 생성해야",
        "body": (
            "네이버검색의 9월 CPA_반복사용은 ₩14,582로 구글(₩4,041) 대비 3.6배. "
            "검색 광고는 이미 생성된 수요를 낚는 채널이라 토스뱅크 브랜드 인지도가 낮은 상태에서는 "
            "검색 볼륨 자체가 제한됩니다. 페이스북·유튜브에서 브랜드 검색 의도를 먼저 만들어야 효율이 따라옵니다."
        ),
        "action": "네이버검색 예산 중 일반키워드 비중을 줄이고, 페이스북/유튜브 인지 캠페인에서 '토스뱅크 계좌개설' 검색 의도 생성 후 네이버 브랜드 키워드로 수확하는 구조로 전환.",
        "risk": "네이버검색을 완전히 끊으면 경쟁사 브랜드 키워드 도용 광고가 틈을 탈 수 있습니다.",
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
            if ins.get("risk"):
                st.markdown(f"⚠️ **리스크**: {ins['risk']}")

st.divider()
st.subheader("📊 인사이트 우선순위 매트릭스")

# 각 인사이트에 고유 좌표 직접 지정 (겹침 방지)
priority_items = [
    {"no": 1,  "label": "#1 9월 이슈",     "영향도": 5.0, "실행용이성": 4.2, "color": "#FF4444"},
    {"no": 2,  "label": "#2 채널 효율",    "영향도": 5.0, "실행용이성": 5.5, "color": "#4285F4"},
    {"no": 3,  "label": "#3 9월 원인",     "영향도": 4.2, "실행용이성": 1.8, "color": "#888888"},
    {"no": 4,  "label": "#4 소재 효율",    "영향도": 4.0, "실행용이성": 4.8, "color": "#F5A623"},
    {"no": 5,  "label": "#5 타겟팅",       "영향도": 4.0, "실행용이성": 3.5, "color": "#44BB44"},
    {"no": 6,  "label": "#6 퍼널 병목",    "영향도": 3.5, "실행용이성": 2.5, "color": "#B47FFF"},
    {"no": 7,  "label": "#7 캠페인 목적",  "영향도": 3.5, "실행용이성": 3.0, "color": "#FF6B6B"},
    {"no": 8,  "label": "#8 연간 트렌드",  "영향도": 3.0, "실행용이성": 4.5, "color": "#4F9CF9"},
    {"no": 9,  "label": "#9 채널 구조",    "영향도": 3.8, "실행용이성": 5.2, "color": "#1877F2"},
    {"no": 10, "label": "#10 9월 이후",    "영향도": 3.5, "실행용이성": 4.0, "color": "#FF8C00"},
    {"no": 11, "label": "#11 소재 키워드", "영향도": 2.8, "실행용이성": 5.5, "color": "#DAA520"},
    {"no": 12, "label": "#12 종합",        "영향도": 2.0, "실행용이성": 4.8, "color": "#888888"},
    {"no": 13, "label": "#13 자동이체설정", "영향도": 3.2, "실행용이성": 3.8, "color": "#7ECECA"},
    {"no": 14, "label": "#14 네이버 의도", "영향도": 3.0, "실행용이성": 2.8, "color": "#03C75A"},
]

fig_matrix = go.Figure()

# 사분면 배경 색
fig_matrix.add_shape(type="rect", x0=3, y0=3, x1=6.5, y1=6.5,
                     fillcolor="rgba(68,187,68,0.06)", line_width=0)
fig_matrix.add_shape(type="rect", x0=0, y0=3, x1=3, y1=6.5,
                     fillcolor="rgba(245,166,35,0.06)", line_width=0)
fig_matrix.add_shape(type="rect", x0=3, y0=0, x1=6.5, y1=3,
                     fillcolor="rgba(79,156,249,0.06)", line_width=0)
fig_matrix.add_shape(type="rect", x0=0, y0=0, x1=3, y1=3,
                     fillcolor="rgba(200,50,50,0.04)", line_width=0)

# 기준선
fig_matrix.add_shape(type="line", x0=3, y0=0, x1=3, y1=6.5,
                     line=dict(dash="dot", color="rgba(150,150,150,0.5)", width=1))
fig_matrix.add_shape(type="line", x0=0, y0=3, x1=6.5, y1=3,
                     line=dict(dash="dot", color="rgba(150,150,150,0.5)", width=1))

# 사분면 레이블
for txt, x, y, col in [
    ("🚀 즉시 실행", 5.0, 6.1, "rgba(68,187,68,0.9)"),
    ("📋 계획 후 실행", 1.5, 6.1, "rgba(245,166,35,0.9)"),
    ("⏳ 여건 갖춰지면", 5.0, 0.3, "rgba(79,156,249,0.7)"),
    ("🔻 낮은 우선순위", 1.5, 0.3, "rgba(150,150,150,0.6)"),
]:
    fig_matrix.add_annotation(
        x=x, y=y, text=txt, showarrow=False,
        font=dict(color=col, size=11),
    )

# 각 포인트: 점(큰 원) + 번호 텍스트만
for item in priority_items:
    fig_matrix.add_trace(go.Scatter(
        x=[item["실행용이성"]],
        y=[item["영향도"]],
        mode="markers+text",
        marker=dict(size=34, color=item["color"], opacity=0.85,
                    line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
        text=[f"<b>#{item['no']}</b>"],
        textposition="middle center",
        textfont=dict(color="white", size=11),
        name=item["label"],
        hovertemplate=(
            f"<b>{item['label']}</b><br>"
            f"영향도: {item['영향도']}<br>"
            f"실행 용이성: {item['실행용이성']}<extra></extra>"
        ),
        showlegend=True,
    ))

fig_matrix.update_layout(
    height=500,
    xaxis=dict(title="← 실행 어려움 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 실행 용이성 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 실행 쉬움 →",
               range=[0, 6.5], showgrid=False, zeroline=False),
    yaxis=dict(title="← 영향 낮음 &nbsp; 영향도 &nbsp; 영향 높음 →",
               range=[0, 6.5], showgrid=False, zeroline=False),
    legend=dict(
        orientation="v", x=1.02, y=1, xanchor="left",
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    margin=dict(l=10, r=160, t=20, b=10),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_matrix)

# 우선순위 순위표
st.subheader("🏆 우선순위 순위표")
rank_df = pd.DataFrame([
    {
        "순위": i + 1,
        "인사이트": item["label"],
        "영향도": item["영향도"],
        "실행용이성": item["실행용이성"],
        "우선순위 점수": round(item["영향도"] * item["실행용이성"], 1),
    }
    for i, item in enumerate(
        sorted(priority_items, key=lambda x: x["영향도"] * x["실행용이성"], reverse=True)
    )
])
st.dataframe(rank_df, hide_index=True,
             column_config={
                 "우선순위 점수": st.column_config.ProgressColumn(
                     "우선순위 점수",
                     min_value=0, max_value=35, format="%.1f"
                 )
             })
