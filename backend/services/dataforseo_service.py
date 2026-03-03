"""
DataForSEO Keywords Data API integration.
Fetches real search volume, CPC, and competition data from Google Ads via DataForSEO.
"""
import json
import httpx
from typing import Optional
import os

DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN", "tianchu.zhuang@quvideo.com")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "539bbbcf76e92ca6")
BASE_URL = "https://api.dataforseo.com/v3"

# US English by default — covers the broadest dataset
DEFAULT_LOCATION = 2840   # United States
DEFAULT_LANGUAGE = "en"


async def get_search_volume(
    keywords: list[str],
    location_code: int = DEFAULT_LOCATION,
    language_code: str = DEFAULT_LANGUAGE,
) -> dict[str, dict]:
    """
    Query DataForSEO for search volume data for up to 1000 keywords at once.
    Returns a dict keyed by keyword with fields:
      search_volume, cpc, competition_index, monthly_searches
    Keywords not found in Google Ads data are returned with None values.
    """
    if not keywords:
        return {}

    # Deduplicate and lowercase
    keywords = list({kw.lower().strip() for kw in keywords})

    payload = [{
        "keywords": keywords,
        "location_code": location_code,
        "language_code": language_code,
    }]

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}/keywords_data/google_ads/search_volume/live",
            auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    results: dict[str, dict] = {}

    tasks = data.get("tasks", [])
    if not tasks or tasks[0].get("status_code") != 20000:
        return results

    for item in (tasks[0].get("result") or []):
        kw = item.get("keyword", "").lower().strip()
        results[kw] = {
            "search_volume": item.get("search_volume"),
            "cpc": item.get("cpc"),
            "competition_index": item.get("competition_index"),
            "monthly_searches": item.get("monthly_searches"),
        }

    return results


async def get_account_balance() -> Optional[float]:
    """Check remaining DataForSEO credit balance."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/appendix/user_data",
            auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
        )
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["tasks"][0]["result"][0]["money"]["balance"]
    except Exception:
        return None
