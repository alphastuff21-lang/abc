"""시가총액 상위 종목 풀을 정량 점수로 스캔해 추천 종목 리스트를 만든다."""
import streamlit as st

from . import financials, news, price_data, scoring, ticker, valuation


def _top_positive_keyword(tagged):
    if tagged.empty:
        return None
    positive = tagged[tagged["score"] > 0].sort_values("score", ascending=False)
    if positive.empty:
        return None
    return positive.iloc[0]["keywords"]


def _score_one(code: str, name: str):
    price_df = price_data.get_price_history(code, years=1)
    if price_df.empty:
        return None
    current_price = float(price_df.iloc[-1]["Close"])

    annual, quarterly = financials.get_financial_summary(code)
    metrics = financials.extract_key_metrics(annual, quarterly)

    news_df = news.get_recent_news(code, pages=1)
    news_result = news.score_news(news_df)

    val = valuation.estimate_target_price(annual, current_price, score=50)
    fin_result = scoring.compute_financial_score(
        metrics, avg_per=val.get("avg_per"), avg_pbr=val.get("avg_pbr")
    )
    total_score = scoring.compute_total_score(fin_result["financial_score"], news_result["news_score"])
    rec = scoring.recommendation(total_score)
    val = valuation.estimate_target_price(annual, current_price, score=total_score)

    breakdown = fin_result["breakdown"]
    valuation_score = (breakdown.get("per_valuation", 50.0) + breakdown.get("pbr_valuation", 50.0)) / 2

    return {
        "code": code,
        "name": name,
        "current_price": current_price,
        "financial_score": fin_result["financial_score"],
        "valuation_score": valuation_score,
        "news_score": news_result["news_score"],
        "total_score": total_score,
        "recommendation": rec["label"],
        "target_price": val.get("adjusted_target"),
        "upside_pct": val.get("upside_pct"),
        "top_keyword": _top_positive_keyword(news_result["tagged"]),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def build_recommendations(pool_size: int = 30, top_n: int = 10):
    """시가총액 상위 pool_size개 종목을 스캔해 종합 점수 상위 top_n개를 반환."""
    try:
        pool = ticker.top_by_marketcap(pool_size)
    except Exception:
        return []
    results = []
    for row in pool:
        try:
            scored = _score_one(row["Code"], row["Name"])
        except Exception:
            scored = None
        if scored is not None:
            results.append(scored)

    results.sort(key=lambda r: r["total_score"], reverse=True)
    return results[:top_n]
