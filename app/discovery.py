import os, re, time, requests
from urllib.parse import urlencode
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

NIST_NEWS_FEED = "https://csrc.nist.gov/News"

def _serpapi_search(query: str, num: int = 10) -> List[Dict]:
    key = os.getenv("SERPAPI_KEY")
    if not key:
        return []

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "api_key": key,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    results = []
    for item in (data.get("organic_results") or []):
        link = item.get("link")
        title = item.get("title")
        if not link or not title:
            continue
        results.append({
            "url": link,
            "title": title,
            "source": "google-serpapi",
            "published": item.get("date") or item.get("snippet") or "",
        })
    return results

def _nist_csrc_fallback(num: int = 10) -> List[Dict]:
    # very simple fallback using site: filter
    q = "site:csrc.nist.gov \"SP 800\" update OR revision OR draft"
    return _serpapi_search(q, num)

def _rank_and_dedupe(items: List[Dict]) -> List[Dict]:
    seen = set()
    ranked = []
    for x in items:
        u = x["url"].split("#")[0]
        if u in seen:
            continue
        seen.add(u)
        ranked.append(x)
    return ranked[:10]

def discover_sources(topic: str, limit: int = 10) -> List[Dict]:
    query = f"{topic} site:nist.gov OR site:csrc.nist.gov"
    primary = _serpapi_search(query, num=limit)
    fallback = []
    if not primary:
        fallback = _nist_csrc_fallback(limit)
    merged = _rank_and_dedupe(primary + fallback)
    # Assign IDs
    for i, m in enumerate(merged):
        m["id"] = f"src{i+1:02d}"
    return merged
