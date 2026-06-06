import streamlit as st

st.set_page_config(
    page_title="토스뱅크 광고 성과 대시보드",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("pages/1_overview.py",           title="개요",            icon="📊", default=True),
    st.Page("pages/2_channel.py",            title="채널 분석",        icon="📡"),
    st.Page("pages/3_funnel.py",             title="퍼널 분석",        icon="🔽"),
    st.Page("pages/4_creative.py",           title="소재 분석",        icon="🎨"),
    st.Page("pages/5_metric_hierarchy.py",   title="Metric Hierarchy", icon="🌲"),
    st.Page("pages/6_september_issue.py",    title="9월 이슈 드릴다운", icon="🔍"),
    st.Page("pages/7_insights.py",           title="인사이트 리포트",   icon="💡"),
]

pg = st.navigation(pages)
pg.run()
