import math


def _safe_float(value) -> float | None:
    try:
        v = float(value)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def fmt_krw(value) -> str:
    v = _safe_float(value)
    if v is None:
        return "-"
    iv = int(v)
    if abs(iv) >= 100_000_000:
        return f"{iv / 100_000_000:.1f}억"
    if abs(iv) >= 10_000:
        return f"{iv / 10_000:.0f}만"
    return f"{iv:,}원"


def fmt_pct(value) -> str:
    v = _safe_float(value)
    return "-" if v is None else f"{v:.1f}%"


def fmt_roas(value) -> str:
    v = _safe_float(value)
    return "-" if v is None else f"{v:.2f}x"


def fmt_num(value) -> str:
    v = _safe_float(value)
    return "-" if v is None else f"{int(v):,}"


def gap_badge(pct) -> str:
    v = _safe_float(pct)
    if v is None or v == 0:
        return "⚫ -"
    if v >= 80:
        return f"🟢 {v:.0f}%"
    if v >= 60:
        return f"🟡 {v:.0f}%"
    return f"🔴 {v:.0f}%"
