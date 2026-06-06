import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data.xlsx"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_PATH, sheet_name="Sheet1")
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["month_label"] = df["date"].dt.strftime("%m월")
    df["month_num"] = df["date"].dt.month

    num_cols = ["광고노출", "광고클릭", "광고비", "앱설치", "앱실행",
                "회원가입", "계좌개설", "첫거래", "반복사용", "자동이체설정", "추천완료"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).clip(lower=0)
    return df


@st.cache_data
def get_monthly(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["광고비", "광고노출", "광고클릭", "앱설치", "앱실행",
            "회원가입", "계좌개설", "첫거래", "반복사용", "자동이체설정", "추천완료"]
    m = df.groupby("year_month")[cols].sum().reset_index()
    _add_kpis(m)
    return m


@st.cache_data
def get_channel_monthly(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["광고비", "광고노출", "광고클릭", "앱설치", "앱실행",
            "회원가입", "계좌개설", "첫거래", "반복사용"]
    m = df.groupby(["year_month", "channel"])[cols].sum().reset_index()
    _add_kpis(m)
    return m


@st.cache_data
def get_creative_monthly(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["광고비", "광고노출", "광고클릭", "앱설치", "앱실행",
            "회원가입", "계좌개설", "첫거래", "반복사용"]
    m = df.groupby(["year_month", "creative_format"])[cols].sum().reset_index()
    _add_kpis(m)
    return m


@st.cache_data
def get_adgroup_monthly(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["광고비", "광고노출", "광고클릭", "앱설치", "앱실행",
            "회원가입", "계좌개설", "첫거래", "반복사용"]
    m = df.groupby(["year_month", "ad_group"])[cols].sum().reset_index()
    _add_kpis(m)
    return m


def _add_kpis(m: pd.DataFrame) -> None:
    safe = lambda a, b: np.where(b > 0, a / b, np.nan)
    m["CTR"]           = safe(m["광고클릭"],  m["광고노출"]) * 100
    m["CPC"]           = safe(m["광고비"],    m["광고클릭"])
    m["CPI"]           = safe(m["광고비"],    m["앱설치"])
    m["CPM"]           = safe(m["광고비"],    m["광고노출"]) * 1000
    m["CPA_회원가입"]  = safe(m["광고비"],    m["회원가입"])
    m["CPA_계좌개설"]  = safe(m["광고비"],    m["계좌개설"])
    m["CPA_반복사용"]  = safe(m["광고비"],    m["반복사용"])
    m["클릭_설치율"]   = safe(m["앱설치"],    m["광고클릭"]) * 100
    m["설치_실행율"]   = safe(m["앱실행"],    m["앱설치"])   * 100
    m["실행_가입율"]   = safe(m["회원가입"],  m["앱실행"])   * 100
    m["가입_계좌율"]   = safe(m["계좌개설"],  m["회원가입"]) * 100
    m["계좌_첫거래율"] = safe(m["첫거래"],    m["계좌개설"]) * 100
    m["첫거래_반복율"] = safe(m["반복사용"],  m["첫거래"])   * 100
