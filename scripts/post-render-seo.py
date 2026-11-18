#!/usr/bin/env python3
"""Publish clean canonical URLs in the Quarto sitemap and page heads."""

from __future__ import annotations

import html
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


PROJECT_DIR = Path(os.environ.get("QUARTO_PROJECT_DIR", Path.cwd()))
OUTPUT_DIR = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site"))
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = PROJECT_DIR / OUTPUT_DIR

SITEMAP = OUTPUT_DIR / "sitemap.xml"
PROFILE_PAGE = PROJECT_DIR / "profile-page.html"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", SITEMAP_NS)


def clean_path(path: str) -> str:
    if path == "/index.html":
        return "/"
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    if path.endswith(".html"):
        return path[:-5]
    return path


def add_canonical(page: Path, canonical_url: str) -> None:
    if not page.is_file():
        return

    source = page.read_text(encoding="utf-8")
    canonical = f'<link rel="canonical" href="{html.escape(canonical_url, quote=True)}">'
    tag_pattern = re.compile(
        r"<link\b(?=[^>]*\brel\s*=\s*['\"]canonical['\"])[^>]*>\s*",
        re.IGNORECASE,
    )
    if tag_pattern.search(source):
        source = tag_pattern.sub(canonical + "\n", source, count=1)
    else:
        head_close = re.search(r"</head\s*>", source, re.IGNORECASE)
        if not head_close:
            raise RuntimeError(f"No closing </head> found in {page}")
        source = source[: head_close.start()] + canonical + "\n" + source[head_close.start() :]
    page.write_text(source, encoding="utf-8")


if not SITEMAP.is_file():
    raise FileNotFoundError(f"Quarto did not generate {SITEMAP}")

tree = ET.parse(SITEMAP)
root = tree.getroot()
url_tag = f"{{{SITEMAP_NS}}}url"
loc_tag = f"{{{SITEMAP_NS}}}loc"
canonical_urls: list[str] = []

for url in root.findall(url_tag):
    loc = url.find(loc_tag)
    if loc is None or not loc.text:
        continue

    original_url = loc.text.strip()
    parsed = urlsplit(original_url)
    canonical_path = clean_path(parsed.path)
    canonical_url = urlunsplit(
        (parsed.scheme, parsed.netloc, canonical_path, parsed.query, parsed.fragment)
    )
    loc.text = canonical_url
    canonical_urls.append(canonical_url)

    output_path = OUTPUT_DIR / unquote(parsed.path).lstrip("/")
    if parsed.path.endswith("/"):
        output_path /= "index.html"
    add_canonical(output_path, canonical_url)

tree.write(SITEMAP, encoding="UTF-8", xml_declaration=True)

homepage = OUTPUT_DIR / "index.html"
if homepage.is_file() and PROFILE_PAGE.is_file():
    source = homepage.read_text(encoding="utf-8")
    profile_schema = PROFILE_PAGE.read_text(encoding="utf-8").strip()
    if '"@type": "ProfilePage"' not in source:
        head_close = re.search(r"</head\s*>", source, re.IGNORECASE)
        if not head_close:
            raise RuntimeError(f"No closing </head> found in {homepage}")
        source = source[: head_close.start()] + profile_schema + "\n" + source[head_close.start() :]
        homepage.write_text(source, encoding="utf-8")

print(f"Updated clean sitemap URLs and canonical tags for {len(canonical_urls)} pages.")
