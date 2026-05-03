# Vitamin Price Monitor — Technical Guide

---

## 1. Executive Summary

### Business Problem

Supplement brands and retailers compete on price for commodity vitamins where a 5–10% price difference can shift purchase decisions. Manual competitor monitoring is slow, inconsistent, and unscalable. Most off-the-shelf tools use CSS selectors that break whenever competitor sites redesign.

### Solution

An automated, selector-free competitor pricing system that:

- Tracks supplement product prices across NOW Foods, Life Extension, and Thorne on a daily schedule
- Normalizes all prices to **cost-per-serving** for apples-to-apples comparison (ignoring pack size differences)
- Auto-onboards new products — add a URL row and the system populates everything within 5 minutes
- Detects price changes ≥ 0.1% and logs them to a `changes` tab for historical analysis
- Delivers a weekly AI-powered trend analysis email every Monday morning via Claude Sonnet

### System Capabilities

| Capability | Detail |
|------------|--------|
| Products monitored | 5 (Phase 1) → 27 (Phase 3) |
| Daily scraping cadence | 6:00 am, no LLM calls |
| Weekly analysis | Monday 7:00 am, Claude Sonnet |
| Auto-onboarding | New product live within 5 minutes |
| Change detection threshold | ≥ 0.1% price or cost-per-serving delta |
| Extraction method | Selector-free: JSON-LD → meta tags → Supplement Facts table → Haiku fallback |
| Storage | Google Sheets (4 tabs) |
| Delivery | Gmail weekly digest |
| Daily scraping cost | $0.00 (no LLM) |
| Weekly analysis cost | < $0.02 (Phase 1) / < $0.05 (Phase 3) |

### Technologies

| Layer | Tool | Role |
|-------|------|------|
| Orchestration | n8n (self-hosted) | Scheduling, Sheets I/O, Gmail, Claude API call |
| Scraper Sidecar | Python FastAPI (`scraper-api`) | All HTTP scraping and price extraction |
| Page Rendering | httpx (static) + Playwright (JS) | Fetch HTML from competitor sites |
| Extraction | JSON-LD → meta tags → Supplement Facts table | Programmatic cascade — no CSS selectors |
| AI Extraction Fallback | Claude Haiku | Onboarding only, when structured data unavailable |
| AI Analysis | Claude Sonnet | Weekly trend analysis — narrative + cluster detection |
| Storage | Google Sheets (4 tabs) | products, snapshots, changes, analysis |
| Delivery | Gmail via n8n Gmail node | Weekly email digest |
| Infrastructure | Docker Compose | n8n + scraper-api on a single VPS |

---

## 2. Architecture Overview

See [`architecture.md`](architecture.md) for the full system diagram and [`n8n_workflow_diagram.md`](n8n_workflow_diagram.md) for detailed per-workflow node maps.

### Data Flow

1. User adds a product URL row to the `products` tab in Google Sheets
2. **Workflow 1 (Onboarding)** fires every 5 minutes, detects the blank `product_id`, checks `robots.txt`
3. Scraper API extracts price, serving data, and product name via the 4-tier cascade
4. Products tab is fully populated; product is now eligible for daily monitoring
5. **Workflow 2 (Daily Capture)** runs at 6:00 am, loops all active products, appends a snapshot row per product
6. Each snapshot includes `price`, `cost_per_serving`, `availability`, and extraction metadata
7. **Workflow 3 (Weekly Analysis)** runs Monday at 7:00 am, reads 7 days of snapshots
8. Change detection compares Monday's snapshot to last Monday's — logs any delta ≥ 0.1%
9. Claude Sonnet receives a pre-aggregated markdown table (not raw HTML) and returns structured JSON analysis
10. Gmail digest sent to configured recipient with executive summary, significant changes, and watch list

### Key Design Principles

1. **Selector-free extraction** — uses JSON-LD schema.org markup, meta tags, and FDA Supplement Facts tables. Survives site redesigns.
2. **Zero daily LLM cost** — Claude is only called once per week (analysis). Daily scraping is entirely programmatic.
3. **Sidecar pattern** — the Python FastAPI scraper runs as a separate Docker container. n8n stays clean; all scraping complexity lives in the sidecar.
4. **Modular three-workflow design** — onboarding, capture, and analysis are independent. Each can be triggered manually or disabled without affecting the others.
5. **Structured data priority** — Tier 1 (JSON-LD) is attempted first on every URL. Haiku fallback is gated to onboarding only and flagged for review.
6. **Cost normalization** — raw price is always converted to `cost_per_serving` for fair comparison across different pack sizes and serving counts.

