"""네이버 금융 종목 뉴스 스크래핑 및 키워드 기반 호재/악재 점수화."""
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/item/main.naver"}

# 키워드: 가중치 (양수=호재, 음수=악재). 값이 클수록 영향이 크다.
POSITIVE_KEYWORDS = {
    "사상 최대": 3, "어닝서프라이즈": 3, "흑자전환": 3, "역대 최대": 3,
    "수주": 2, "계약 체결": 2, "공급 계약": 2, "대규모 수주": 3,
    "목표가 상향": 3, "목표주가 상향": 3, "실적 개선": 2, "실적 호조": 2,
    "신제품": 1, "신기술": 1, "특허": 1, "양산": 1,
    "수출 확대": 2, "수출 호조": 2, "매출 증가": 2, "영업이익 증가": 2,
    "배당 확대": 2, "자사주 매입": 2, "자사주 소각": 2,
    "MOU": 1, "협약": 1, "투자 유치": 2, "지분 인수": 1,
    "급등": 2, "강세": 1, "신고가": 2, "호실적": 2,
}

NEGATIVE_KEYWORDS = {
    "실적 부진": -2, "어닝쇼크": -3, "적자전환": -3, "역대 최저": -2,
    "목표가 하향": -3, "목표주가 하향": -3, "실적 악화": -2,
    "리콜": -2, "소송": -2, "제재": -2, "규제": -1, "관세": -1,
    "유상증자": -2, "횡령": -3, "배임": -3, "감사의견 거절": -3,
    "파업": -2, "적자": -1, "부도": -3, "상장폐지": -3,
    "급락": -2, "약세": -1, "신저가": -2, "어닝미스": -2,
    "매출 감소": -2, "영업이익 감소": -2, "구조조정": -1,
}

ALL_KEYWORDS = {**POSITIVE_KEYWORDS, **NEGATIVE_KEYWORDS}


@st.cache_data(ttl=1800, show_spinner=False)
def get_recent_news(code: str, pages: int = 3) -> pd.DataFrame:
    """최근 종목 뉴스 헤드라인(제목/언론사/날짜)을 최대 pages*20건 수집."""
    rows = []
    for page in range(1, pages + 1):
        url = (
            "https://finance.naver.com/item/news_news.naver"
            f"?code={code}&page={page}&sm=title_entity_id.basic&clusterId="
        )
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tr in soup.select("table.type5 tbody tr"):
            title_tag = tr.select_one("td.title a.tit")
            date_tag = tr.select_one("td.date")
            info_tag = tr.select_one("td.info")
            if not title_tag:
                continue
            rows.append(
                {
                    "title": title_tag.get_text(strip=True),
                    "source": info_tag.get_text(strip=True) if info_tag else "",
                    "date": date_tag.get_text(strip=True) if date_tag else "",
                }
            )
        if not rows:
            break

    if not rows:
        return pd.DataFrame(columns=["title", "source", "date"])

    df = pd.DataFrame(rows).drop_duplicates(subset=["title"])
    df["date"] = pd.to_datetime(df["date"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date", ascending=False).reset_index(drop=True)
    return df


def score_headline(title: str):
    """헤드라인 하나에 매칭된 키워드와 가중치 합계를 반환."""
    matched = []
    total = 0
    for kw, weight in ALL_KEYWORDS.items():
        if kw in title:
            matched.append((kw, weight))
            total += weight
    return total, matched


def score_news(news_df: pd.DataFrame):
    """뉴스 전체에 대해 호재/악재 점수를 집계.

    반환: dict(news_score 0~100, raw_score, positive_count, negative_count, tagged_df)
    """
    if news_df.empty:
        return {
            "news_score": 50.0,
            "raw_score": 0,
            "positive_count": 0,
            "negative_count": 0,
            "tagged": pd.DataFrame(columns=["title", "source", "date", "score", "keywords"]),
        }

    tagged_rows = []
    raw_total = 0
    pos_count = 0
    neg_count = 0
    for _, r in news_df.iterrows():
        s, matched = score_headline(r["title"])
        raw_total += s
        if s > 0:
            pos_count += 1
        elif s < 0:
            neg_count += 1
        tagged_rows.append(
            {
                "title": r["title"],
                "source": r["source"],
                "date": r["date"],
                "score": s,
                "keywords": ", ".join(f"{k}({v:+d})" for k, v in matched),
            }
        )

    tagged = pd.DataFrame(tagged_rows)

    # raw_total(대략 -30~+30 범위)을 0~100 스케일로 변환 (50=중립)
    news_score = 50 + raw_total * 2.5
    news_score = max(0, min(100, news_score))

    return {
        "news_score": news_score,
        "raw_score": raw_total,
        "positive_count": pos_count,
        "negative_count": neg_count,
        "tagged": tagged,
    }
