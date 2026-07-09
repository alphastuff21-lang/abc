"""실적(최우선) + 뉴스/호재를 종합한 정량 점수화 및 매수/매도 판정."""

# (지표키, 가중치, 스케일 저점, 스케일 고점, 저점이 유리한지 여부)
FINANCIAL_FACTORS = [
    ("revenue_growth", 15, -10, 20, False),
    ("operating_profit_growth", 15, -10, 30, False),
    ("operating_margin", 10, 0, 20, False),
    ("roe", 15, 0, 20, False),
    ("debt_ratio", 10, 50, 200, True),
]
# 밸류에이션(저평가일수록 매수 매력 높음)은 최근 지표를 역사적 평균과 비교해 별도 계산
VALUATION_WEIGHT_PER = 20
VALUATION_WEIGHT_PBR = 15

FINANCIAL_WEIGHT = 0.65
NEWS_WEIGHT = 0.35


def _scale(value, low, high, invert=False):
    if value is None:
        return 50.0  # 데이터 없으면 중립
    if high == low:
        return 50.0
    pct = (value - low) / (high - low)
    pct = max(0.0, min(1.0, pct))
    score = pct * 100
    return 100 - score if invert else score


def _valuation_score(current_multiple, avg_multiple):
    """현재 배수가 역사적 평균보다 낮을수록(저평가) 높은 점수."""
    if current_multiple is None or avg_multiple is None or avg_multiple == 0:
        return 50.0
    ratio = current_multiple / avg_multiple  # 1.0 = 평균과 동일
    # ratio 0.7 이하(30% 저평가) -> 100점, ratio 1.3 이상(30% 고평가) -> 0점
    pct = (1.3 - ratio) / (1.3 - 0.7)
    return max(0.0, min(1.0, pct)) * 100


def compute_financial_score(metrics: dict, avg_per: float, avg_pbr: float) -> dict:
    breakdown = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for key, weight, low, high, invert in FINANCIAL_FACTORS:
        s = _scale(metrics.get(key), low, high, invert)
        breakdown[key] = s
        weighted_sum += s * weight
        weight_total += weight

    per_score = _valuation_score(metrics.get("per"), avg_per)
    pbr_score = _valuation_score(metrics.get("pbr"), avg_pbr)
    breakdown["per_valuation"] = per_score
    breakdown["pbr_valuation"] = pbr_score
    weighted_sum += per_score * VALUATION_WEIGHT_PER + pbr_score * VALUATION_WEIGHT_PBR
    weight_total += VALUATION_WEIGHT_PER + VALUATION_WEIGHT_PBR

    financial_score = weighted_sum / weight_total if weight_total else 50.0
    return {"financial_score": financial_score, "breakdown": breakdown}


def compute_total_score(financial_score: float, news_score: float) -> float:
    return financial_score * FINANCIAL_WEIGHT + news_score * NEWS_WEIGHT


def recommendation(total_score: float) -> dict:
    if total_score >= 70:
        return {"label": "매수", "detail": "실적/밸류에이션/뉴스 종합 점수가 우수합니다."}
    if total_score >= 50:
        return {"label": "중립(관망)", "detail": "긍정 요인과 부정 요인이 혼재되어 있습니다."}
    return {"label": "매도/비중축소", "detail": "실적 또는 뉴스 흐름이 부진합니다."}
