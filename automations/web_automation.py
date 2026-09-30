"""02 Web Automation: scrape page titles/links and check a site for broken links.

Uses only `requests` + the standard-library HTML parser, so no browser is needed.
For JavaScript-heavy sites, swap in Selenium or Playwright.
"""
import argparse
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

HEADERS = {"User-Agent": "python-automation-toolkit/1.0"}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()


def parse_page(html: str, base_url: str) -> tuple[str, list[str]]:
    """Return the page title and absolute http(s) links, de-duplicated in order."""
    parser = LinkParser()
    parser.feed(html)
    seen, links = set(), []
    for href in parser.links:
        url = urljoin(base_url, href).split("#")[0]
        if urlparse(url).scheme in ("http", "https") and url not in seen:
            seen.add(url)
            links.append(url)
    return parser.title, links


def scrape(url: str) -> tuple[str, list[str]]:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return parse_page(resp.text, url)


def check_links(links: list[str]) -> list[tuple[str, str]]:
    """Return (url, problem) for every link that fails or returns >= 400."""
    broken = []
    for link in links:
        try:
            r = requests.head(link, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 405:  # some servers reject HEAD
                r = requests.get(link, headers=HEADERS, timeout=10)
            if r.status_code >= 400:
                broken.append((link, str(r.status_code)))
        except requests.RequestException as exc:
            broken.append((link, type(exc).__name__))
    return broken


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--check", action="store_true", help="also check links for errors")
    args = parser.parse_args()

    title, links = scrape(args.url)
    print(f"Title: {title}\nFound {len(links)} links")
    for link in links:
        print(f"  {link}")
    if args.check:
        broken = check_links(links)
        print(f"\n{len(broken)} broken link(s)")
        for link, problem in broken:
            print(f"  [{problem}] {link}")


if __name__ == "__main__":
    main()
