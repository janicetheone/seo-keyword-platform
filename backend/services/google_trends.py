import logging
import asyncio
from functools import partial
from pytrends.request import TrendReq
from backend.utils.rate_limiter import trends_limiter

logger = logging.getLogger(__name__)


def _fetch_trends_sync(keywords: list[str], timeframe: str = "today 3-m", geo: str = "") -> dict:
    """Synchronous pytrends fetch (runs in executor)."""
    pytrends = TrendReq(hl="en-US", tz=360)
    # pytrends only handles up to 5 keywords at once
    batch = keywords[:5]
    result = {
        "interest_over_time": {},
        "related_queries": {},
        "rising": [],
    }
    try:
        pytrends.build_payload(batch, cat=0, timeframe=timeframe, geo=geo)
        iot = pytrends.interest_over_time()
        if not iot.empty:
            for kw in batch:
                if kw in iot.columns:
                    values = iot[kw].tolist()
                    result["interest_over_time"][kw] = values
                    # Average of last 4 data points as score
                    recent = values[-4:] if len(values) >= 4 else values
                    result["interest_over_time"][f"{kw}_score"] = sum(recent) / len(recent)

        related = pytrends.related_queries()
        for kw in batch:
            if kw in related:
                top = related[kw].get("top")
                rising = related[kw].get("rising")
                if top is not None and not top.empty:
                    result["related_queries"][kw] = top["query"].tolist()[:10]
                if rising is not None and not rising.empty:
                    for _, row in rising.head(10).iterrows():
                        result["rising"].append({
                            "keyword": row["query"],
                            "value": row["value"],
                            "parent": kw,
                        })
    except Exception as e:
        logger.warning(f"Google Trends error for {batch}: {e}")

    return result


async def fetch_trends(keywords: list[str], timeframe: str = "today 3-m", geo: str = "") -> dict:
    """Async wrapper for pytrends."""
    await trends_limiter.acquire()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_fetch_trends_sync, keywords, timeframe, geo))


async def fetch_trends_batched(keywords: list[str], timeframe: str = "today 3-m", geo: str = "") -> dict:
    """Fetch trends for more than 5 keywords by batching."""
    combined = {
        "interest_over_time": {},
        "related_queries": {},
        "rising": [],
    }
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i + 5]
        result = await fetch_trends(batch, timeframe, geo)
        combined["interest_over_time"].update(result["interest_over_time"])
        combined["related_queries"].update(result["related_queries"])
        combined["rising"].extend(result["rising"])
    return combined
