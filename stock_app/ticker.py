"""종목명 <-> 종목코드 변환."""
import FinanceDataReader as fdr
import streamlit as st


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _load_listing():
    krx = fdr.StockListing("KRX")
    return krx[["Code", "Name", "Market", "Marcap"]].dropna(subset=["Name"])


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def top_by_marketcap(n: int = 30):
    """시가총액 기준 상위 n개 종목을 반환한다."""
    listing = _load_listing()
    top = listing.dropna(subset=["Marcap"]).sort_values("Marcap", ascending=False).head(n)
    return top.to_dict("records")


def find_candidates(query: str, limit: int = 8):
    """입력한 문자열을 포함하는 종목명 후보 목록을 반환한다."""
    query = query.strip()
    if not query:
        return []
    listing = _load_listing()

    exact = listing[listing["Name"] == query]
    if not exact.empty:
        return exact.head(limit).to_dict("records")

    contains = listing[listing["Name"].str.contains(query, case=False, na=False)]
    return contains.head(limit).to_dict("records")


def resolve_code(query: str):
    """입력이 종목코드(6자리 숫자)면 그대로, 아니면 이름으로 매칭되는 첫 후보를 반환."""
    query = query.strip()
    if query.isdigit() and len(query) == 6:
        listing = _load_listing()
        row = listing[listing["Code"] == query]
        if not row.empty:
            r = row.iloc[0]
            return {"Code": r["Code"], "Name": r["Name"], "Market": r["Market"]}
        return {"Code": query, "Name": query, "Market": "UNKNOWN"}

    candidates = find_candidates(query, limit=1)
    return candidates[0] if candidates else None
