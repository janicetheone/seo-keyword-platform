import httpx
import logging
import json
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.competitor import Competitor, CompetitorPage
from backend.models.competitor_keyword import CompetitorKeyword
from backend.models.keyword import Keyword
from backend.models.collection_job import CollectionJob
from backend.utils.rate_limiter import competitor_limiter
from backend.utils.text_processing import extract_ngrams, filter_stopwords, deduplicate_keywords

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


async def fetch_sitemap_urls(sitemap_url: str, max_urls: int = 100) -> list[str]:
    """Parse a sitemap.xml and return page URLs."""
    await competitor_limiter.acquire()
    urls = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(sitemap_url, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"Sitemap fetch failed: {sitemap_url} -> {resp.status_code}")
                return urls
            soup = BeautifulSoup(resp.text, "lxml-xml")

            # Check for sitemap index
            sitemaps = soup.find_all("sitemap")
            if sitemaps:
                for sm in sitemaps[:5]:
                    loc = sm.find("loc")
                    if loc:
                        sub_urls = await fetch_sitemap_urls(loc.text.strip(), max_urls=max_urls // 5)
                        urls.extend(sub_urls)
            else:
                for url_tag in soup.find_all("url"):
                    loc = url_tag.find("loc")
                    if loc:
                        urls.append(loc.text.strip())

    except Exception as e:
        logger.warning(f"Sitemap parse error for {sitemap_url}: {e}")

    return urls[:max_urls]


async def crawl_page(url: str) -> dict | None:
    """Crawl a single page and extract SEO elements."""
    await competitor_limiter.acquire()
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "lxml")

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "").strip()

            h1 = ""
            h1_tag = soup.find("h1")
            if h1_tag:
                h1 = h1_tag.get_text(strip=True)

            h2s = [tag.get_text(strip=True) for tag in soup.find_all("h2")]

            return {
                "url": url,
                "title": title,
                "meta_description": meta_desc,
                "h1": h1,
                "h2s": h2s,
            }
    except Exception as e:
        logger.warning(f"Page crawl failed for {url}: {e}")
        return None


async def analyze_competitor(db: AsyncSession, competitor_id: int) -> CollectionJob:
    """Full competitor analysis pipeline."""
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise ValueError(f"Competitor {competitor_id} not found")

    job = CollectionJob(
        job_type="competitor_crawl",
        status="running",
        target=competitor.domain,
        started_at=datetime.utcnow(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        # Step 1: Fetch sitemap
        sitemap_url = competitor.sitemap_url or f"https://{competitor.domain}/sitemap.xml"
        urls = await fetch_sitemap_urls(sitemap_url)
        job.progress = 20
        await db.commit()

        if not urls:
            # Fallback: try common pages
            urls = [
                f"https://{competitor.domain}",
                f"https://{competitor.domain}/features",
                f"https://{competitor.domain}/templates",
                f"https://{competitor.domain}/pricing",
            ]

        # Step 2: Crawl pages
        all_keywords_text = []
        pages_crawled = 0
        for i, url in enumerate(urls[:50]):
            page_data = await crawl_page(url)
            if page_data:
                page = CompetitorPage(
                    competitor_id=competitor.id,
                    url=page_data["url"],
                    title=page_data["title"],
                    meta_description=page_data["meta_description"],
                    h1=page_data["h1"],
                    h2s=json.dumps(page_data["h2s"]),
                )
                db.add(page)
                pages_crawled += 1

                # Extract keywords from page elements
                text_parts = [page_data["title"], page_data["meta_description"], page_data["h1"]]
                text_parts.extend(page_data["h2s"])
                full_text = " ".join(text_parts)
                ngrams = extract_ngrams(full_text, min_n=1, max_n=3)
                ngrams = filter_stopwords(ngrams)

                for ngram in ngrams:
                    all_keywords_text.append({
                        "keyword": ngram,
                        "source_page": url,
                        "in_title": 1 if ngram in page_data["title"].lower() else 0,
                        "in_h1": 1 if ngram in page_data["h1"].lower() else 0,
                        "in_meta": 1 if ngram in page_data["meta_description"].lower() else 0,
                    })

            job.progress = 20 + (60 * (i + 1) / min(len(urls), 50))
            await db.commit()

        # Step 3: Aggregate and save competitor keywords
        kw_agg = {}
        for item in all_keywords_text:
            kw = item["keyword"]
            if kw not in kw_agg:
                kw_agg[kw] = {"frequency": 0, "in_title": 0, "in_h1": 0, "in_meta": 0, "source_page": item["source_page"]}
            kw_agg[kw]["frequency"] += 1
            kw_agg[kw]["in_title"] += item["in_title"]
            kw_agg[kw]["in_h1"] += item["in_h1"]
            kw_agg[kw]["in_meta"] += item["in_meta"]

        # Delete old keywords for this competitor
        old_kws = await db.execute(
            select(CompetitorKeyword).where(CompetitorKeyword.competitor_id == competitor.id)
        )
        for old in old_kws.scalars().all():
            await db.delete(old)

        saved = 0
        for kw_text, agg in kw_agg.items():
            if agg["frequency"] >= 1 and len(kw_text) > 2:
                ck = CompetitorKeyword(
                    competitor_id=competitor.id,
                    keyword=kw_text,
                    source_page=agg["source_page"],
                    frequency=agg["frequency"],
                    in_title=agg["in_title"],
                    in_h1=agg["in_h1"],
                    in_meta=agg["in_meta"],
                )
                db.add(ck)
                saved += 1

        competitor.last_crawled = datetime.utcnow()
        competitor.total_pages = pages_crawled
        job.keywords_found = saved
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Competitor analysis for {competitor.domain}: {pages_crawled} pages, {saved} keywords")

    except Exception as e:
        logger.error(f"Competitor analysis failed for {competitor.domain}: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        await db.commit()

    return job


async def get_keyword_gap(db: AsyncSession, competitor_id: int) -> dict:
    """Analyze keyword gap between us and a competitor."""
    # Our keywords
    our_result = await db.execute(select(Keyword.keyword))
    our_keywords = {row[0] for row in our_result.all()}

    # Competitor keywords
    comp_result = await db.execute(
        select(CompetitorKeyword.keyword).where(CompetitorKeyword.competitor_id == competitor_id)
    )
    comp_keywords = {row[0] for row in comp_result.all()}

    gap = comp_keywords - our_keywords  # They have, we don't
    overlap = our_keywords & comp_keywords  # Both have
    unique = our_keywords - comp_keywords  # We have, they don't

    return {
        "gap": sorted(list(gap))[:100],
        "overlap": sorted(list(overlap))[:100],
        "unique": sorted(list(unique))[:100],
        "gap_count": len(gap),
        "overlap_count": len(overlap),
        "unique_count": len(unique),
    }
