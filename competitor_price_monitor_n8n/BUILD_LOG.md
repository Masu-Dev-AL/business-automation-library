# Build Log — Vitamin Price Monitor

Tracks issues encountered during builds and setup. Keep this updated so others
can skip known pitfalls.

---

## Open Issues

| # | Date | Area | Issue | Status |
|---|---|---|---|---|
| — | — | — | — | — |

---

## Resolved Issues

| # | Date | Area | Issue | Resolution |
|---|---|---|---|---|
| 1 | 2026-04-30 | Infrastructure | Trafilatura can't be installed in n8n's hardened Docker image (no package manager) | Replaced with Python FastAPI sidecar service (`scraper-api`) running alongside n8n |
| 2 | 2026-04-30 | Extraction | CSS selector approach required manual re-discovery when sites redesigned | Replaced with JSON-LD → meta tags → Supplement Facts cascade — no stored selectors |
| 3 | 2026-04-30 | Cost | Claude used for extraction in weekly loop was expensive and fragile | Claude now only called once/week for analysis; extraction is programmatic |
| 4 | 2026-04-30 | Architecture | Weekly workflow couldn't detect flash sales (only saw week-boundary prices) | Moved to daily snapshots — scraper runs at 6am daily, weekly workflow aggregates |

---

## Build Notes

### Playwright in Docker
The `Dockerfile.scraper` runs `playwright install chromium --with-deps` at image build time.
This adds ~500MB to the image. If disk space is tight, drop `playwright` from requirements
and set `requires_browser=FALSE` on all product rows — the JSON-LD tier handles most sites.

### n8n Environment Variables
n8n must be started with `ANTHROPIC_API_KEY` and other env vars set at the Docker level
(in docker-compose.yml `environment` section). n8n's built-in Variables are an Enterprise
feature and cannot be used in the community edition.

### Google Sheets OAuth2
Both Google Sheets and Gmail use OAuth2 via the same Google Cloud project. Set up one
OAuth2 credential in n8n and share it across all Sheets and Gmail nodes.

### Rate Limiting
The scraper-api enforces a 5-second minimum between requests to the same domain (in-memory,
per-process). This is sufficient for Phase 1–3 scale with a single worker. If you scale
up significantly, consider adding Redis for cross-process rate state.

### NOW Foods / Thorne Bot Protection
If these sites start returning 403 or empty responses, set `requires_browser=TRUE` on
those rows in the products sheet. The scraper will route them through Playwright automatically.
Expect ~3–5x slower scrape time for browser-based URLs.
