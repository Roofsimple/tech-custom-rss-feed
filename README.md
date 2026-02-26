# RSS Digest

A static site RSS aggregator for cybersecurity and tech news, auto-published via GitHub Actions.

## Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the fetch script
python fetch.py

# 3. Open the digest
open index.html        # Mac
start index.html       # Windows
```

## Customizing Feeds

Edit `feeds.yaml` to add or remove feeds. Each entry needs:
- `name` — display name
- `url` — RSS/Atom feed URL
- `category` — used for grouping (e.g. Security, Tech)

## Settings (feeds.yaml)

| Setting | Default | Description |
|---|---|---|
| `max_age_hours` | 24 | Only include articles newer than this |
| `max_articles_per_feed` | 10 | Cap per feed |
| `site_title` | — | Page heading |
| `timezone` | UTC | Display timezone for timestamps |

## GitHub Actions (Phase 4)

See `.github/workflows/update-feed.yml` — runs daily at 7am UTC, commits the updated `index.html` to the repo, and publishes via GitHub Pages.
