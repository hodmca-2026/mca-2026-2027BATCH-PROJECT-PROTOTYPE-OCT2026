"""
Scrapy-based version of the competitor price crawler (IR Unit V: "python scrapy").

Scrapy is the industrial-strength choice when crawling needs to follow pagination
links, respect robots.txt / crawl-delay automatically, and run many requests
concurrently — which is the difference between this and the simpler
BeautifulSoup script (crawler.py), which is better suited to a single already-
known listing page.

Run with:
    scrapy runspider scrapy_spider.py -a source=sample_competitor_page.html -o output.json

Or against a real site once selectors are adjusted to match its markup:
    scrapy runspider scrapy_spider.py -a source=https://example-fashion-site.com/mens-shirts -o output.json
"""

import re
import scrapy


def parse_price(text: str):
    cleaned = re.sub(r"[^\d.]", "", text or "")
    return float(cleaned) if cleaned else None


class CompetitorPriceSpider(scrapy.Spider):
    name = "competitor_prices"

    # CSS selectors — adjust these to match the real target site's HTML structure
    card_selector = ".product-card"
    name_selector = ".product-name::text"
    price_selector = ".product-price::text"

    def __init__(self, source=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not source:
            raise ValueError("Pass a source with -a source=<url_or_local_file>")
        self.source = source

    def _build_request(self):
        if self.source.startswith("http://") or self.source.startswith("https://"):
            return scrapy.Request(url=self.source, callback=self.parse)
        import os
        path = os.path.abspath(self.source)
        return scrapy.Request(url=f"file://{path}", callback=self.parse)

    async def start(self):
        # Scrapy >= 2.13 entrypoint
        yield self._build_request()

    def start_requests(self):
        # Backward-compatible entrypoint for Scrapy < 2.13
        yield self._build_request()

    def parse(self, response):
        for card in response.css(self.card_selector):
            name = card.css(self.name_selector).get()
            price_raw = card.css(self.price_selector).get()
            if not name:
                continue
            yield {
                "name": name.strip(),
                "price": parse_price(price_raw),
            }
