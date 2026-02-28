import re
from typing import Iterable


def clean_keyword(kw: str) -> str:
    """Normalize a keyword string."""
    kw = kw.lower().strip()
    kw = re.sub(r'\s+', ' ', kw)
    kw = re.sub(r'[^\w\s\-\']', '', kw)
    return kw.strip()


def deduplicate_keywords(keywords: Iterable[str]) -> list[str]:
    """Remove duplicate keywords preserving order."""
    seen = set()
    result = []
    for kw in keywords:
        cleaned = clean_keyword(kw)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def extract_ngrams(text: str, min_n: int = 1, max_n: int = 3) -> list[str]:
    """Extract n-grams from text for keyword analysis."""
    words = clean_keyword(text).split()
    ngrams = []
    for n in range(min_n, max_n + 1):
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i + n])
            if len(ngram) > 2:
                ngrams.append(ngram)
    return ngrams


STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
    'not', 'no', 'nor', 'so', 'yet', 'both', 'each', 'every', 'all',
    'any', 'few', 'more', 'most', 'other', 'some', 'such', 'than',
    'too', 'very', 'just', 'about', 'up', 'out', 'if', 'then', 'that',
    'this', 'these', 'those', 'it', 'its', 'my', 'your', 'his', 'her',
    'our', 'their', 'what', 'which', 'who', 'whom', 'when', 'where',
    'why', 'how', 'i', 'me', 'we', 'us', 'you', 'he', 'she', 'they',
    'them', 'www', 'com', 'http', 'https',
}


def filter_stopwords(keywords: list[str]) -> list[str]:
    """Remove keywords that are just stop words."""
    return [kw for kw in keywords if not all(w in STOP_WORDS for w in kw.split())]
