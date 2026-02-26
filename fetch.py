#!/usr/bin/env python3
"""
RSS Digest Generator
Fetches feeds defined in feeds.yaml and renders a static index.html
"""

import feedparser
import yaml
import requests
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import time

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "feeds.yaml"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_PATH = BASE_DIR / "index.html"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def parse_published(entry):
    """Return a timezone-aware datetime from a feed entry, or None."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def fetch_feed(feed_config, max_age_hours, max_articles):
    """Fetch a single RSS feed and return a list of article dicts."""
    url = feed_config["url"]
    name = feed_config["name"]
    category = feed_config.get("category", "General")

    print(f"  Fetching: {name}")
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "RSSDigest/1.0"})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
    except Exception as e:
        print(f"    ✗ Error fetching {name}: {e}")
        return []

    if not parsed.entries:
        print(f"    ✗ Could not parse {name}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    articles = []

    for entry in parsed.entries[:max_articles * 2]:  # fetch extra, filter down
        pub = parse_published(entry)

        # If no date available, include anyway (some feeds omit dates)
        if pub and pub < cutoff:
            continue

        articles.append({
            "title": entry.get("title", "No title").strip(),
            "link": entry.get("link", "#"),
            "summary": _clean_summary(entry.get("summary", "")),
            "published": pub,
            "published_str": pub.strftime("%-I:%M %p · %b %-d") if pub else "Date unknown",
            "source": name,
            "category": category,
        })

        if len(articles) >= max_articles:
            break

    print(f"    ✓ {len(articles)} articles")
    return articles


def _clean_summary(raw: str) -> str:
    """Strip HTML tags and truncate summary text."""
    import re
    clean = re.sub(r"<[^>]+>", "", raw)
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"')
    clean = " ".join(clean.split())  # collapse whitespace
    return clean[:280] + "…" if len(clean) > 280 else clean


def build_digest(config):
    settings = config["settings"]
    max_age = settings.get("max_age_hours", 24)
    max_per_feed = settings.get("max_articles_per_feed", 10)
    tz_name = settings.get("timezone", "UTC")
    local_tz = ZoneInfo(tz_name)

    print("\n📡 Fetching feeds...")
    all_articles = []
    categories = {}

    for feed_cfg in config["feeds"]:
        articles = fetch_feed(feed_cfg, max_age, max_per_feed)
        all_articles.extend(articles)
        cat = feed_cfg.get("category", "General")
        categories.setdefault(cat, 0)
        categories[cat] += len(articles)

    # Sort all articles newest-first
    all_articles.sort(key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    print(f"\n✅ Total articles collected: {len(all_articles)}")

    # Group by category for template
    grouped = {}
    for article in all_articles:
        grouped.setdefault(article["category"], []).append(article)

    # Render template
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("digest.html")

    generated_at = datetime.now(local_tz).strftime("%A, %B %-d %Y · %-I:%M %p %Z")

    html = template.render(
        title=settings.get("site_title", "Daily Digest"),
        generated_at=generated_at,
        grouped=grouped,
        total=len(all_articles),
        max_age_hours=max_age,
    )

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"\n🌐 Digest saved to: {OUTPUT_PATH}")
    print(f"   Open with: open {OUTPUT_PATH}  (Mac) or start {OUTPUT_PATH}  (Windows)\n")


if __name__ == "__main__":
    config = load_config()
    build_digest(config)
