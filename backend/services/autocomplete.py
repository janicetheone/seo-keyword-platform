import httpx
import json
import string
import asyncio
import logging
from backend.utils.rate_limiter import autocomplete_limiter
from backend.utils.text_processing import clean_keyword, deduplicate_keywords

logger = logging.getLogger(__name__)

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"


async def fetch_autocomplete(query: str, lang: str = "en") -> list[str]:
    """Fetch Google Autocomplete suggestions for a query."""
    await autocomplete_limiter.acquire()
    params = {
        "client": "firefox",
        "q": query,
        "hl": lang,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(AUTOCOMPLETE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 1:
                return [clean_keyword(s) for s in data[1] if isinstance(s, str)]
    except Exception as e:
        logger.warning(f"Autocomplete failed for '{query}': {e}")
    return []


async def expand_with_alphabet(seed: str, lang: str = "en") -> list[str]:
    """Expand a seed keyword with alphabet suffixes (seed + a/b/c/.../z)."""
    tasks = []
    # Base query
    tasks.append(fetch_autocomplete(seed, lang))
    # Alphabet expansion
    for letter in string.ascii_lowercase:
        tasks.append(fetch_autocomplete(f"{seed} {letter}", lang))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_keywords = []
    for result in results:
        if isinstance(result, list):
            all_keywords.extend(result)
    return deduplicate_keywords(all_keywords)


async def expand_keyword(seed: str, depth: int = 1, lang: str = "en") -> list[str]:
    """Recursively expand a seed keyword.

    depth=1: just alphabet expansion
    depth=2: take top 5 results and expand again
    """
    all_keywords = await expand_with_alphabet(seed, lang)
    logger.info(f"Depth 1: Found {len(all_keywords)} keywords for '{seed}'")

    if depth >= 2 and all_keywords:
        top_seeds = all_keywords[:5]
        for sub_seed in top_seeds:
            sub_results = await expand_with_alphabet(sub_seed, lang)
            all_keywords.extend(sub_results)
        all_keywords = deduplicate_keywords(all_keywords)
        logger.info(f"Depth 2: Total {len(all_keywords)} keywords for '{seed}'")

    return all_keywords
