from __future__ import annotations

from datetime import date
import streamlit as st

_MIN = date(2025, 1, 1)
_MAX = date(2025, 3, 31)
_ALL_CHANNELS = ["구글", "메타", "네이버"]


def render_sidebar() -> tuple[date, date, list[str]]:
    with st.sidebar:
        st.markdown("## 🔍 필터")
        date_range = st.date_input(
            "기간",
            value=(_MIN, _MAX),
            min_value=_MIN,
            max_value=_MAX,
        )
        channels = st.multiselect(
            "채널",
            options=_ALL_CHANNELS,
            default=_ALL_CHANNELS,
        )
        st.divider()
        st.caption("📅 데이터: 2025 Q1")

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = _MIN, _MAX

    return start, end, channels or _ALL_CHANNELS
