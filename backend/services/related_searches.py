import httpx
import logging
from bs4 import BeautifulSoup
from backend.utils.rate_limiter import serp_limiter
from backend.utils.text_processing import clean_keyword

logger = logging.getLogger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_related_searches(query: str) -> dict:
    """Scrape Google SERP for related searches and People Also Ask."""
    await serp_limiter.acquire()
    result = {"related": [], "people_also_ask": []}

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                GOOGLE_SEARCH_URL,
                params={"q": query, "hl": "en", "num": 10},
                headers=HEADERS,
            )
            if resp.status_code != 200:
                logger.warning(f"SERP fetch failed for '{query}': HTTP {resp.status_code}")
                return result

            soup = BeautifulSoup(resp.text, "lxml")

            # Related searches (bottom of SERP)
            for a_tag in soup.select("div#botstuff a"):
                text = a_tag.get_text(strip=True)
                cleaned = clean_keyword(text)
                if cleaned and len(cleaned) > 2:
                    result["related"].append(cleaned)

            # People Also Ask
            for div in soup.select("div.related-question-pair, div[data-sgrd]"):
                text = div.get_text(strip=True)
                cleaned = clean_keyword(text)
                if cleaned and len(cleaned) > 5:
                    result["people_also_ask"].append(cleaned)

            # Fallback: look for "People also search for"
            if not result["related"]:
                for span in soup.find_all("span"):
                    parent = span.find_parent("a")
                    if parent and parent.get("href", "").startswith("/search"):
                        text = span.get_text(strip=True)
                        cleaned = clean_keyword(text)
                        if cleaned and len(cleaned) > 2:
                            result["related"].append(cleaned)

    except Exception as e:
        logger.warning(f"SERP scrape failed for '{query}': {e}")

    # Deduplicate
    result["related"] = list(dict.fromkeys(result["related"]))[:20]
    result["people_also_ask"] = list(dict.fromkeys(result["people_also_ask"]))[:10]
    return result