---

## 3. Implementation Guide

### 3.1 Prerequisites

- VPS with Docker and Docker Compose v2 installed (Debian 12 / Ubuntu 22.04+ recommended)
- Domain + Traefik already configured for n8n SSL (or use the n8n cloud alternative)
- Google Cloud project with OAuth2 credentials (for Sheets + Gmail)
- Anthropic API key

Complete the [`prerequisites_checklist.md`](prerequisites_checklist.md) before starting.

---

### 3.2 VPS Setup

**Clone and configure:**

```bash
git clone <your-fork> vitamin-price-monitor
cd vitamin-price-monitor/competitor_price_monitor_n8n
cp config/.env.example config/.env
```

Edit `config/.env`:

```
N8N_HOST=n8n.your-domain.com
TIMEZONE=America/New_York
N8N_ENCRYPTION_KEY=<generate with: openssl rand -hex 16>
ANTHROPIC_API_KEY=sk-ant-api03-...
VITAMIN_MONITOR_SHEET_ID=<your-google-sheet-id>
VITAMIN_MONITOR_RECIPIENT=you@email.com
```

**Configure Traefik labels (if using Traefik):**

In `config/docker-compose.yml`, uncomment the `labels:` block under the `n8n` service and replace `n8n.your-domain.com` with your actual hostname.

**Start services:**

```bash
docker compose -f config/docker-compose.yml up -d
```

This starts two containers:
- `n8n` — your workflow engine
- `scraper-api` — the Python FastAPI sidecar (only accessible internally via `http://scraper-api:8000`)

The first startup takes ~3 minutes while Playwright Chromium installs inside the scraper container.

**Verify scraper-api is healthy:**

```bash
docker compose -f config/docker-compose.yml exec n8n wget -qO- http://scraper-api:8000/health
# Expected: {"status":"ok","version":"1.0.0","playwright_available":true}
```

---

### 3.3 n8n Credential Setup

**Google Sheets OAuth2:**

1. In Google Cloud Console → APIs & Services → Credentials → Create OAuth 2.0 Client
2. Application type: Web application
3. Authorized redirect URI: `https://n8n.your-domain.com/rest/oauth2-credential/callback`
4. Copy Client ID and Client Secret
5. In n8n → Credentials → New → **Google Sheets OAuth2 API**
6. Paste credentials → Connect → sign in → Allow

**Gmail OAuth2:**

Use the same Client ID and Client Secret:

1. In n8n → Credentials → New → **Gmail OAuth2 API**
2. Paste same credentials → Connect → Allow

> Both Sheets and Gmail use the same OAuth client. One Google Cloud project, two n8n credentials.

---

### 3.4 Google Sheets Setup

1. Create a new Google Sheet
2. Create 4 tabs: `products`, `snapshots`, `changes`, `analysis`
3. Add column headers from `config/google_sheets_seed.md` to row 1 of each tab
4. Pre-fill the 5 Phase 1 seed rows into the `products` tab — `url`, `competitor_name`, `competitor_code`, `vitamin`, `vitamin_code` columns only. Leave everything else blank.

The onboarding workflow fills in all other fields automatically.

---

### 3.5 Workflow 1 — Vitamin Monitor Onboarding

**Purpose:** Auto-detect new rows in the products sheet (blank `product_id`) and populate all fields via the scraper-api.

**Trigger:** Schedule → Every 5 Minutes

---

**Node A1 — Schedule Trigger**
- Type: Schedule Trigger
- Interval: Every 5 minutes

---

**Node A2 — Read Products Sheet**
- Type: Google Sheets → Get All Rows
- Sheet: select your spreadsheet → `products` tab
- Add filter: `product_id` is empty

---

**Node A3 — IF New Rows**
- Type: IF
- Condition: `{{ $input.all().length > 0 }}`
- True branch continues; False branch ends workflow

---

