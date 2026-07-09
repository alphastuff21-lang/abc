import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from stock_app import financials, news, price_data, recommender, scoring, ticker, valuation

st.set_page_config(
    page_title="국내 주식 종목 분석/예측",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

REC_COLORS = {"매수": "#22c55e", "중립(관망)": "#f59e0b", "매도/비중축소": "#f43f5e"}
MONEY_ROWS = {"매출액", "영업이익", "당기순이익", "EPS(원)", "BPS(원)", "주당배당금(원)"}

st.markdown(
    """
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css');
    html, body, [class^="css"], [class*=" css"] {
        font-family: 'Pretendard Variable', Pretendard, -apple-system, 'Malgun Gothic', sans-serif;
    }

    /* 타이포그래피 계층: 제목(Title) > 부제목(Subtitle) > 상세 내용(Detail/Body) */
    .app-title, .section-title { font-family: 'Pretendard Variable', Pretendard, sans-serif; }
    .app-subtitle, .rec-caption, .score-bar-label,
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
        font-family: 'Pretendard Variable', Pretendard, sans-serif;
    }
    [data-testid="stCaptionContainer"] p {
        font-size: 0.85rem !important; font-weight: 400 !important;
        color: #9a9aab !important; line-height: 1.55 !important;
    }
    p, span, div, label { font-family: 'Pretendard Variable', Pretendard, -apple-system, 'Malgun Gothic', sans-serif; }

    .stApp {
        background:
            radial-gradient(circle at 15% 0%, rgba(168, 85, 247, 0.18) 0%, transparent 45%),
            radial-gradient(circle at 85% 10%, rgba(249, 115, 22, 0.10) 0%, transparent 40%),
            #0b0b12;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #05050a 0%, #0f0f18 100%);
        border-right: 1px solid rgba(168, 85, 247, 0.15);
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #e5e5ec !important; }

    section[data-testid="stSidebar"] button {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(255,255,255,0.03) !important;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] button:hover {
        border-color: rgba(168, 85, 247, 0.6) !important;
        background: rgba(168, 85, 247, 0.12) !important;
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(90deg, #a855f7, #ec4899) !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(168, 85, 247, 0.35);
    }

    /* 추천 종목 리스트의 종목명 버튼: 링크처럼 보이도록 스타일 */
    section[data-testid="stMain"] button {
        border-radius: 8px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: #c084fc !important;
        font-weight: 700 !important;
        justify-content: flex-start !important;
        padding-left: 0.3rem !important;
        transition: all 0.15s ease;
    }
    section[data-testid="stMain"] button:hover {
        background: rgba(168, 85, 247, 0.12) !important;
        color: #f472b6 !important;
        text-decoration: underline;
    }

    /* 제목(Title) */
    .app-title {
        font-size: 2.6rem; font-weight: 800; margin-bottom: 0.3rem; letter-spacing: -0.02em; line-height: 1.2;
        background: linear-gradient(90deg, #f4f4f6 0%, #f4f4f6 40%, #c084fc 70%, #f472b6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    /* 부제목(Subtitle) */
    .app-subtitle {
        color: #c7c7d6; font-size: 1.05rem; font-weight: 500; line-height: 1.6; margin-bottom: 1.4rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border-radius: 18px; padding: 1.1rem 1.3rem 0.9rem 1.3rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(168, 85, 247, 0.18);
    }
    div[data-testid="stMetricLabel"] { color: #a1a1b5 !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] { color: #f8f8fb !important; font-weight: 800 !important; }

    /* 섹션 부제목(Subtitle 역할) */
    .section-title {
        font-size: 1.3rem; font-weight: 700; color: #f8f8fb;
        border-left: 5px solid #a855f7; padding-left: 0.65rem; margin: 2rem 0 0.9rem 0;
    }

    .rec-badge {
        display: inline-block; padding: 0.4rem 1.1rem; border-radius: 999px;
        font-weight: 700; font-size: 1.05rem; color: #0b0b12; box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }
    /* 상세 내용(Detail/Body) */
    .rec-caption { color: #9a9aab; font-size: 0.85rem; font-weight: 400; line-height: 1.55; margin-top: 0.5rem; }

    .score-bar-wrap { margin-bottom: 0.7rem; }
    .score-bar-label { font-size: 0.86rem; font-weight: 700; color: #d4d4e0; margin-bottom: 3px; }
    .score-bar-track { background: rgba(255,255,255,0.08); border-radius: 8px; height: 14px; overflow: hidden; }
    .score-bar-fill { height: 100%; border-radius: 8px; }

    [data-testid="stDataFrame"] {
        border-radius: 14px; overflow: hidden;
        border: 1px solid rgba(168, 85, 247, 0.15);
        box-shadow: 0 4px 18px rgba(0,0,0,0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_money(value, unit="원"):
    if value is None or pd.isna(value):
        return "-"
    return f"{value:,.0f}{unit}"


def fmt_multiple(value, unit="배"):
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.2f}{unit}"


def bar_color(value):
    if value >= 70:
        return "#22c55e"
    if value >= 40:
        return "#f59e0b"
    return "#f43f5e"


def score_bar_html(label, value):
    pct = max(0.0, min(100.0, value))
    return (
        f'<div class="score-bar-wrap"><div class="score-bar-label">{label} · {value:.1f}점</div>'
        f'<div class="score-bar-track"><div class="score-bar-fill" '
        f'style="width:{pct}%; background:{bar_color(value)};"></div></div></div>'
    )


def format_financial_table(df: pd.DataFrame) -> pd.DataFrame:
    """실적 테이블을 화면 표시용으로 포맷: 금액은 천단위 콤마+정수, 비율/배수는 소수 1자리."""
    if df.empty:
        return df
    disp = df.astype(object)
    for idx in df.index:
        if idx in MONEY_ROWS:
            disp.loc[idx] = df.loc[idx].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "-")
        else:
            disp.loc[idx] = df.loc[idx].map(lambda v: f"{v:,.1f}" if pd.notna(v) else "-")
    return disp


def render_recommendation_section():
    st.markdown('<div class="section-title">🔥 추천 종목 TOP 10</div>', unsafe_allow_html=True)
    st.caption(
        "시가총액 TOP 30 종목을 대상으로 실적 점수(65%)와 뉴스/호재 점수(35%)를 종합한 순위입니다. "
        "저평가 매력 점수는 현재 PER·PBR이 자사의 역사적 평균 배수보다 낮을수록(저평가) 높게 산정됩니다. "
        "결과는 1시간 동안 캐시되어 재사용됩니다."
    )
    with st.spinner("추천 종목 스캔 중... (최초 1회는 다소 시간이 걸릴 수 있습니다)"):
        recs = recommender.build_recommendations(pool_size=30, top_n=10)

    if not recs:
        st.warning("추천 종목을 계산하지 못했습니다.")
        return

    st.caption("👉 종목명을 클릭하면 해당 종목의 상세 분석으로 이동합니다.")

    col_spec = [0.6, 2.2, 1.3, 1, 1.1, 1, 1, 1.1, 1.3, 1, 2]
    headers = [
        "순위", "종목명", "현재가", "실적점수", "저평가점수",
        "뉴스점수", "종합점수", "투자판단", "목표주가", "상승여력", "주요 호재 키워드",
    ]
    header_cols = st.columns(col_spec)
    for c, h in zip(header_cols, headers):
        c.markdown(f"<span style='color:#9a9aab;font-size:0.8rem;font-weight:700;'>{h}</span>", unsafe_allow_html=True)

    for i, r in enumerate(recs, start=1):
        cols = st.columns(col_spec)
        cols[0].write(i)
        if cols[1].button(f"{r['name']} ({r['code']})", key=f"rec_pick_{r['code']}", width="stretch"):
            st.session_state["pending_query"] = r["code"]
            st.rerun()
        cols[2].write(fmt_money(r["current_price"]))
        cols[3].write(f"{r['financial_score']:.1f}")
        cols[4].write(f"{r['valuation_score']:.1f}")
        cols[5].write(f"{r['news_score']:.1f}")
        cols[6].markdown(f"**{r['total_score']:.1f}**")
        cols[7].markdown(
            f"<span style='color:{REC_COLORS.get(r['recommendation'], '#d4d4e0')};font-weight:700;'>"
            f"{r['recommendation']}</span>",
            unsafe_allow_html=True,
        )
        cols[8].write(fmt_money(r["target_price"]) if r.get("target_price") else "-")
        cols[9].write(f"{r['upside_pct']:+.1f}%" if r.get("upside_pct") is not None else "-")
        cols[10].write(r["top_keyword"] or "-")


st.markdown('<div class="app-title">📈 국내 주식 종목별 분석 및 예측</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">실적(재무 데이터)을 최우선으로, 최근 뉴스의 호재/악재를 정량 점수화하여 '
    "매수 여부와 목표주가를 제시합니다. 투자 참고용이며 투자 판단의 책임은 본인에게 있습니다.</div>",
    unsafe_allow_html=True,
)

# TOP30 종목 클릭 시 위젯이 이미 생성되기 전(스크립트 최상단)에 값을 반영해야
# "widget already instantiated" 오류 없이 종목 입력창을 갱신할 수 있다.
if "pending_query" in st.session_state:
    st.session_state["query_input"] = st.session_state.pop("pending_query")
    st.session_state["run_flag"] = True
if "query_input" not in st.session_state:
    st.session_state["query_input"] = "삼성전자"

with st.sidebar:
    st.header("🔍 종목 입력")
    query = st.text_input("종목명 또는 종목코드", key="query_input")
    years = st.slider("주가 조회 기간(년)", 1, 5, 2)
    news_pages = st.slider("뉴스 조회 페이지 수(페이지당 최대 20건)", 1, 10, 5)
    if st.button("분석 시작", type="primary", width='stretch'):
        st.session_state["run_flag"] = True

    st.markdown("---")
    st.markdown("**🏆 시가총액 TOP 30**")
    with st.spinner("시가총액 순위 불러오는 중..."):
        top30 = ticker.top_by_marketcap(30)
    for i, row in enumerate(top30, start=1):
        marcap_trillion = row["Marcap"] / 1e12
        label = f"{i}. {row['Name']} · {marcap_trillion:,.0f}조"
        if st.button(label, key=f"top30_{row['Code']}", width='stretch'):
            st.session_state["pending_query"] = row["Code"]
            st.rerun()

run = st.session_state.get("run_flag", False)

if not run:
    st.info("좌측에서 종목명(예: 삼성전자, SK하이닉스)이나 종목코드를 입력하고 [분석 시작]을 눌러주세요.")
    render_recommendation_section()
    st.stop()

with st.spinner("종목 코드 확인 중..."):
    stock = ticker.resolve_code(query)

if not stock:
    st.error(f"'{query}'에 해당하는 종목을 찾을 수 없습니다.")
    st.stop()

code, name, market = stock["Code"], stock["Name"], stock["Market"]
st.subheader(f"{name} ({code}) · {market}")

with st.spinner("주가 데이터 수집 중..."):
    price_df = price_data.get_price_history(code, years=years)

if price_df.empty:
    st.error("주가 데이터를 가져오지 못했습니다.")
    st.stop()

current_price = float(price_df.iloc[-1]["Close"])
prev_close = float(price_df.iloc[-2]["Close"]) if len(price_df) > 1 else current_price
day_change_pct = (current_price - prev_close) / prev_close * 100 if prev_close else 0.0

with st.spinner("재무 실적 데이터 수집 중..."):
    annual, quarterly = financials.get_financial_summary(code)
    metrics = financials.extract_key_metrics(annual, quarterly)

with st.spinner("뉴스 및 호재/악재 분석 중..."):
    news_df = news.get_recent_news(code, pages=news_pages)
    news_result = news.score_news(news_df)

# 밸류에이션 비교 기준(역사적 평균 PER/PBR)을 먼저 구한 뒤 실적 점수에 반영
val = valuation.estimate_target_price(annual, current_price, score=50)
fin_result = scoring.compute_financial_score(
    metrics, avg_per=val.get("avg_per"), avg_pbr=val.get("avg_pbr")
)
total_score = scoring.compute_total_score(fin_result["financial_score"], news_result["news_score"])
rec = scoring.recommendation(total_score)
val = valuation.estimate_target_price(annual, current_price, score=total_score)

# ---------------------------------------------------------------- 핵심 요약
c1, c2, c3, c4 = st.columns(4)
c1.metric("현재가", fmt_money(current_price), f"{day_change_pct:+.2f}%")
c2.metric("종합 점수 (100점)", f"{total_score:.1f}점")
with c3:
    st.markdown(
        '<div style="font-size:0.875rem;color:#64748b;font-weight:600;margin-bottom:0.35rem;">투자 판단</div>'
        f'<span class="rec-badge" style="background:{REC_COLORS.get(rec["label"], "#334155")};">{rec["label"]}</span>',
        unsafe_allow_html=True,
    )
if val.get("adjusted_target"):
    c4.metric(
        "목표주가",
        fmt_money(val["adjusted_target"]),
        f"{val['upside_pct']:+.1f}%" if val.get("upside_pct") is not None else None,
    )
else:
    c4.metric("목표주가", "산정 불가")

st.markdown(f'<div class="rec-caption">{rec["detail"]}</div>', unsafe_allow_html=True)

if val.get("upside_pct") is not None:
    if rec["label"] == "매수" and val["upside_pct"] < -10:
        st.warning(
            f"⚠️ 종합 점수는 매수 기준을 충족하지만, 밸류에이션 목표가는 현재가 대비 "
            f"{val['upside_pct']:.1f}%로 낮게 산정되었습니다. 최근 급등으로 이미 목표가에 근접했거나 "
            f"단기 과열일 수 있으니 목표가 산정 근거를 함께 확인하세요."
        )
    elif rec["label"].startswith("매도") and val["upside_pct"] > 10:
        st.info(
            f"ℹ️ 종합 점수는 낮지만, 밸류에이션 목표가는 현재가 대비 {val['upside_pct']:.1f}% 높게 "
            f"산정되었습니다. 저평가 구간일 수 있으니 함께 참고하세요."
        )

# ---------------------------------------------------------------- 점수 세부
st.markdown('<div class="section-title">📊 점수 구성</div>', unsafe_allow_html=True)
col_score, col_val = st.columns([3, 2])

with col_score:
    st.write(
        f"**실적 점수 {fin_result['financial_score']:.1f} / 100** (가중 65%) · "
        f"**뉴스/호재 점수 {news_result['news_score']:.1f} / 100** (가중 35%)"
    )
    breakdown_labels = {
        "revenue_growth": "매출 성장률(YoY)",
        "operating_profit_growth": "영업이익 성장률(YoY)",
        "operating_margin": "영업이익률",
        "roe": "ROE",
        "debt_ratio": "부채비율(낮을수록 유리)",
        "per_valuation": "PER 저평가 매력",
        "pbr_valuation": "PBR 저평가 매력",
    }
    bars_html = "".join(
        score_bar_html(breakdown_labels.get(k, k), v) for k, v in fin_result["breakdown"].items()
    )
    st.markdown(bars_html, unsafe_allow_html=True)

with col_val:
    st.markdown("**🎯 목표주가 산정 근거**")
    rows = [
        ("PER법 목표가", fmt_money(val.get("per_target"))),
        ("PBR법 목표가", fmt_money(val.get("pbr_target"))),
        ("역사적 평균 PER", fmt_multiple(val.get("avg_per"))),
        ("역사적 평균 PBR", fmt_multiple(val.get("avg_pbr"))),
        ("기본(가중평균) 목표가", fmt_money(val.get("base_target"))),
        ("점수 반영 최종 목표가", fmt_money(val.get("adjusted_target"))),
    ]
    st.dataframe(
        pd.DataFrame(rows, columns=["항목", "값"]).set_index("항목"),
        width='stretch',
    )

# ---------------------------------------------------------------- 재무 지표
st.markdown('<div class="section-title">💰 실적/재무 지표 (연간)</div>', unsafe_allow_html=True)
if not annual.empty:
    st.dataframe(format_financial_table(annual), width='stretch')
    st.caption("※ 매출액/영업이익/당기순이익 단위: 억원. EPS·BPS·주당배당금 단위: 원.")
else:
    st.warning("재무 데이터를 가져오지 못했습니다.")

with st.expander("최근 분기 실적 보기"):
    if not quarterly.empty:
        st.dataframe(format_financial_table(quarterly), width='stretch')
    else:
        st.write("분기 데이터 없음")

# ---------------------------------------------------------------- 주가 차트 + 변곡점
st.markdown('<div class="section-title">📉 주가 흐름 및 변곡점 이벤트</div>', unsafe_allow_html=True)

inflection_points = price_data.find_inflection_points(price_df, order=max(5, len(price_df) // 40))

news_tagged = news_result["tagged"]


def _nearest_event(date, window_days=5):
    if news_tagged.empty:
        return None
    diffs = (news_tagged["date"] - date).abs()
    within = news_tagged[diffs.dt.total_seconds() <= window_days * 86400]
    if within.empty:
        return None
    best = within.loc[diffs[within.index].idxmin()]
    return best

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=price_df["Date"],
        y=price_df["Close"],
        mode="lines",
        name="종가",
        line=dict(color="#c084fc", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(168, 85, 247, 0.12)",
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f}원<extra></extra>",
    )
)

annotations = []
for pt in inflection_points:
    event = _nearest_event(pt["date"])
    hover = f"{pt['kind']} {pt['price']:,.0f}원"
    if event is not None:
        hover += f"<br>{event['title']}"
    fig.add_trace(
        go.Scatter(
            x=[pt["date"]],
            y=[pt["price"]],
            mode="markers",
            marker=dict(
                size=12,
                color="#f43f5e" if pt["kind"] == "고점" else "#22c55e",
                line=dict(width=1.5, color="#0b0b12"),
            ),
            name=pt["kind"],
            showlegend=False,
            hovertext=hover,
            hoverinfo="text",
        )
    )
    if event is not None:
        annotations.append(
            dict(
                x=pt["date"],
                y=pt["price"],
                text=event["title"][:20] + "…",
                showarrow=True,
                arrowhead=1,
                arrowcolor="#71717a",
                font=dict(size=10, color="#e5e5ec"),
            )
        )

fig.update_layout(
    annotations=annotations,
    height=550,
    hovermode="closest",
    xaxis_title="날짜",
    yaxis_title="종가(원)",
    plot_bgcolor="#0f0f18",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Malgun Gothic, sans-serif", color="#d4d4e0"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickformat=",.0f"),
    margin=dict(t=30, l=10, r=10, b=10),
)
st.plotly_chart(fig, width='stretch')

st.markdown("**변곡점 상세**")
if inflection_points:
    detail_rows = []
    for pt in inflection_points:
        event = _nearest_event(pt["date"])
        detail_rows.append(
            {
                "날짜": pt["date"].strftime("%Y-%m-%d"),
                "구분": pt["kind"],
                "종가": fmt_money(pt["price"]),
                "관련 이벤트(뉴스)": event["title"] if event is not None else "관련 뉴스 없음(조회 기간 외 가능)",
            }
        )
    st.dataframe(pd.DataFrame(detail_rows), width='stretch')
else:
    st.write("변곡점을 찾지 못했습니다.")

st.caption("※ 이벤트 매칭은 최근 수집된 뉴스(조회 페이지 수 기준)에 한정되며, 과거 변곡점은 관련 뉴스가 없을 수 있습니다.")

# ---------------------------------------------------------------- 뉴스 목록
st.markdown('<div class="section-title">📰 최근 뉴스 및 호재/악재 키워드</div>', unsafe_allow_html=True)
st.write(
    f"긍정 신호 {news_result['positive_count']}건 · 부정 신호 {news_result['negative_count']}건 "
    f"(원점수 합계 {news_result['raw_score']:+d})"
)
if not news_tagged.empty:
    show_df = news_tagged.copy()
    show_df["date"] = show_df["date"].dt.strftime("%Y-%m-%d %H:%M")
    show_df = show_df.rename(
        columns={"title": "제목", "source": "언론사", "date": "날짜", "score": "점수", "keywords": "매칭 키워드"}
    )
    st.dataframe(show_df, width='stretch', height=400)
else:
    st.write("수집된 뉴스가 없습니다.")

render_recommendation_section()
