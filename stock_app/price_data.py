"""주가 시세 조회 및 변곡점(local peak/trough) 탐지."""
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd
import streamlit as st
from scipy.signal import argrelextrema


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(code: str, years: int = 2) -> pd.DataFrame:
    start = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
    df = fdr.DataReader(code, start)
    if df.empty:
        return df
    df = df.reset_index()
    return df


def find_inflection_points(df: pd.DataFrame, order: int = 10, top_n: int = 8):
    """Close 시계열에서 국소 최대/최소(변곡점)를 찾아 최근/변동폭이 큰 상위 top_n개를 반환.

    order: 좌우 몇 개 데이터포인트 안에서 극값인지 판단하는 창 크기.
    """
    if df.empty or len(df) < order * 2 + 1:
        return []

    close = df["Close"].to_numpy()
    max_idx = argrelextrema(close, lambda a, b: a >= b, order=order)[0]
    min_idx = argrelextrema(close, lambda a, b: a <= b, order=order)[0]

    points = []
    for idx in list(max_idx) + list(min_idx):
        kind = "고점" if idx in max_idx else "저점"
        points.append(
            {
                "index": int(idx),
                "date": df.iloc[idx]["Date"],
                "price": float(df.iloc[idx]["Close"]),
                "kind": kind,
            }
        )

    if not points:
        return []

    points_df = pd.DataFrame(points).drop_duplicates(subset=["index"])
    # 인접 변곡점 대비 변동폭(중요도)을 계산해 상위 top_n개만 남긴다.
    points_df = points_df.sort_values("index").reset_index(drop=True)
    points_df["magnitude"] = points_df["price"].diff().abs().fillna(0) + points_df["price"].diff(-1).abs().fillna(0)
    points_df = points_df.sort_values("magnitude", ascending=False).head(top_n)
    points_df = points_df.sort_values("date")
    return points_df.to_dict("records")