**Node A4 — Loop Over Items**
- Type: Split In Batches
- Batch Size: 1

---

**Node A5 — Extract Domain**
- Type: Set
- Fields:
  - `url` = `{{ $json.url }}`
  - `domain` = `{{ new URL($json.url).hostname }}`
  - `path` = `{{ new URL($json.url).pathname }}`
  - `vitamin` = `{{ $json.vitamin }}`

---

**Node A6 — Fetch robots.txt**
- Type: HTTP Request
- Method: GET
- URL: `=https://{{ $json.domain }}/robots.txt`
- Options: Ignore HTTP errors (404 = crawling allowed by convention)

---

**Node A7 — Parse robots.txt**
- Type: Code (JavaScript)
- Code: paste contents of `scripts/n8n_parse_robots.js`
- Output: `{ scrape_allowed: "yes"|"no"|"unknown", matched_rule }`

---

**Node A8 — IF Scrape Allowed**
- Type: IF
- Condition: `{{ $json.scrape_allowed !== 'no' }}`

**False branch:**

**Node A9a — Update Sheet (Blocked)**
- Type: Google Sheets → Update Row
- Match on: `url`
- Set: `scrape_allowed=no`, `normalization_quality=unresolvable`, `date_added={{ new Date().toISOString().slice(0,10) }}`

**True branch:**

**Node A9b — Call Scraper API**
- Type: HTTP Request
- Method: POST
- URL: `={{ $env.SCRAPER_API_URL }}/scrape`
- Body (JSON):
  ```json
  {
    "url": "={{ $('Extract Domain').first().json.url }}",
    "allow_llm_fallback": true,
    "vitamin_hint": "={{ $('Extract Domain').first().json.vitamin }}"
  }
  ```
- Timeout: 60 seconds

---

**Node A10 — Parse Scraper Response**
- Type: Code (JavaScript)
- Code: paste contents of `scripts/n8n_parse_scraper_response.js`
- Computes: `cost_per_serving`, `cost_per_unit`, `normalization_quality`

---

**Node A11 — Generate product_id**
- Type: Code (JavaScript)
- Logic: build `{competitor_code}-{vitamin_code}-{timestamp_suffix}` from the original row data

```javascript
const row = $('Read Products Sheet').first().json;
const parsed = $input.first().json;
const seq = String(Date.now()).slice(-3);
const productId = `${row.competitor_code}-${row.vitamin_code}-${seq}`;
return [{ json: { ...parsed, product_id: productId } }];
```

---

**Node A12 — Update Products Sheet**
- Type: Google Sheets → Update Row
- Match on: `url`
- Columns to write: `product_id`, `product_name`, `servings_per_container`, `serving_size_raw`, `serving_size_value`, `serving_size_unit`, `availability`, `normalization_quality`, `scrape_allowed=yes`, `extraction_method`, `consecutive_errors=0`, `last_successful_scrape`, `date_added`

Connect A12 → A4 (loop back to next item).

---

### 3.6 Workflow 2 — Vitamin Monitor Daily Capture

**Purpose:** Scrape current prices for all active products and append to the `snapshots` tab. No LLM calls.

**Trigger:** Schedule → Cron `0 6 * * *` (daily 6:00 am)

---

**Node B1 — Schedule Trigger**
- Cron: `0 6 * * *`

**Node B2 — Set Run Date**
- Set field: `run_date` = `{{ new Date().toISOString().slice(0,10) }}`

**Node B3 — Read Active Products**
- Google Sheets → Get All Rows from `products`
- Filter: `scrape_allowed = yes` AND `normalization_quality != unresolvable`

**Node B4 — Loop Over Items** (Split In Batches, size 1)

**Node B5 — Call Scraper API**
- POST `{{ $env.SCRAPER_API_URL }}/scrape`
- Body: `{ url, product_id, requires_browser, allow_llm_fallback: false, vitamin_hint }`
- Note: `allow_llm_fallback` is explicitly `false` — daily monitoring never calls Haiku

**Node B6 — Parse Scraper Response**
- Code: paste `scripts/n8n_parse_scraper_response.js`

**Node B7 — IF Error**
- Condition: `{{ $json.scraper_error !== null }}`

**True branch (error):**

