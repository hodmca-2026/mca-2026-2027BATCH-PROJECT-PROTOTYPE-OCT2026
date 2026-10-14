"""UNIT V (IR) - WEB CRAWLER using requests + Beautiful Soup.

Crawler structure:  seed URLs -> queue -> fetch -> parse -> extract data -> add new links -> repeat
Run:  python crawler.py https://example.com/jobs 20
Output: crawled_jobs.csv  (title, url, text)
"""
import re
import sys
import csv
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def html_to_text(html):
    """PARSE step: remove scripts/styles and return clean visible text + title."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(separator=" ")
    return title, clean(text)


def clean(text):
    text = re.sub(r"\S+@\S+", " email ", text)       # keep the idea "has email"
    text = re.sub(r"http\S+", " url ", text)
    text = re.sub(r"[^a-zA-Z ]", " ", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def crawl(seed_url, max_pages=20, out_file="crawled_jobs.csv"):
    """BFS crawler restricted to the seed's domain."""
    domain = urlparse(seed_url).netloc
    queue, visited, rows = deque([seed_url]), set(), []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:                                           # FETCH
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if "text/html" not in resp.headers.get("Content-Type", ""):
                continue
        except requests.RequestException:
            continue

        title, text = html_to_text(resp.text)          # PARSE + EXTRACT
        rows.append([title, url, text])
        print(f"[{len(visited)}] {url}")

        soup = BeautifulSoup(resp.text, "html.parser") # FOLLOW LINKS
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"]).split("#")[0]
            if urlparse(link).netloc == domain and link not in visited:
                queue.append(link)

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "url", "text"])
        w.writerows(rows)
    print(f"Saved {len(rows)} pages to {out_file}")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    crawl(seed, n)
