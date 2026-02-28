"""
Trending keyword discovery from multiple sources:
- Google Trends RSS feed (official, no API key needed)
- Reddit hot posts (public JSON API, no auth)
- Twitter trending via trends24.in (public aggregator)
"""

import asyncio
import logging
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


# ─── Google Trends RSS ───────────────────────────────────────────────────────
# Uses Google's official trending RSS feed — no API key, no pytrends quirks.

async def fetch_google_trending() -> list[dict]:
    """Fetch Google daily trending searches via the official RSS feed."""
    results = []
    try:
        async with httpx.AsyncClient(
            timeout=15,
            headers=BROWSER_HEADERS,
            follow_redirects=True,
        ) as client:
            resp = await client.get("https://trends.google.com/trending/rss?geo=US")
            if resp.status_code != 200:
                logger.warning(f"Google Trends RSS returned {resp.status_code}")
                return results

            root = ET.fromstring(resp.text)
            ns = {"ht": "https://trends.google.com/trending/rss"}
            items = root.findall(".//item")
            for i, item in enumerate(items[:30]):
                title_el = item.find("title")
                traffic_el = item.find("ht:approx_traffic", ns)
                news_el = item.find("ht:picture_source", ns)
                if title_el is not None and title_el.text:
                    detail = ""
                    if traffic_el is not None and traffic_el.text:
                        detail = f"{traffic_el.text} searches"
                    results.append({
                        "term": title_el.text.strip(),
                        "rank": i + 1,
                        "source": "google",
                        "detail": detail,
                    })
    except ET.ParseError as e:
        logger.warning(f"Google Trends RSS parse error: {e}")
    except Exception as e:
        logger.warning(f"Google Trends RSS failed: {e}")
    return results


# ─── Reddit ──────────────────────────────────────────────────────────────────

async def fetch_reddit_trending() -> list[dict]:
    """Fetch hot posts from Reddit popular (public JSON API, no auth needed)."""
    results = []
    try:
        async with httpx.AsyncClient(
            timeout=12,
            headers={"User-Agent": "SEOKeywordBot/1.0 (keyword research tool)"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                "https://www.reddit.com/r/popular/hot.json",
                params={"limit": 30, "raw_json": 1},
            )
            if resp.status_code == 200:
                posts = resp.json().get("data", {}).get("children", [])
                for i, post in enumerate(posts):
                    d = post.get("data", {})
                    title = d.get("title", "").strip()
                    subreddit = d.get("subreddit_name_prefixed", "")
                    score = d.get("score", 0)
                    if title:
                        results.append({
                            "term": title[:120],
                            "rank": i + 1,
                            "source": "reddit",
                            "detail": f"{subreddit} · {score:,} upvotes",
                        })
            else:
                logger.warning(f"Reddit returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Reddit trending failed: {e}")
    return results


# ─── Twitter (via trends24.in) ────────────────────────────────────────────────

async def fetch_twitter_trending() -> list[dict]:
    """Scrape Twitter trending topics from trends24.in (public aggregator)."""
    results = []
    try:
        async with httpx.AsyncClient(
            timeout=15,
            headers=BROWSER_HEADERS,
            follow_redirects=True,
        ) as client:
            resp = await client.get("https://trends24.in/united-states/")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                # trends24 uses ol.trend-card__list directly (no wrapper .trend-card)
                seen = set()
                rank = 1
                for ol in soup.select("ol.trend-card__list"):
                    for li in ol.find_all("li"):
                        term = li.get_text(strip=True).lstrip("#").strip()
                        if term and term.lower() not in seen:
                            seen.add(term.lower())
                            results.append({
                                "term": term,
                                "rank": rank,
                                "source": "twitter",
                                "detail": "",
                            })
                            rank += 1
                            if rank > 25:
                                break
                    if rank > 25:
                        break
            else:
                logger.warning(f"trends24.in returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Twitter trending (trends24.in) failed: {e}")
    return results


# ─── Combined ────────────────────────────────────────────────────────────────

async def fetch_all_trending() -> dict:
    """Fetch trending topics from all sources concurrently."""
    google_res, reddit_res, twitter_res = await asyncio.gather(
        fetch_google_trending(),
        fetch_reddit_trending(),
        fetch_twitter_trending(),
        return_exceptions=True,
    )
    return {
        "google": google_res if isinstance(google_res, list) else [],
        "reddit": reddit_res if isinstance(reddit_res, list) else [],
        "twitter": twitter_res if isinstance(twitter_res, list) else [],
    }
