"""External website search for HR Insight AI using the Brave Search API.

The provider key is read only on the server from BRAVE_SEARCH_API_KEY.
This module uses Python's standard library, so no new package is required.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
REQUEST_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 2_000_000


class WebSearchAPIError(RuntimeError):
    """Safe, user-displayable external search error."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class WebSearchNotConfigured(WebSearchAPIError):
    """Raised when the server does not have a provider key configured."""

    def __init__(self) -> None:
        super().__init__(
            "External website search is not configured yet. Add BRAVE_SEARCH_API_KEY "
            "to a .env file in the project root and restart Flask. Internal HR search "
            "will continue to work without it.",
            status_code=503,
        )


def _safe_http_url(value: object) -> str | None:
    """Accept only ordinary HTTP(S) result URLs without embedded credentials."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"http", "https"}:
            return None
        if not parts.hostname or parts.username or parts.password:
            return None
        # Remove fragments so the same page does not appear multiple times.
        return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path or "/", parts.query, ""))
    except (TypeError, ValueError):
        return None


def _domain_for(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def search_web(query: str, count: int = 6) -> list[dict[str, str]]:
    """Search the web and return normalized title, URL, domain, and snippet fields."""
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        raise WebSearchNotConfigured()

    cleaned_query = str(query or "").strip()
    if not cleaned_query:
        return []
    count = max(1, min(int(count), 8))

    query_params = urlencode({
        "q": cleaned_query,
        "count": count,
        "country": "IN",
        "search_lang": "en",
        "safesearch": "moderate",
    })
    request = Request(
        f"{BRAVE_SEARCH_ENDPOINT}?{query_params}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
            "User-Agent": "HRInsightAI/1.0 (HR knowledge website search)",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise WebSearchAPIError("The external search response was too large. Please try again.", 502)
            payload = json.loads(raw.decode("utf-8"))
    except HTTPError as error:
        if error.code in {401, 403}:
            raise WebSearchAPIError(
                "The web search provider rejected the API key. Check BRAVE_SEARCH_API_KEY and confirm that the API plan is active.",
                502,
            ) from None
        if error.code == 429:
            raise WebSearchAPIError(
                "The external web search request limit has been reached. Please try again later.",
                429,
            ) from None
        raise WebSearchAPIError(
            f"The external web search provider returned HTTP {error.code}. Please try again later.",
            502,
        ) from None
    except (URLError, TimeoutError, OSError):
        raise WebSearchAPIError(
            "Could not connect to the external web search provider. Check your internet connection and try again.",
            502,
        ) from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise WebSearchAPIError(
            "The external search provider returned an unreadable response. Please try again later.",
            502,
        ) from None

    web = payload.get("web", {}) if isinstance(payload, dict) else {}
    raw_results = web.get("results", []) if isinstance(web, dict) else []
    if not isinstance(raw_results, list):
        raw_results = []

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        url = _safe_http_url(item.get("url"))
        if not url:
            continue
        dedupe_key = url.lower().rstrip("/")
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        domain = _domain_for(url)
        title = str(item.get("title") or domain or "Website result").strip()
        description = str(item.get("description") or "No description was provided by the search provider.").strip()
        # Keep the values short and prevent unexpectedly huge markup payloads.
        normalized.append({
            "title": title[:300],
            "url": url[:2000],
            "domain": domain[:255],
            "description": description[:1000],
        })
        if len(normalized) >= count:
            break

    return normalized
