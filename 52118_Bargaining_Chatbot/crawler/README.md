# Competitor Price Crawler (IR Unit V)

Two implementations of the same task — scraping a competitor's product listing
page for `{name, price}` pairs, then suggesting a floor/ceiling price range for
the Seller Dashboard based on what similar products sell for elsewhere.

- `crawler.py` — BeautifulSoup + requests. Simple, good for a single known page.
- `scrapy_spider.py` — Scrapy. Better when you need to follow pagination,
  respect robots.txt/crawl-delay, or crawl many pages concurrently.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run against the included test page

```bash
python crawler.py sample_competitor_page.html
# or
scrapy runspider scrapy_spider.py -a source=sample_competitor_page.html -o output.json
```

Both have been tested end-to-end against `sample_competitor_page.html` and
correctly extract all 5 sample products with prices.

## Run against a real site

Real fashion e-commerce sites weren't reachable from the sandboxed environment
this project was built in (outbound network there is restricted to package
registries only) — so this couldn't be tested against a live site here. To
point it at a real listing page on your own machine:

1. Open the target page in your browser, inspect the HTML, and note the CSS
   classes wrapping each product card, its name, and its price.
2. Either edit `DEFAULT_SELECTORS` in `crawler.py` / the selector attributes in
   `scrapy_spider.py`, or pass `--selectors config.json` to `crawler.py` with:
   ```json
   { "card": ".actual-card-class", "name": ".actual-name-class", "price": ".actual-price-class" }
   ```
3. Run it: `python crawler.py https://real-site.com/mens-shirts --selectors config.json`

Please also check the target site's `robots.txt` and terms of service before
crawling it for real.