**Node B8a — Increment Error Counter**
- Google Sheets → Update Row, match on `product_id`
- Set `consecutive_errors` = `{{ parseInt($('Read Active Products').first().json.consecutive_errors || 0) + 1 }}`
- Loop back to B4

**False branch (success):**

**Node B8b — Append Snapshot**
- Google Sheets → Append Row to `snapshots` tab
- Columns: `snapshot_id`, `product_id`, `run_date`, `price`, `cost_per_serving`, `cost_per_unit`, `availability`, `normalization_quality`, `extraction_method`, `scraper_version`
- `snapshot_id` = `{{ $json.product_id + '_' + $('Set Run Date').first().json.run_date.replace(/-/g,'') }}`

**Node B9 — Update Product Meta**
- Google Sheets → Update Row, match on `product_id`
- Set: `extraction_method`, `consecutive_errors=0`, `last_successful_scrape={{ $('Set Run Date').first().json.run_date }}`
- Loop back to B4

---

### 3.7 Workflow 3 — Vitamin Monitor Weekly Analysis

**Purpose:** Aggregate 7 days of snapshots, detect price changes, call Claude Sonnet for trend analysis, send email digest.

**Trigger:** Schedule → Cron `0 7 * * 1` (Monday 7:00 am)

---

**Node W1 — Schedule Trigger** (Cron: `0 7 * * 1`)

**Node W2 — Set Run Start**
- Set fields:
  - `run_start` = `{{ new Date().toISOString() }}`
  - `seven_days_ago` = `{{ new Date(Date.now()-7*24*60*60*1000).toISOString().slice(0,10) }}`

**Node W3 — Read Products Sheet**
- Google Sheets → Get All from `products`
- Filter: `scrape_allowed=yes`, `normalization_quality != unresolvable`

**Node W4 — Read Snapshots**
- Google Sheets → Get All from `snapshots`
- Filter: `run_date >= {{ $('Set Run Start').first().json.seven_days_ago }}`

> Run W3 and W4 in parallel — connect both from W2. Use a Merge node (Append mode) before W5,
> or configure W5 to read both by node name directly.

**Node W5 — Aggregate Snapshots**
- Code: paste `scripts/n8n_aggregate_snapshots.js`
- Reads W3 and W4 by node name
- Output: `{ products, summary_table_md, run_stats }`

**Node W6 — Detect Changes**
- Code: paste `scripts/n8n_detect_changes.js`
- Output: array of change objects, or `[{ no_changes: true }]` sentinel

**Node W7 — IF Any Changes**
- Condition: `{{ !$input.first().json.no_changes }}`
- False branch ends the workflow

**Node W8 — Build Claude Prompt**
- Type: Set
- Assemble `system_prompt` and `user_prompt` strings from `config/claude_analysis_prompt.md`
- Inject `summary_table_md` and `run_stats` from `$('Aggregate Snapshots').first().json`

**Node W9 — Call Claude Sonnet**
- HTTP Request → POST `https://api.anthropic.com/v1/messages`
- Headers: `x-api-key: {{ $env.ANTHROPIC_API_KEY }}`, `anthropic-version: 2023-06-01`
- Body:
  ```json
  {
    "model": "claude-sonnet-4-6",
    "max_tokens": 1500,
    "system": "={{ $json.system_prompt }}",
    "messages": [{ "role": "user", "content": "={{ $json.user_prompt }}" }]
  }
  ```

**Node W10 — Parse Claude Response**
- Code: paste `scripts/n8n_parse_analysis_response.js`
- Output: `{ executive_summary, significant_changes, cluster_analysis, watch_list, tokens_used }`

**Node W11 — Append Changes**
- Google Sheets → Append Rows to `changes` tab
- Input: `$('Detect Changes').all()` filtered by `!no_changes`
- Columns: `timestamp`, `product_id`, `competitor_name`, `vitamin`, `product_name`, `change_type`, `value_before`, `value_after`, `pct_delta`, `normalization_quality`

**Node W12 — Write Analysis Row**
- Google Sheets → Append Row to `analysis` tab
- Columns: `run_date`, `products_scraped`, `products_errored`, `changes_detected`, `claude_summary`, `claude_raw_json`, `tokens_used`

