from __future__ import annotations

import duckdb
import pandas as pd
import streamlit as st
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent  # Similarity/

_CHANNEL_RENAME = {
    "일": "date", "채널": "channel", "채널분류": "channel_type",
    "캠페인": "campaign", "캠페인목적": "campaign_goal",
    "그룹": "adgroup", "소재": "creative",
    "노출": "ch_impressions", "클릭": "ch_clicks", "비용": "ch_cost",
    "회원가입": "ch_signups", "구매": "ch_purchases", "구매매출": "ch_revenue",
}

_AF_RENAME = {
    "일": "date", "미디어소스": "media_source",
    "캠페인": "campaign", "그룹": "adgroup", "소재": "creative",
    "클릭": "af_clicks", "회원가입": "af_signups",
    "구매": "af_purchases", "구매매출": "af_revenue",
}

_CHANNEL_MAP = {
    "구글": "googleadwords_int",
    "메타": "Facebook Ads",
    "네이버": "naver_search",
}

_JOIN_KEYS = ["date", "media_source", "campaign", "adgroup", "creative"]


def _read_dir(path: Path, rename: dict[str, str]) -> pd.DataFrame:
    # rglob으로 월별 하위 폴더 구조도 자동 지원 (raw/channel/2025-04/*.csv)
    files = sorted(path.rglob("*.csv"))
    if not files:
        return pd.DataFrame(columns=list(rename.values()))
    dfs = [pd.read_csv(f, encoding="utf-8-sig") for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df.columns = [c.lstrip("﻿") for c in df.columns]
    return df.rename(columns=rename)


@st.cache_data(ttl=300, show_spinner="데이터 로딩 중...")
def load_joined() -> pd.DataFrame:
    ch = _read_dir(ROOT / "data/raw/channel", _CHANNEL_RENAME)
    af = _read_dir(ROOT / "data/raw/appsflyer", _AF_RENAME)

    ch["date"] = pd.to_datetime(ch["date"])
    ch["media_source"] = ch["channel"].map(_CHANNEL_MAP)
    af["date"] = pd.to_datetime(af["date"])

    df = ch.merge(af, on=_JOIN_KEYS, how="left")

    for col in ["af_clicks", "af_signups", "af_purchases", "af_revenue"]:
        df[col] = df[col].fillna(0)

    _add_derived(df)
    df["creative_type"] = df["creative"].str.split("_").str[0]
    return df


def _add_derived(df: pd.DataFrame) -> None:
    cost = df["ch_cost"].replace(0, None)
    df["roas_platform"] = (df["ch_revenue"] / cost).round(2)
    df["roas_af"]       = (df["af_revenue"] / cost).round(2)
    df["ctr"]           = (df["ch_clicks"] / df["ch_impressions"].replace(0, None) * 100).round(2)
    df["cpr"]           = (cost / df["af_signups"].replace(0, None)).round(0)
    df["cpa"]           = (cost / df["af_purchases"].replace(0, None)).round(0)
    df["signup_gap_pct"]   = (df["af_signups"]   / df["ch_signups"].replace(0, None)   * 100).round(1)
    df["purchase_gap_pct"] = (df["af_purchases"] / df["ch_purchases"].replace(0, None) * 100).round(1)
    df["revenue_gap_pct"]  = (df["af_revenue"]   / df["ch_revenue"].replace(0, None)   * 100).round(1)


def filter_date(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    return df[mask]


@st.cache_data(ttl=300, show_spinner="Braze 로딩 중...")
def load_braze_campaigns() -> pd.DataFrame:
    files = sorted((ROOT / "data/raw/braze/campaigns").glob("*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in files], ignore_index=True)
    df.columns = [c.lstrip("﻿") for c in df.columns]
    df["sent_at"] = pd.to_datetime(df["sent_at"])
    return df


@st.cache_data(ttl=300)
def load_braze_users() -> pd.DataFrame:
    files = sorted((ROOT / "data/raw/braze").glob("users_*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.read_csv(files[-1], encoding="utf-8-sig")
    df.columns = [c.lstrip("﻿") for c in df.columns]
    return df


@st.cache_data(ttl=300)
def load_braze_purchases() -> pd.DataFrame:
    files = sorted((ROOT / "data/raw/braze").glob("purchases_*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in files], ignore_index=True)
    df.columns = [c.lstrip("﻿") for c in df.columns]
    df["purchase_at"] = pd.to_datetime(df["purchase_at"])
    return df


def query(sql: str, df: pd.DataFrame, name: str = "df") -> pd.DataFrame:
    """DuckDB로 pandas DataFrame에 SQL 쿼리 실행."""
    con = duckdb.connect()
    con.register(name, df)
    return con.execute(sql).df()
