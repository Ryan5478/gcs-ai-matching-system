"""Tavily-powered job discovery with aggregator filtering."""

import os
from typing import List, Dict
from tavily import TavilyClient

from backend.engine.job_board_filter import (
    is_job_board,
    extract_company_from_url,
)

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        _client = TavilyClient(api_key=api_key)
    return _client


def discover_jobs(query: str, max_results: int = 20) -> Dict:
    """Search the web for jobs, filter out aggregators, return direct postings.

    Returns:
        {
            "results": [ {title, url, company, snippet, source}, ... ],
            "total_searched": int,
            "filtered_out": int,
        }
    """
    client = _get_client()

    # Nudge Tavily toward actual job pages
    enhanced_query = f"{query} job posting careers apply"

    try:
        response = client.search(
            query=enhanced_query,
            max_results=max_results,
            search_depth="advanced",
        )
    except Exception as e:
        raise RuntimeError(f"Tavily search failed: {e}") from e

    raw = response.get("results", []) or []

    kept: List[Dict] = []
    filtered = 0

    for r in raw:
        url = (r.get("url") or "").strip()
        if not url:
            continue

        if is_job_board(url):
            filtered += 1
            continue

        title = (r.get("title") or "").strip()
        snippet = (r.get("content") or "").strip()
        company = extract_company_from_url(url)

        # Skip obvious non-job pages
        lowered = (title + " " + snippet).lower()
        if not any(
            kw in lowered
            for kw in [
                "job",
                "role",
                "position",
                "career",
                "hiring",
                "engineer",
                "developer",
                "manager",
                "analyst",
            ]
        ):
            filtered += 1
            continue

        kept.append(
            {
                "title": title or "Untitled",
                "url": url,
                "company": company,
                "snippet": snippet[:400],
                "source": _host(url),
            }
        )

    return {
        "results": kept,
        "total_searched": len(raw),
        "filtered_out": filtered,
    }


def _host(url: str) -> str:
    from urllib.parse import urlparse

    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""