**Node W13 — Build Email Digest**
- Code: paste `scripts/n8n_build_email_digest.js`
- Also reads `$('Detect Changes')` and `$('Aggregate Snapshots')` by node name
- Output: `{ has_changes, subject, body_text, body_html }`

**Node W14 — IF Has Changes**
- Condition: `{{ $json.has_changes === true }}`

**Node W15 — Gmail Send Digest**
- Gmail node → Send Email
- To: `{{ $env.VITAMIN_MONITOR_RECIPIENT }}`
- Subject: `{{ $json.subject }}`
- HTML Body: `{{ $json.body_html }}`

---

## 4. Script Reference

### n8n Code Nodes

| Script | Used In | Purpose |
|--------|---------|---------|
| `n8n_parse_robots.js` | Workflow 1 — Node A7 | Parses raw robots.txt body; returns `scrape_allowed` (yes/no/unknown) and the matched rule |
| `n8n_parse_scraper_response.js` | Workflows 1 + 2 — Nodes A10, B6 | Validates scraper API output; computes `cost_per_serving`, `cost_per_unit`, `normalization_quality` (verified/partial/unresolvable) |
| `n8n_aggregate_snapshots.js` | Workflow 3 — Node W5 | Pivots 7 days of snapshot rows into a per-product history map; computes price deltas and generates `summary_table_md` |
| `n8n_detect_changes.js` | Workflow 3 — Node W6 | Compares Monday snapshot to previous Monday; emits change records for any delta ≥ 0.1%; returns `no_changes` sentinel if clean |
| `n8n_parse_analysis_response.js` | Workflow 3 — Node W10 | Strips markdown code fences from Claude response; parses JSON; validates required fields (`executive_summary`, `significant_changes`, `watch_list`) |
| `n8n_build_email_digest.js` | Workflow 3 — Node W13 | Formats plain text + HTML email body; sections: executive summary, significant changes, other changes, competitive position, watch list, data quality footer |

### Python Scraper Sidecar

| Script | Role |
|--------|------|
| `py_scraper_api.py` | FastAPI app — exposes `/health`, `/scrape`, `/robots` endpoints; env-based config |
| `py_scraper_cascade.py` | Core extraction logic — 4-tier cascade (JSON-LD → meta tags → Supplement Facts → Haiku fallback); rate-limits to 5 s/domain |
| `py_scraper_models.py` | Pydantic request/response schemas — `ScrapeRequest`, `ScrapeResponse`, `RobotsRequest`, `HealthResponse` |
| `robots_txt_checker.py` | CLI utility — pre-flight crawl permission check for a list of URLs; run before adding new competitor domains |

### Extraction Cascade (py_scraper_cascade.py)

```
Input: url, allows_browser, allow_llm_fallback, vitamin_hint

TIER 1 — JSON-LD (schema.org Product)
  Parse <script type="application/ld+json">
  Extract: price, availability, product_name
  → If price found: success, tier=1

TIER 2 — Meta Tags (fallback if Tier 1 has no price)
  Check og:title, product:price:amount, twitter:data1
  → If price found: success, tier=2

TIER 3 — Supplement Facts table (always runs)
  Parse <table>/<div>/<section> containing "supplement facts"
  Extract: servings_per_container, serving_size_value, serving_size_unit
  → Contributes to response regardless of price success

TIER 4 — Claude Haiku fallback (onboarding only, gated)
  Only if price=null AND allow_llm_fallback=true
  Sends first 4,000 chars of page text to Haiku
  → tier=4, flagged for manual review

Response fields:
  price, servings_per_container, serving_size_value,
  extraction_method, extraction_tier (1–4, 0 = error),
  confidence (high/low), error, scraper_version
```

---

## 5. Google Sheets Reference

Full column definitions are in `config/google_sheets_seed.md`. The summary below covers key fields per tab.

### Tab: products

