#!/usr/bin/env python3
"""
fetch_talk_of_the_town.py — stdlib-only New Yorker Talk of the Town fetcher.

Usage:
  python3 fetch_talk_of_the_town.py [--covered URL,URL,...] [--out PATH]

Emits JSON to stdout (and optionally --out):
  {"available": bool, "title": str, "section": str, "dek": str,
   "text": str, "url": str, "source": "The New Yorker", "error": str|null}

Exit code: 0 on success, 2 on failure.

Strategy:
  TOC page (https://www.newyorker.com/magazine/talk-of-the-town) ships its
  article index as regular anchor markup. Regex-extract /magazine/YYYY/MM/DD/slug
  paths, de-dup, sort by the embedded date descending, drop covered URLs, pick
  top.

  Article pages ship LD+JSON <script type="application/ld+json"> with a
  NewsArticle block whose `articleBody` field is the clean article text —
  no JS walking required. `headline`, `articleSection`, `alternativeHeadline`
  (dek), and `datePublished` all live in the same block.

  Falls back to <p>-tag scrape only if LD+JSON is missing.

Known constraints:
  - newyorker.com 403s empty/weak User-Agents. Full Chrome UA works.
  - No cookies, no JS execution needed.
"""

import argparse
import json
import re
import sys
import urllib.request
from html import unescape
from typing import Optional

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}

TOC_URL = "https://www.newyorker.com/magazine/talk-of-the-town"
ARTICLE_PATH_RE = re.compile(r"/magazine/(\d{4})/(\d{2})/(\d{2})/([a-z0-9-]+)")
LD_JSON_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def http_get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_article_paths(toc_html: str) -> list:
    """Return list of (YYYYMMDD_int, full_url) sorted desc, de-duplicated."""
    seen = {}
    for m in ARTICLE_PATH_RE.finditer(toc_html):
        y, mo, d, slug = m.groups()
        path = f"/magazine/{y}/{mo}/{d}/{slug}"
        full = "https://www.newyorker.com" + path
        date_key = int(y + mo + d)
        if full not in seen:
            seen[full] = date_key
    ordered = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
    return [(dk, url) for url, dk in ordered]


def pick_novel(paths, covered: set) -> Optional[str]:
    covered_norm = {c.rstrip("/") for c in covered}
    for _, url in paths:
        if url.rstrip("/") not in covered_norm:
            return url
    return None


def load_ld_newsarticle(html: str) -> Optional[dict]:
    for m in LD_JSON_RE.finditer(html):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") in ("NewsArticle", "Article", "ReportageNewsArticle"):
                return node
    return None


def strip_html_fallback(html: str) -> str:
    body_match = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
    chunk = body_match.group(1) if body_match else html
    paras = re.findall(r"<p[^>]*>(.*?)</p>", chunk, re.DOTALL)
    out = []
    for p in paras:
        txt = re.sub(r"<[^>]+>", "", p)
        txt = unescape(txt).strip()
        if len(txt) > 40:
            out.append(txt)
    return "\n\n".join(out)


def fetch(covered: set) -> dict:
    base = {"available": False, "title": "", "section": "", "dek": "",
            "text": "", "url": "", "source": "The New Yorker", "error": None}
    try:
        toc_html = http_get(TOC_URL)
    except Exception as e:
        base["error"] = f"toc_fetch_failed: {e}"
        return base

    paths = extract_article_paths(toc_html)
    if not paths:
        base["error"] = "toc_no_paths_found"
        return base

    url = pick_novel(paths, covered)
    if not url:
        base["error"] = "all_articles_already_covered"
        return base
    base["url"] = url

    try:
        art_html = http_get(url)
    except Exception as e:
        base["error"] = f"article_fetch_failed: {e}"
        return base

    article = load_ld_newsarticle(art_html)
    if article:
        base["title"] = article.get("headline", "") or ""
        base["section"] = article.get("articleSection", "") or ""
        base["dek"] = article.get("alternativeHeadline", "") or ""
        body = article.get("articleBody", "") or ""
        if body and len(body) > 500:
            base["text"] = body
            base["available"] = True
            return base

    text = strip_html_fallback(art_html)
    if len(text) > 500:
        base["text"] = text
        base["available"] = True
        if not base["title"]:
            m = re.search(r"<title>(.*?)</title>", art_html, re.DOTALL)
            if m:
                base["title"] = unescape(re.sub(r"\s+", " ", m.group(1))).strip()
        return base

    base["error"] = f"article_text_too_short ({len(text)} chars, ld={'yes' if article else 'no'})"
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--covered", default="", help="comma-separated covered URLs")
    ap.add_argument("--out", default="", help="optional path to also write JSON")
    args = ap.parse_args()

    covered = {u.strip() for u in args.covered.split(",") if u.strip()}
    result = fetch(covered)
    payload = json.dumps(result, ensure_ascii=False)
    print(payload)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
    sys.exit(0 if result.get("available") else 2)


if __name__ == "__main__":
    main()
