import argparse
import json
import os
import pathlib
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# --- Dependencies ---
try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    sys.exit("Missing dep: pip install curl_cffi")

try:
    from selectolax.parser import HTMLParser
except ImportError:
    sys.exit("Missing dep: pip install selectolax")

# --- Config ---
ARCHIVE_BASE = "https://archive.ph"
REQUEST_DELAY_SEC = 3.0
REQUEST_TIMEOUT = 45
MAX_RETRIES = 3

CF_CHALLENGE_SIGNATURES = (
    "Just a moment...",
    "Checking your browser",
    "cf-browser-verification",
    "challenge-platform",
)

# New Yorker CSS selector fallback chains
TITLE_SELECTORS = [
    'h1[class*="Hed"]', 'h1[class*="hed"]', 'h1[class*="title"]',
    'h1[class*="Title"]', 'h1',
]
DEK_SELECTORS = [
    '[class*="Dek"]', '[class*="dek"]', 'h2[class*="sub"]',
    '.article__dek', 'h2',
]
AUTHOR_SELECTORS = [
    '[class*="Byline"] a', '[class*="byline"] a',
    '[class*="ContributorLink"]', '[rel="author"]',
    '[class*="Byline"]', '[class*="byline"]',
]
DATE_SELECTORS = [
    'time[datetime]', 'time', '[class*="publish-date"]',
    '[class*="PublishDate"]', '[class*="DateTime"]',
]
BODY_SELECTORS = [
    'div[class*="BodyContent"] p',
    'div[class*="ArticleBody"] p',
    'div[class*="article-body"] p',
    'div[class*="body-content"] p',
    'article p',
    'div[class*="content"] p',
]


# --- Data model ---
@dataclass
class Article:
    url: str
    snapshot_url: str
    title: str
    dek: str
    author: str
    published: str
    body: str

    def as_markdown(self) -> str:
        lines = [f"# {self.title}"]
        if self.dek:
            lines.append(f"*{self.dek}*\n")
        if self.author or self.published:
            meta = " | ".join(filter(None, [self.author, self.published]))
            lines.append(f"{meta}\n")
        lines.append(self.body)
        return "\n".join(lines)

    def to_json(self, source: str = "The New Yorker") -> dict:
        return {
            "available": True,
            "title": self.title,
            "text": self.as_markdown(),
            "source": source,
            "url": self.url,
        }


def _first_text(tree: HTMLParser, selectors: list) -> str:
    for sel in selectors:
        node = tree.css_first(sel)
        if node:
            text = node.text(strip=True)
            if text:
                return text
    return ""


def _first_attr(tree: HTMLParser, selectors: list, attr: str) -> str:
    for sel in selectors:
        node = tree.css_first(sel)
        if node and node.attributes.get(attr, ""):
            return node.attributes[attr]
    return ""


# --- Core scraping ---
def fetch_archive_snapshot(url: str) -> Optional[Article]:
    session = cffi_requests.Session(impersonate="chrome124")
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
    }

    archive_url = f"{ARCHIVE_BASE}/newest/{url}"
    resp = None

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(
                archive_url, headers=headers,
                timeout=REQUEST_TIMEOUT, allow_redirects=True
            )
            if any(sig in resp.text for sig in CF_CHALLENGE_SIGNATURES):
                sys.stderr.write(f"CF challenge on attempt {attempt + 1}\n")
                time.sleep(REQUEST_DELAY_SEC * 2)
                continue
            if resp.status_code == 404:
                sys.stderr.write("No archive snapshot found for this URL\n")
                return None
            if resp.status_code == 200:
                break
            sys.stderr.write(f"HTTP {resp.status_code} on attempt {attempt + 1}\n")
            time.sleep(REQUEST_DELAY_SEC)
        except Exception as e:
            sys.stderr.write(f"Request error attempt {attempt + 1}: {e}\n")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(REQUEST_DELAY_SEC)
    else:
        return None

    snapshot_url = str(resp.url)
    tree = HTMLParser(resp.text)

    title = _first_text(tree, TITLE_SELECTORS)
    dek = _first_text(tree, DEK_SELECTORS)
    author = _first_text(tree, AUTHOR_SELECTORS)

    # Date: prefer datetime attr, fall back to text
    published = _first_attr(tree, ['time[datetime]'], 'datetime')
    if not published:
        published = _first_text(tree, DATE_SELECTORS)

    # Body paragraphs
    body_paragraphs = []
    for sel in BODY_SELECTORS:
        nodes = tree.css(sel)
        candidates = [n.text(strip=True) for n in nodes if n.text(strip=True)]
        if len(candidates) > 2:
            body_paragraphs = candidates
            break

    body = "\n\n".join(body_paragraphs)

    if not title or not body:
        sys.stderr.write(
            f"Extraction incomplete — title={bool(title)}, paragraphs={len(body_paragraphs)}\n"
            f"Snapshot URL: {snapshot_url}\n"
        )
        return None

    return Article(
        url=url,
        snapshot_url=snapshot_url,
        title=title,
        dek=dek,
        author=author,
        published=published,
        body=body,
    )


# --- Output helpers ---
def emit_fallback(url: str, source: str = "The New Yorker") -> None:
    sys.stdout.write(json.dumps(
        {"available": False, "title": "", "text": "", "source": source, "url": url},
        ensure_ascii=False, indent=2
    ) + "\n")


# --- URL resolution: env var (exec mode) or argparse (CLI mode) ---
def resolve_url_and_source() -> tuple:
    env_url = os.environ.get("SECTOR7_URL", "")
    env_source = os.environ.get("SECTOR7_SOURCE", "The New Yorker")
    if env_url:
        return env_url, env_source

    parser = argparse.ArgumentParser(description="Fetch TNY article via archive.ph, output JSON")
    parser.add_argument("--url", required=True, help="Article URL to fetch")
    parser.add_argument("--source", default="The New Yorker", help="Source label")
    args = parser.parse_args()
    return args.url, args.source


# --- Entry point ---
def main() -> None:
    url, source = resolve_url_and_source()

    try:
        article = fetch_archive_snapshot(url)
        if article:
            sys.stdout.write(json.dumps(article.to_json(source), ensure_ascii=False, indent=2) + "\n")
        else:
            emit_fallback(url, source)
    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        emit_fallback(url, source)


if __name__ == "__main__":
    main()