| Column | Type | Description |
|--------|------|-------------|
| `url` | Text | Competitor product page URL — the unique identifier for onboarding |
| `product_id` | Text | Auto-generated: `{competitor_code}-{vitamin_code}-{seq}` — blank until onboarding runs |
| `competitor_name` | Text | Human-readable brand name (e.g., "NOW Foods") |
| `competitor_code` | Text | Short code used in product_id (e.g., "NOW") |
| `vitamin` | Text | Full vitamin name (e.g., "Vitamin D3") |
| `vitamin_code` | Text | Short code (e.g., "D3") |
| `price` | Number | Last known retail price (USD) |
| `cost_per_serving` | Number | `price / servings_per_container` |
| `servings_per_container` | Number | From Supplement Facts table |
| `normalization_quality` | Text | `verified` / `partial` / `unresolvable` |
| `scrape_allowed` | Text | `yes` / `no` / `unknown` |
| `requires_browser` | Boolean | TRUE = use Playwright (Chromium), FALSE = httpx (static) |
| `consecutive_errors` | Number | Incremented on each scrape failure; reset to 0 on success |
| `last_successful_scrape` | Date | ISO date of last clean snapshot |

### Tab: snapshots

| Column | Description |
|--------|-------------|
| `snapshot_id` | `{product_id}_{YYYYMMDD}` |
| `product_id` | Foreign key to products tab |
| `run_date` | ISO date (YYYY-MM-DD) |
| `price` | Scraped price at this date |
| `cost_per_serving` | Computed at capture time |
| `availability` | `in_stock` / `out_of_stock` / `unknown` |
| `extraction_method` | `json_ld` / `meta_tags` / `table_parse` / `haiku_fallback` |

### Tab: changes

Each row is a detected price or availability event ≥ 0.1% delta. Key columns: `change_type`, `value_before`, `value_after`, `pct_delta`, `timestamp`.

### Tab: analysis

One row per weekly run. Key columns: `run_date`, `products_scraped`, `changes_detected`, `claude_summary` (plain text), `claude_raw_json`, `tokens_used`.

### Suggested Views

- **Price Leaders:** filter `products` by `normalization_quality=verified`, sort by `cost_per_serving` ascending
- **Error Watch:** filter `products` by `consecutive_errors >= 3` to find products needing attention
- **Recent Changes:** filter `changes` by `timestamp >= [date]`, sort by `pct_delta` descending
- **Cost Trend:** filter `snapshots` by `product_id`, sort by `run_date` — chart `cost_per_serving` over time

---

## 6. Testing Procedures

### 6.1 Test the Scraper Directly

From the VPS (or via Docker exec):

```bash
# Health check
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status":"ok","version":"1.0.0","playwright_available":true}

# Scrape test (NOW Foods D3 5000 IU)
curl -s -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.nowfoods.com/products/supplements/vitamin-d3-5000-iu-softgels", "vitamin_hint": "Vitamin D3", "allow_llm_fallback": false}' \
  | python3 -m json.tool
# Expected: price != null, extraction_tier 1 or 2, error: null
```

### 6.2 Sample Test Cases

**Test Case 1 — Standard Product (Tier 1 extraction)**
- URL: `https://www.nowfoods.com/products/supplements/vitamin-d3-1000-iu-softgels`
- Expected: `extraction_tier: 1`, `confidence: high`, `price` populated, `servings_per_container` populated
- Onboarding result: `normalization_quality: verified`

**Test Case 2 — Bot-Protected Site (Playwright required)**
- Initial scrape returns: `extraction_tier: 0`, `error: "bot_protection_detected"` or empty price
- Action: set `requires_browser = TRUE` on the products row
- Retry: re-trigger onboarding by clearing `product_id` on that row
- Expected after Playwright: `extraction_tier: 1` or `2`, `confidence: high`

**Test Case 3 — No JSON-LD (Tier 3 extraction)**
- Some smaller brands serve price only in plain HTML
- Expected: `extraction_tier: 3`, `servings_per_container` populated from Supplement Facts, but price may be null
- Result: `normalization_quality: partial` — check the URL manually and consider enabling `allow_llm_fallback`

### 6.3 Verification Checklist

**Scraper service:**
- [ ] `/health` returns `playwright_available: true`
- [ ] Test curl for at least one NOW Foods URL returns `price != null`

**Workflow 1 (Onboarding):**
- [ ] Seed row added to `products` tab with URL + metadata, blank `product_id`
- [ ] Workflow triggered (manually or wait 5 min)
- [ ] `product_id` is now populated in that row
- [ ] `normalization_quality` is `verified` or `partial` (not blank)
- [ ] `cost_per_serving` is populated for verified products

