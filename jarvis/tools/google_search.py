"""Live world news / web lookup via the Google Custom Search JSON API."""

import requests

from jarvis import config

SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def google_search(query: str, num_results: int = 5) -> str:
    """Search Google and return a compact text digest of the top results.

    Requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX (a Programmable
    Search Engine configured to search the whole web).
    """
    if not config.GOOGLE_SEARCH_API_KEY or not config.GOOGLE_SEARCH_CX:
        return (
            "Error: Google Search is not configured. "
            "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in .env."
        )

    resp = requests.get(
        SEARCH_ENDPOINT,
        params={
            "key": config.GOOGLE_SEARCH_API_KEY,
            "cx": config.GOOGLE_SEARCH_CX,
            "q": query,
            "num": min(max(num_results, 1), 10),
        },
        timeout=15,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return f"No results found for: {query}"

    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        snippet = item.get("snippet", "").replace("\n", " ")
        link = item.get("link", "")
        lines.append(f"{i}. {title}\n   {snippet}\n   Source: {link}")
    return "\n".join(lines)
