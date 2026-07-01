from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import feedparser
import httpx
from pydantic import BaseModel, Field


ARXIV_API_URL = "https://export.arxiv.org/api/query"
DEFAULT_PAGE_SIZE = 100
REQUEST_INTERVAL_SECONDS = 3.0


class ArxivApiError(RuntimeError):
    """Raised when the arXiv API request or response cannot be handled."""


class Paper(BaseModel):
    title: str
    authors: list[str]
    published: datetime
    updated: datetime
    arxiv_id: str
    abstract_url: str
    pdf_url: str
    primary_category: str
    categories: list[str]
    summary: str
    matched_keywords: list[str] = Field(default_factory=list)
    score: int = 0


def build_search_query(keywords: list[str], categories: list[str]) -> str:
    if not keywords:
        raise ValueError("At least one keyword is required to query arXiv.")
    if not categories:
        raise ValueError("At least one arXiv category is required.")

    keyword_terms = []
    for keyword in keywords:
        escaped = keyword.replace('"', '\\"')
        keyword_terms.append(f'ti:"{escaped}"')
        keyword_terms.append(f'abs:"{escaped}"')

    category_terms = [f"cat:{category}" for category in categories]
    return f"({' OR '.join(keyword_terms)}) AND ({' OR '.join(category_terms)})"


def build_query_url(search_query: str, start: int, max_results: int) -> str:
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def fetch_papers(
    keywords: list[str],
    categories: list[str],
    max_results: int = 100,
    timeout: float = 20.0,
    client: httpx.Client | None = None,
) -> list[Paper]:
    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    search_query = build_search_query(keywords, categories)
    owns_client = client is None
    active_client = client or httpx.Client(timeout=timeout, follow_redirects=True)
    papers: list[Paper] = []

    try:
        for start in range(0, max_results, DEFAULT_PAGE_SIZE):
            if start:
                time.sleep(REQUEST_INTERVAL_SECONDS)
            page_size = min(DEFAULT_PAGE_SIZE, max_results - start)
            url = build_query_url(search_query, start=start, max_results=page_size)
            try:
                response = active_client.get(url)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ArxivApiError(
                    f"arXiv API returned HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                ) from exc
            except httpx.TimeoutException as exc:
                raise ArxivApiError("Timed out while querying the arXiv API.") from exc
            except httpx.RequestError as exc:
                raise ArxivApiError(f"Network error while querying the arXiv API: {exc}") from exc

            page_papers = parse_feed(response.text)
            papers.extend(page_papers)
            if len(page_papers) < page_size:
                break
    finally:
        if owns_client:
            active_client.close()

    return papers[:max_results]


def parse_feed(atom_xml: str) -> list[Paper]:
    parsed = feedparser.parse(atom_xml)
    if parsed.bozo:
        raise ArxivApiError(f"Malformed arXiv API response: {parsed.bozo_exception}")

    entries = getattr(parsed, "entries", [])
    papers: list[Paper] = []
    for entry in entries:
        try:
            papers.append(_paper_from_entry(entry))
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ArxivApiError(f"Malformed arXiv entry in API response: {exc}") from exc
    return papers


def _paper_from_entry(entry: Any) -> Paper:
    links = list(entry.get("links", []))
    abstract_url = _entry_abstract_url(entry, links)
    pdf_url = _entry_pdf_url(links)
    categories = _entry_categories(entry)
    primary_category = _entry_primary_category(entry, categories)

    return Paper(
        title=_clean_text(entry["title"]),
        authors=[author["name"] for author in entry.get("authors", [])],
        published=_parse_datetime(entry["published"]),
        updated=_parse_datetime(entry.get("updated", entry["published"])),
        arxiv_id=_entry_arxiv_id(entry, abstract_url),
        abstract_url=abstract_url,
        pdf_url=pdf_url,
        primary_category=primary_category,
        categories=categories,
        summary=_clean_text(entry.get("summary", "")),
    )


def _entry_abstract_url(entry: Any, links: list[dict[str, Any]]) -> str:
    for link in links:
        if link.get("rel") == "alternate" and link.get("href"):
            return str(link["href"])
    return str(entry.get("id", ""))


def _entry_pdf_url(links: list[dict[str, Any]]) -> str:
    for link in links:
        href = str(link.get("href", ""))
        if link.get("title") == "pdf" or link.get("type") == "application/pdf" or "/pdf/" in href:
            return href
    return ""


def _entry_categories(entry: Any) -> list[str]:
    categories = [str(tag["term"]) for tag in entry.get("tags", []) if tag.get("term")]
    return list(dict.fromkeys(categories))


def _entry_primary_category(entry: Any, categories: list[str]) -> str:
    primary = entry.get("arxiv_primary_category")
    if isinstance(primary, dict) and primary.get("term"):
        return str(primary["term"])
    return categories[0] if categories else ""


def _entry_arxiv_id(entry: Any, abstract_url: str) -> str:
    raw_id = str(entry.get("id", abstract_url)).rstrip("/")
    candidate = raw_id.rsplit("/", maxsplit=1)[-1]
    return re.sub(r"v\d+$", "", candidate)


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_text(value: str) -> str:
    return " ".join(value.split())