**Workflow 2 (Daily Capture):**
- [ ] Workflow triggered manually from n8n UI
- [ ] `snapshots` tab has new rows (one per active product)
- [ ] `last_successful_scrape` updated on products rows
- [ ] `consecutive_errors` is 0 for all successful products

**Workflow 3 (Weekly Analysis):**
- [ ] At least 2 days of snapshots exist in the `snapshots` tab
- [ ] Workflow triggered manually
- [ ] `changes` tab has rows (if price differences detected)
- [ ] `analysis` tab has a new row with `claude_summary` populated
- [ ] Weekly digest email received at `VITAMIN_MONITOR_RECIPIENT`

---

## 7. Troubleshooting

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Onboarding workflow never fires | Schedule Trigger not activated | Activate the workflow in the n8n UI (toggle switch) |
| `product_id` blank after 10+ min | scraper-api not reachable from n8n | Run `docker compose ps` — confirm `scraper-api` is `Up`; check internal network name |
| `extraction_tier: 0`, `error: bot_protection_detected` | Site blocking plain httpx requests | Set `requires_browser=TRUE` on that row; Playwright bypasses basic JS gates |
| `extraction_tier: 3`, no price | JSON-LD and meta tags absent on this URL | Enable `allow_llm_fallback` for onboarding only; Haiku will extract if the price exists in plain text |
| `consecutive_errors` at 3+ for a product | URL changed or site temporarily down | Verify the URL is still valid; test directly via `curl -X POST /scrape`; check extraction tier |
| Weekly digest email not arriving | Gmail OAuth expired or workflow inactive | Re-authorize Gmail credential in n8n → Credentials; ensure Workflow 3 is activated |
| Claude Sonnet response not valid JSON | Claude wrapped response in markdown fences | `n8n_parse_analysis_response.js` strips code fences — check that script is pasted correctly |
| `snapshot_id` conflicts (duplicate rows) | Daily workflow triggered twice on same day | Safe to ignore — Append creates a new row; filter by distinct `snapshot_id` in downstream analysis |
| Workflow 3 ends at W7 (no changes) | All prices stable this week | Expected behavior — no email sent when `no_changes` sentinel fires |
| Playwright container slow (20–30s/URL) | Chromium cold start per request | Expected for `requires_browser=TRUE` products; consider async batching if scaling past 20 products |
| Google Sheets 429 (rate limit) | Too many API calls per second | Add a 1-second Wait node between B8b and B9 in Workflow 2 |

### Operational Notes

**Adding new products:**
Just add a row to the products sheet with `url`, `competitor_name`, `competitor_code`, `vitamin`, `vitamin_code`. Leave everything else blank. The onboarding workflow fills it in within 5 minutes.

**Handling bot protection:**
If scraper-api returns `error: "bot_protection_detected"`, set `requires_browser = TRUE` on that product row. The next run uses Playwright automatically. Expect ~10–30 s per URL vs ~2 s for static fetches.

**Watching consecutive_errors:**
If `consecutive_errors` reaches 3+ for a product, the URL may have changed or the site may be blocking. Test via direct curl to the scraper endpoint and re-add the row if the URL is permanently changed.

**Expanding to Phase 2 competitors (Vitamin Shoppe, GNC):**
1. Run `python scripts/robots_txt_checker.py` to check crawl permissions first
2. Add rows with `requires_browser=FALSE` initially
3. Monitor `extraction_method` and `consecutive_errors` after the first few daily runs
4. Flip `requires_browser=TRUE` if needed

---

## 8. Cost Analysis

### Development

All tools used in development are free tier or open source.

| Tool | Development Cost |
|------|----------------|
| n8n (self-hosted) | $0 |
| Python FastAPI + Playwright | $0 |
| Google Sheets | $0 |
| Google OAuth2 | $0 |
| Claude Haiku (onboarding fallback) | ~$0.001 per failed extraction |

### Production

