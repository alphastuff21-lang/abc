"""EPS/PER, BPS/PBR 기반 목표주가 산정."""
import pandas as pd


def _historical_avg(annual: pd.DataFrame, row_name: str):
    """추정치((E)) 컬럼을 제외한 실제 결산 연도들의 평균값.

    PER/PBR처럼 배수(multiple)인 지표는 적자 연도의 음수 배수가 섞이면
    평균이 무의미하게 왜곡되므로 0 이하 값은 제외한다.
    """
    if annual.empty or row_name not in annual.index:
        return None
    row = annual.loc[row_name]
    actual_cols = [c for c in row.index if "(E)" not in str(c)]
    vals = row[actual_cols].dropna()
    if "배" in row_name:  # PER(배), PBR(배) 등 배수 지표
        vals = vals[vals > 0]
    if vals.empty:
        return None
    return float(vals.mean())


def _forward_value(annual: pd.DataFrame, row_name: str):
    """가장 최근(추정 포함) 컬럼 값 = 향후 실적 전망에 쓰는 forward 값."""
    if annual.empty or row_name not in annual.index:
        return None
    row = annual.loc[row_name].dropna()
    return float(row.iloc[-1]) if not row.empty else None


def estimate_target_price(annual: pd.DataFrame, current_price: float, score: float):
    """PER/PBR 밴드 기반 목표주가와 근거를 반환.

    - PER법: forward EPS * 최근 실제결산 평균 PER
    - PBR법: forward BPS * 최근 실제결산 평균 PBR
    - 두 방법을 6:4로 가중 평균해 기본 목표가를 구하고, 종합 점수(score, 0~100)를
      50점을 중립으로 하여 ±10% 범위에서 가감해 최종 목표가를 산출한다.
    """
    forward_eps = _forward_value(annual, "EPS(원)")
    forward_bps = _forward_value(annual, "BPS(원)")
    avg_per = _historical_avg(annual, "PER(배)")
    avg_pbr = _historical_avg(annual, "PBR(배)")

    per_target = forward_eps * avg_per if forward_eps and avg_per else None
    pbr_target = forward_bps * avg_pbr if forward_bps and avg_pbr else None

    candidates = [(per_target, 0.6), (pbr_target, 0.4)]
    valid = [(v, w) for v, w in candidates if v is not None]

    if not valid:
        return {
            "base_target": None,
            "adjusted_target": None,
            "per_target": per_target,
            "pbr_target": pbr_target,
            "avg_per": avg_per,
            "avg_pbr": avg_pbr,
            "upside_pct": None,
        }

    weight_sum = sum(w for _, w in valid)
    base_target = sum(v * w for v, w in valid) / weight_sum

    # 점수 50을 중립으로, 최대 ±10% 가감 (score 100 -> +10%, score 0 -> -10%)
    adjustment = (score - 50) / 50 * 0.10
    adjusted_target = base_target * (1 + adjustment)

    upside_pct = None
    if current_price:
        upside_pct = (adjusted_target - current_price) / current_price * 100

    return {
        "base_target": base_target,
        "adjusted_target": adjusted_target,
        "per_target": per_target,
        "pbr_target": pbr_target,
        "avg_per": avg_per,
        "avg_pbr": avg_pbr,
        "forward_eps": forward_eps,
        "forward_bps": forward_bps,
        "upside_pct": upside_pct,
    }
