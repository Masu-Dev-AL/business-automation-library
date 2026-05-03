# Vitamin Price Monitor

A competitor vitamin price monitoring system for supplement businesses. Tracks specific products across competitor websites on a daily schedule, normalizes all pricing to **cost-per-serving**, logs time-series snapshots to Google Sheets, and delivers a weekly email digest with Claude AI trend analysis.

## Overview

Onboarding a new product is a single step: add a URL to the products sheet. The system picks it up automatically within 5 minutes — no workflow to trigger, no selectors to configure.

| Component | Role |
|---|---|
| **n8n** (self-hosted) | Orchestration — scheduling, Google Sheets, Gmail, Claude analysis call |
| **scraper-api** (Python FastAPI) | Sidecar service — all HTTP scraping and price extraction |
| **scraper-api: JSON-LD + meta tags** | Primary extraction path — reads schema.org Product structured data |
| **scraper-api: Supplement Facts** | Servings extraction — parses FDA-required table for cost normalization |
| **Claude Haiku** | Fallback extraction only — onboarding when structured data unavailable |
| **Claude Sonnet** | Weekly trend analysis — cluster detection, significant drops, narrative summary |
| **Google Sheets** | Storage — 4 tabs: products, snapshots, changes, analysis |
| **Gmail** | Weekly digest delivery |

## How It Works

```
User adds URL to products sheet
  ↓ (up to 5 min)
Onboarding workflow: robots check → scraper-api → fill all product fields

Daily 6:00am:
  Read active products → scraper-api for each → append to snapshots tab

Monday 7:00am:
  Aggregate 7-day snapshots → detect changes → Claude Sonnet analysis → email digest
```

## Scraper Cascade (supplement-specific, no selectors)

```
Tier 1: JSON-LD schema.org Product  →  price, availability, name  (most stable)
Tier 2: Open Graph / meta tags      →  price fallback
Tier 3: Supplement Facts table      →  servings_per_container, serving_size
Tier 4: Claude Haiku fallback       →  price only, flagged  (onboarding only)
```

No CSS selectors anywhere — extraction uses structured data patterns that are maintained by the site's own platform team and stable across visual redesigns.

## Competitor Coverage

| Phase | Competitors |
|---|---|
| Phase 1 | NOW Foods, Life Extension, Thorne |
| Phase 2 | + Vitamin Shoppe, GNC |
| Phase 3 | 9 vitamins × 3+ competitors |

Multivitamins excluded — too many formulation variables to normalize reliably.

## Project Structure

```
competitor_price_monitor_n8n/
├── README.md
├── BUILD_LOG.md                             # Issue tracker for proven builds
├── scripts/
│   ├── py_scraper_api.py                   # FastAPI sidecar — endpoints /scrape /health /robots
│   ├── py_scraper_cascade.py               # Extraction cascade (JSON-LD → meta → table → Haiku)
│   ├── py_scraper_models.py                # Pydantic request/response models
│   ├── n8n_parse_scraper_response.js       # Code node: parse /scrape response + cost metrics
│   ├── n8n_aggregate_snapshots.js          # Code node: pivot 7-day snapshots for analysis
│   ├── n8n_detect_changes.js               # Code node: compare snapshot baselines
│   ├── n8n_build_email_digest.js           # Code node: Claude narrative + change data
│   ├── n8n_parse_analysis_response.js      # Code node: parse Claude Sonnet JSON
│   ├── n8n_parse_robots.js                 # Code node: parse robots.txt in n8n
│   └── robots_txt_checker.py              # CLI utility: pre-flight crawl permission check
├── workflow_json/
│   ├── vitamin-monitor-onboarding.json     # Workflow 1 node spec (build manually in n8n)
│   ├── vitamin-monitor-daily.json          # Workflow 2 node spec (build manually in n8n)
│   └── vitamin-monitor-weekly.json         # Workflow 3 node spec (build manually in n8n)
├── config/
│   ├── docker-compose.yml                  # n8n + scraper-api service definitions
│   ├── Dockerfile.scraper                  # Python 3.12 + Playwright Chromium
│   ├── requirements-scraper.txt            # Python dependencies for scraper-api
│   ├── .env.example                        # Credentials template
│   ├── google_sheets_seed.md               # Sheet schema + 5 Phase 1 seed rows
│   └── claude_analysis_prompt.md           # Sonnet analysis prompt + Haiku fallback prompt
└── technical_guide/
    ├── architecture.md                     # Mermaid architecture diagram
    └── technical_guide.md                  # Full setup and operational guide
```

## Quick Start

1. **Google Sheets**: Create a spreadsheet with tabs `products`, `snapshots`, `changes`, `analysis`. Add headers from `config/google_sheets_seed.md`. Pre-fill the 5 seed rows (URL + metadata only — leave all other fields blank).

2. **VPS deploy**:
   ```bash
   cp config/.env.example config/.env   # fill in your credentials
   docker compose -f config/docker-compose.yml up -d
   ```

3. **n8n credentials**: Set up Google Sheets OAuth2 and Gmail OAuth2 inside n8n (Credentials → New).

4. **Build workflows**: Follow `technical_guide/technical_guide.md` to build the 3 workflows in n8n.

5. **Activate**: Enable Workflow 1 (Onboarding). Within 5 minutes, the 5 seed rows will auto-populate. Then enable Workflow 2 (Daily) and Workflow 3 (Weekly).

## Email Digest Example

```
VITAMIN PRICE MONITOR — Week of Apr 28, 2026

EXECUTIVE SUMMARY
NOW Foods dropped Vitamin D3 5000 IU by 28% — now the cheapest D3 option
by a significant margin. Life Extension held steady across all products.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGNIFICANT CHANGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NOW Foods — Vitamin D3 5000 IU Softgels
  Cost/serving: $0.0389 → $0.0281  (-27.8%)  ✓ verified
  Claude: "NOW Foods is now 31% cheaper than Thorne for equivalent D3."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPETITIVE POSITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Vitamin D3   Cheapest: NOW-D3-002  $0.0281/serving  (+31% vs Thorne)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  5/5 products scraped successfully. 0 errors.
  Claude analysis: 2,340 tokens used.
```

## Cost Analysis

| Phase | Claude/week | Scraping | Weekly total |
|---|---|---|---|
| Phase 1 (5 products) | $0.012 (1× Sonnet) | $0 | < $0.02 |
| Phase 3 (27 products) | $0.034 (1× Sonnet) | $0 | < $0.05 |

Daily price capture uses zero LLM calls. Claude Sonnet fires once per week on a pre-aggregated data table (not raw HTML). Claude Haiku is called only during onboarding when structured data extraction fails.

## Normalization Quality

| Quality | Criteria | In Digest? |
|---|---|---|
| `verified` | Price + servings both extracted | Yes — cost-per-serving shown |
| `partial` | One value missing | Yes, flagged |
| `unresolvable` | Neither extractable | No — excluded from monitoring |

## Technologies

| Tool | Version | Purpose |
|---|---|---|
| n8n | latest | Workflow orchestration |
| FastAPI | 0.115 | Scraper sidecar API |
| httpx | 0.27 | Async HTTP client for static pages |
| BeautifulSoup4 + lxml | 4.12 / 5.3 | HTML parsing |
| Playwright (Chromium) | 1.48 | JS-rendered page fallback |
| anthropic SDK | 0.40 | Claude Haiku + Sonnet API |
| Google Sheets API | v4 | Storage (via n8n) |

## License

For educational and personal business use. Review each competitor site's Terms of Service and robots.txt before scraping.