| Item | Frequency | Cost |
|------|-----------|------|
| Daily scraping — 5 products | Daily, no LLM | $0.00 |
| Daily scraping — 27 products | Daily, no LLM | $0.00 |
| Claude Haiku fallback | Only on onboarding failures | ~$0.001/product |
| Claude Sonnet weekly analysis (Phase 1, 5 products) | 1× per week | ~$0.012 |
| Claude Sonnet weekly analysis (Phase 3, 27 products) | 1× per week | ~$0.034 |
| VPS (2 GB, shared) | Monthly | ~$6–12/month |
| **Phase 1 total (5 products, LLM only)** | Weekly | **< $0.02/week** |
| **Phase 3 total (27 products, LLM only)** | Weekly | **< $0.05/week** |

**Why weekly LLM costs are low:** Claude receives a pre-aggregated markdown table (~1,800–4,500 tokens), not raw HTML. The scraper handles all extraction programmatically — Claude only synthesizes the pre-computed delta table.

---

## 9. Customizing for Your Use Case

### 9.1 Adding New Competitors

1. Check `robots.txt` first: `python scripts/robots_txt_checker.py --inline '[{"url":"https://competitor.com/robots.txt"}]'`
2. Add rows to the `products` tab with `url`, `competitor_name`, `competitor_code`, `vitamin`, `vitamin_code`
3. Start with `requires_browser=FALSE` — switch to `TRUE` only if the first onboarding run fails
4. Monitor `extraction_method` to see which tier is working for the new domain

### 9.2 Adding New Vitamins

1. Add `vitamin` and `vitamin_code` values to the new product rows
2. The `vitamin_hint` field in the scraper request is a plain-text hint passed to Haiku fallback and Supplement Facts parsing — use a clear name (e.g., "Vitamin C", "Magnesium Glycinate")
3. No code changes required — the system handles any supplement

### 9.3 Scaling to Phase 2 / Phase 3

| Phase | Products | Action |
|-------|----------|--------|
| Phase 1 | 5 (NOW, LE, Thorne — D3 only) | Baseline — no changes needed |
| Phase 2 | ~15 (add Vitamin Shoppe, GNC) | Add rows; check robots.txt; monitor Playwright load |
| Phase 3 | ~27 (multi-vitamin coverage) | Consider adding a 1-second Wait node in Workflow 2 to avoid Sheets rate limits |

At Phase 3+ scale (27 products), daily scraping takes ~60–90 seconds for static pages and up to 15 minutes if all products require Playwright. Ensure the Workflow 2 schedule leaves enough lead time before Workflow 3.

### 9.4 Swapping the Storage Layer

The current design uses Google Sheets. To swap:

| Alternative | Change Required |
|-------------|----------------|
| PostgreSQL | Replace Google Sheets nodes with Postgres nodes (n8n native); keep same column schema |
| Airtable | Replace Sheets nodes with Airtable nodes; use Airtable field types (Number, Single Select) |
| Notion | Replace Sheets nodes with Notion database nodes; map to Notion property types |
| BigQuery | Use n8n HTTP Request to BigQuery API; best for Phase 3+ at high volume |

In all cases, the Python scraper and n8n Code nodes do not change — only the storage nodes swap.

### 9.5 Changing the Claude Model

The weekly analysis model is set in **Node W9** of Workflow 3. To change:

1. In n8n, open Workflow 3 → Node W9 (Call Claude Sonnet)
2. Update the `"model"` field in the request body
3. Also update the cost estimate comment in `config/claude_analysis_prompt.md`

Latest model IDs: Sonnet 4.6 (`claude-sonnet-4-6`), Haiku 4.5 (`claude-haiku-4-5-20251001`).

### 9.6 Adaptation Checklist

When adapting this project for a different product category or market:

- [ ] Update `vitamin_hint` values in product rows to match the new category
- [ ] Update `config/claude_analysis_prompt.md` system prompt to reflect the new domain context
- [ ] Update `competitor_code` and `competitor_name` values for new brands
- [ ] Re-run `scripts/robots_txt_checker.py` for all new domains
- [ ] Update `VITAMIN_MONITOR_RECIPIENT` in `.env` to the correct analyst email
- [ ] Review `n8n_detect_changes.js` threshold (currently 0.1%) — adjust for your category's typical price volatility
- [ ] Update `n8n_build_email_digest.js` subject line prefix to reflect the new category
- [ ] Review `config/google_sheets_seed.md` column names — rename vitamin-specific columns if needed
