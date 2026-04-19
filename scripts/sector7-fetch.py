"""
sector7-fetch.py — Fetch New Yorker Talk of the Town articles.

Primary:  Jina Reader API (auth bypasses paywall, works from any IP, no extra deps)
Fallback: archive.ph via curl_cffi (works in CCR from server IPs, rate-limited from home)

Usage (either mode):
  SECTOR7_URL="https://..." python3 sector7-fetch.py
  python3 sector7-fetch.py --url "https://..."

Jina key: JINA_API_KEY env var, or read from JINA_KEY_FILE path.
"""

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

# --- Config ---
JINA_KEY_FILE = "/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/config/jina-api-key.txt"
ARCHIVE_BASE = "https://archive.ph"
REQUEST_TIMEOUT = 45
MAX_RETRIES = 3


# --- Data model ---
@dataclass
class Article:
    url: str
    title: str
    text: str  # full markdown body as-is from fetch
    source: str = "The New Yorker"

    def to_json(self) -> dict:
        return {
            "available": True,
            "title": self.title,
            "text": self.text,
            "source": self.source,
            "url": self.url,
        }


def emit_fallback(url: str) -> None:
    sys.stdout.write(json.dumps(
        {"available": False, "title": "", "text": "", "source": "The New Yorker", "url": url},
        ensure_ascii=False, indent=2,
    ) + "\n")


# --- Method 1: Jina Reader API ---
def _load_jina_key() -> str:
    key = os.environ.get("JINA_API_KEY", "").strip()
    if key:
        return key
    try:
        return pathlib.Path(JINA_KEY_FILE).read_text().strip()
    except Exception:
        return ""


def _extract_title_from_markdown(text: str) -> str:
    """Pull first # heading or Title: line from Jina markdown."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
    return ""


def fetch_via_jina(url: str) -> Optional[Article]:
    """Jina Reader: authenticated call bypasses NYer paywall. No curl_cffi needed."""
    key = _load_jina_key()
    if not key:
        sys.stderr.write("Jina key not found — skipping Jina\n")
        return None

    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(
        jina_url,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": "curl/8.4.0",
        },
    )

    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="replace").strip()
            # Detect 404/paywall/empty responses
            if not raw or len(raw) < 300:
                sys.stderr.write(f"Jina response too short ({len(raw)} chars)\n")
                return None
            if "Page Not Found" in raw or "404: Not Found" in raw:
                sys.stderr.write("Jina returned NYer 404 page — bad URL\n")
                return None
            if "Manage your consent" in raw and len(raw) < 2000:
                sys.stderr.write("Jina returned consent wall — possible paywall\n")
                return None
            title = _extract_title_from_markdown(raw)
            return Article(url=url, title=title or "Talk of the Town", text=raw)
        except urllib.error.HTTPError as e:
            sys.stderr.write(f"Jina HTTP {e.code} attempt {attempt + 1}\n")
            if e.code in (401, 403):
                return None  # bad key, don't retry
            time.sleep(2)
        except Exception as e:
            sys.stderr.write(f"Jina error attempt {attempt + 1}: {e}\n")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(2)

    return None


# --- Method 2: archive.ph fallback (requires curl_cffi + selectolax) ---
def fetch_via_archive(url: str) -> Optional[Article]:
    try:
        from curl_cffi import requests as cffi_requests
        from selectolax.parser import HTMLParser
    except ImportError:
        sys.stderr.write("curl_cffi/selectolax not installed — archive.ph fallback unavailable\n")
        return None

    CF_SIGS = ("Just a moment...", "Checking your browser", "cf-browser-verification", "challenge-platform")
    BODY_SELECTORS = [
        'div[class*="BodyContent"] p', 'div[class*="ArticleBody"] p',
        'div[class*="article-body"] p', 'article p', 'div[class*="content"] p',
    ]
    TITLE_SELECTORS = ['h1[class*="Hed"]', 'h1[class*="hed"]', 'h1[class*="title"]', 'h1']

    session = cffi_requests.Session(impersonate="chrome124")
    archive_url = f"{ARCHIVE_BASE}/newest/{url}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(archive_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if any(s in resp.text for s in CF_SIGS):
                sys.stderr.write(f"CF challenge attempt {attempt + 1}\n")
                time.sleep(6)
                continue
            if resp.status_code == 404:
                sys.stderr.write("No archive snapshot\n")
                return None
            if resp.status_code == 429:
                sys.stderr.write("archive.ph rate-limited (home IP)\n")
                return None
            if resp.status_code == 200:
                break
            time.sleep(3)
        except Exception as e:
            sys.stderr.write(f"archive.ph error attempt {attempt + 1}: {e}\n")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(3)
    else:
        return None

    tree = HTMLParser(resp.text)

    title = ""
    for sel in TITLE_SELECTORS:
        node = tree.css_first(sel)
        if node and node.text(strip=True):
            title = node.text(strip=True)
            break

    paragraphs = []
    for sel in BODY_SELECTORS:
        nodes = tree.css(sel)
        candidates = [n.text(strip=True) for n in nodes if n.text(strip=True)]
        if len(candidates) > 2:
            paragraphs = candidates
            break

    if not title or not paragraphs:
        return None

    body = "\n\n".join(paragraphs)
    text = f"# {title}\n\n{body}"
    return Article(url=url, title=title, text=text)


# --- URL resolution ---
def resolve_url() -> str:
    env_url = os.environ.get("SECTOR7_URL", "").strip()
    if env_url:
        return env_url
    parser = argparse.ArgumentParser(description="Fetch TNY article, output JSON")
    parser.add_argument("--url", required=True)
    return parser.parse_args().url


# --- Entry point ---
def main() -> None:
    url = resolve_url()
    if not url:
        sys.stderr.write("No URL provided\n")
        emit_fallback("")
        return

    # Try Jina first
    article = fetch_via_jina(url)

    # Fallback to archive.ph
    if not article:
        sys.stderr.write("Jina failed — trying archive.ph\n")
        article = fetch_via_archive(url)

    if article:
        sys.stdout.write(json.dumps(article.to_json(), ensure_ascii=False, indent=2) + "\n")
    else:
        emit_fallback(url)


if __name__ == "__main__":
    main()
