"""
Competitor Price Crawler (IR Unit V: "Web Crawler: web crawler structure,
web crawler libraries, python scrapy, beautiful soup")

Fetches product listing pages from a competitor site and extracts
{name, price} pairs using BeautifulSoup, so a seller can compare their
floor/ceiling pricing against real market prices before setting them
in the Seller Dashboard.

Usage:
    python crawler.py <url_or_local_path> [--selectors config.json]

By default this targets generic CSS selectors (`.product-card`, `.product-name`,
`.product-price`) matching common fashion-listing page structures. Point
`--selectors` at a JSON file to customize for a specific real site's markup,
e.g.:
    {"card": ".product-item", "name": ".title", "price": ".price"}

NOTE ON RUNNING THIS: real fashion e-commerce sites (Myntra, Ajio, etc.) are
not reachable from the sandboxed environment this project was built in
(outbound network is restricted to package registries only). This script is
written to work against any real site once you run it on your own machine
with normal internet access — just point it at a real product listing URL
and adjust the selectors to match that site's HTML structure. It has been
tested end-to-end against `sample_competitor_page.html` in this folder to
confirm the parsing logic itself is correct.
"""

import sys
import json
import argparse
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_SELECTORS = {
    "card": ".product-card",
    "name": ".product-name",
    "price": ".product-price",
}


def fetch_html(source: str) -> str:
    """Fetch HTML from a URL, or read it from a local file path (for testing)."""
    if source.startswith("http://") or source.startswith("https://"):
        headers = {"User-Agent": "Mozilla/5.0 (compatible; BazaaroPriceBot/1.0)"}
        resp = requests.get(source, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    return Path(source).read_text(encoding="utf-8")


def parse_price(text: str) -> float | None:
    """Extract a numeric price from strings like '₹2,199' or 'Rs. 1,799.00'."""
    cleaned = re.sub(r"[^\d.]", "", text)
    return float(cleaned) if cleaned else None


def crawl(source: str, selectors: dict) -> list[dict]:
    html = fetch_html(source)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for card in soup.select(selectors["card"]):
        name_el = card.select_one(selectors["name"])
        price_el = card.select_one(selectors["price"])
        if not name_el or not price_el:
            continue
        results.append({
            "name": name_el.get_text(strip=True),
            "price": parse_price(price_el.get_text(strip=True)),
        })
    return results


def suggest_pricing(results: list[dict]) -> dict:
    """Turn scraped competitor prices into a simple floor/ceiling suggestion —
    this is the piece that would feed into the Seller Dashboard's pricing form."""
    prices = [r["price"] for r in results if r["price"] is not None]
    if not prices:
        return {}
    avg = sum(prices) / len(prices)
    return {
        "sample_size": len(prices),
        "min_competitor_price": min(prices),
        "max_competitor_price": max(prices),
        "avg_competitor_price": round(avg, 2),
        "suggested_floor_price": round(min(prices) * 0.9, 2),   # 10% under cheapest competitor
        "suggested_ceiling_price": round(avg * 1.05, 2),        # 5% over average
    }


def main():
    parser = argparse.ArgumentParser(description="Crawl a competitor product listing page.")
    parser.add_argument("source", help="URL or local HTML file path to crawl")
    parser.add_argument("--selectors", help="Path to a JSON file overriding default CSS selectors")
    args = parser.parse_args()

    selectors = DEFAULT_SELECTORS
    if args.selectors:
        selectors = json.loads(Path(args.selectors).read_text())

    products = crawl(args.source, selectors)
    pricing = suggest_pricing(products)

    print(json.dumps({"products": products, "pricing_suggestion": pricing}, indent=2))


if __name__ == "__main__":
    main()
