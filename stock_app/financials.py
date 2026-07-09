"""네이버 금융에서 재무 실적(매출/영업이익/ROE/PER/PBR 등) 스크래핑."""
import io

import pandas as pd
import requests
import streamlit as st

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/item/main.naver"}


def _find_financial_table(tables):
    for t in tables:
        cols = t.columns
        first_col = cols[0]
        label = first_col[0] if isinstance(first_col, tuple) else first_col
        if isinstance(label, str) and "주요재무정보" in label:
            return t
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_financial_summary(code: str):
    """연간/분기 주요 재무정보를 (annual_df, quarterly_df) 튜플로 반환.

    네이버 페이지 테이블은 '최근 연간 실적'과 '최근 분기 실적' 두 그룹의 컬럼이
    같은 표에 이어져 있고 기간 라벨(예: 2025.12)이 겹칠 수 있어, 그룹 라벨(레벨0)
    기준으로 분리해야 연간 YoY / 분기 QoQ 성장률을 혼동 없이 계산할 수 있다.
    """
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.encoding = resp.apparent_encoding
    tables = pd.read_html(io.StringIO(resp.text))

    table = _find_financial_table(tables)
    if table is None:
        return pd.DataFrame(), pd.DataFrame()

    table = table.copy()
    index_col = table.columns[0]
    labels = table[index_col]
    labels = labels.iloc[:, 0] if isinstance(labels, pd.DataFrame) else labels

    def split(group_keyword):
        cols = [c for c in table.columns if isinstance(c, tuple) and group_keyword in str(c[0])]
        if not cols:
            return pd.DataFrame()
        sub = table[cols].copy()
        sub.columns = [c[1] for c in cols]
        sub.index = labels
        sub.index.name = "지표"
        sub = sub[~sub.index.duplicated(keep="first")]
        # 배당 미지급 분기의 "-" 등 텍스트 placeholder가 섞이면 해당 컬럼 전체가
        # object(문자열) dtype이 되어 숫자 계산이 깨지므로 전부 숫자로 강제 변환한다.
        sub = sub.apply(pd.to_numeric, errors="coerce")
        return sub

    annual = split("연간")
    quarterly = split("분기")
    return annual, quarterly


def latest_non_null(row: pd.Series):
    """가장 최근(오른쪽) 컬럼부터 값이 있는 첫 항목을 반환."""
    for col in reversed(row.index):
        val = row[col]
        if pd.notna(val):
            return col, val
    return None, None


WANTED_METRICS = {
    "매출액": "revenue",
    "영업이익": "operating_profit",
    "영업이익률": "operating_margin",
    "순이익률": "net_margin",
    "ROE(지배주주)": "roe",
    "부채비율": "debt_ratio",
    "EPS(원)": "eps",
    "PER(배)": "per",
    "BPS(원)": "bps",
    "PBR(배)": "pbr",
    "주당배당금(원)": "dps",
}


def extract_key_metrics(annual: pd.DataFrame, quarterly: pd.DataFrame) -> dict:
    """밸류에이션은 최신 분기, 성장성(YoY)은 연간 실적 기준으로 핵심 지표를 추출."""
    metrics = {}

    # 밸류에이션/수익성 지표는 가장 최근 값(분기 우선, 없으면 연간)을 사용
    for kor, eng in WANTED_METRICS.items():
        value, period = None, None
        if not quarterly.empty and kor in quarterly.index:
            period, value = latest_non_null(quarterly.loc[kor])
        if value is None and not annual.empty and kor in annual.index:
            period, value = latest_non_null(annual.loc[kor])
        metrics[eng] = value
        metrics[f"{eng}_period"] = period

    # 매출/영업이익 성장률(YoY, 연간 컬럼 기준 최근 두 회계연도 비교)
    for base, key in (("매출액", "revenue_growth"), ("영업이익", "operating_profit_growth")):
        if not annual.empty and base in annual.index:
            row = annual.loc[base].dropna()
            if len(row) >= 2:
                prev, curr = row.iloc[-2], row.iloc[-1]
                if prev not in (0, None):
                    metrics[key] = (curr - prev) / abs(prev) * 100

    return metrics
