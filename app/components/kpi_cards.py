from __future__ import annotations

import streamlit as st

_CARD_STYLE = """
<style>
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 14px 16px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    border-color: #03C75A;
    box-shadow: 0 4px 14px rgba(3,199,90,0.08);
}
.kpi-label {
    font-size: 0.7rem;
    color: #8b949e;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e6edf3;
    white-space: nowrap;
    line-height: 1.2;
    font-family: 'Pretendard', sans-serif;
}
</style>
"""


def render_kpi_row(metrics: list[dict]) -> None:
    st.markdown(_CARD_STYLE, unsafe_allow_html=True)
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'  <div class="kpi-label">{m["label"]}</div>'
                f'  <div class="kpi-value">{m["value"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
