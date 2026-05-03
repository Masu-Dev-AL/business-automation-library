# Interactive Build Prompt — Vitamin Price Monitor

**How to use:** Copy everything below the horizontal rule and paste it as your first message in a new Claude Desktop conversation. Claude will guide you through the build one step at a time.

---

I'm building the **Vitamin Price Monitor** project and need your help walking me through the setup step by step. Wait for me to confirm each step is done before moving to the next. If I run into an error, help me troubleshoot it before continuing.

---

## What This Project Does

Tracks competitor vitamin prices (NOW Foods, Life Extension, Thorne) daily. Normalizes everything to cost-per-serving. Delivers a weekly email digest with Claude AI trend analysis.

**Onboarding:** I add a URL to a Google Sheet → system auto-populates within 5 min  
**Daily 6am:** Scrape prices → append to snapshots tab (no LLM)  
**Monday 7am:** Aggregate 7-day data → Claude Sonnet analysis → email digest

---

## Architecture

```
n8n (orchestrator) ←→ scraper-api (Python FastAPI sidecar)
         ↓                        ↓
  Google Sheets          httpx + BeautifulSoup + Playwright
  Gmail                  Extraction cascade:
  Claude Sonnet            Tier 1: JSON-LD schema.org
    (weekly analysis)      Tier 2: Open Graph meta tags
                           Tier 3: Supplement Facts table
                           Tier 4: Claude Haiku (onboarding fallback)
```

Both services run in Docker Compose on the same VPS. n8n calls the scraper via `http://scraper-api:8000/scrape` — it never touches HTML itself.

---

## What's Already Built (code files are written)

All scripts are in the project repo at `competitor_price_monitor_n8n/`. Nothing needs to be coded — just deployed and configured.

**Python scraper service:**
- `scripts/py_scraper_api.py` — FastAPI app
- `scripts/py_scraper_cascade.py` — extraction cascade
- `scripts/py_scraper_models.py` — Pydantic models

**n8n Code node scripts (paste these into n8n):**
- `scripts/n8n_parse_robots.js`
- `scripts/n8n_parse_scraper_response.js`
- `scripts/n8n_aggregate_snapshots.js`
- `scripts/n8n_detect_changes.js`
- `scripts/n8n_parse_analysis_response.js`
- `scripts/n8n_build_email_digest.js`

**Config:**
- `config/docker-compose.yml` — service definitions
- `config/Dockerfile.scraper` — Python + Playwright image
- `config/.env.example` — credentials template
- `config/google_sheets_seed.md` — sheet schema + seed rows
- `config/claude_analysis_prompt.md` — Claude Sonnet prompt

---

## Build Phases (in order)

1. VPS — fix docker-compose.yml, bring n8n + scraper-api up
2. Google Sheets — create 4 tabs, add headers, add seed rows
3. n8n credentials — Google OAuth2 (Sheets + Gmail)
4. Workflow 1: Onboarding (every 5 min)
5. Workflow 2: Daily Capture (6am)
6. Workflow 3: Weekly Analysis (Monday 7am)
7. End-to-end test

---

## n8n Code Node Scripts (copy-paste ready)

### `n8n_parse_robots.js`
```javascript
const response = $input.first();
const statusCode = response.json?.statusCode ?? response.statusCode ?? 200;
const body = response.json?.body ?? response.body ?? '';

if (statusCode === 404) {
  return [{ json: { scrape_allowed: 'yes', matched_rule: 'no robots.txt found' } }];
}
if (statusCode >= 400) {
  return [{ json: { scrape_allowed: 'unknown', matched_rule: `http_error_${statusCode}` } }];
}

const robotsText = typeof body === 'string' ? body : JSON.stringify(body);
const userAgent = 'Mozilla/5.0';
let disallowedPaths = [];
let allowedPaths = [];
let inRelevantBlock = false;

for (const rawLine of robotsText.split('\n')) {
  const line = rawLine.trim();
  if (!line || line.startsWith('#')) continue;
  const [field, ...rest] = line.split(':');
  const key = field.trim().toLowerCase();
  const value = rest.join(':').trim();
  if (key === 'user-agent') {
    inRelevantBlock = ['*', userAgent.toLowerCase()].includes(value.toLowerCase());
  } else if (inRelevantBlock) {
    if (key === 'disallow' && value) disallowedPaths.push(value);
    if (key === 'allow' && value) allowedPaths.push(value);
  }
}

const productPath = $('Extract Domain').first()?.json?.path ?? '/';
for (const path of allowedPaths) {
  if (productPath.startsWith(path)) return [{ json: { scrape_allowed: 'yes', matched_rule: `Allow: ${path}` } }];
}
for (const path of disallowedPaths) {
  if (path === '/' || productPath.startsWith(path)) return [{ json: { scrape_allowed: 'no', matched_rule: `Disallow: ${path}` } }];
}
return [{ json: { scrape_allowed: 'yes', matched_rule: null } }];
```

---

### `n8n_parse_scraper_response.js`
```javascript
const response = $input.first().json;

if (response.error) {
  return [{ json: { ...response, normalization_quality: 'unresolvable', cost_per_serving: null, cost_per_unit: null, parse_error: false, scraper_error: response.error } }];
}

const price = response.price != null ? parseFloat(response.price) : null;
const servings = response.servings_per_container != null ? parseInt(response.servings_per_container, 10) : null;
const servingValue = response.serving_size_value != null ? parseFloat(response.serving_size_value) : null;

let normalizationQuality;
if (price !== null && servings !== null) normalizationQuality = 'verified';
else if (price !== null || servings !== null) normalizationQuality = 'partial';
else normalizationQuality = 'unresolvable';

const costPerServing = (price !== null && servings !== null && servings > 0)
  ? parseFloat((price / servings).toFixed(6)) : null;
const costPerUnit = (costPerServing !== null && servingValue !== null && servingValue > 0)
  ? parseFloat((price / (servings * servingValue)).toFixed(8)) : null;

return [{ json: {
  product_id: response.product_id, url: response.url, product_name: response.product_name,
  price, servings_per_container: servings, serving_size_raw: response.serving_size_raw,
  serving_size_value: servingValue, serving_size_unit: response.serving_size_unit,
  availability: response.availability || 'unknown', form: response.form,
  cost_per_serving: costPerServing, cost_per_unit: costPerUnit,
  normalization_quality: normalizationQuality, extraction_method: response.extraction_method,
  extraction_tier: response.extraction_tier, confidence: response.confidence,
  scraper_version: response.scraper_version, scraper_error: null, parse_error: false,
} }];
```

---

### `n8n_aggregate_snapshots.js`
```javascript
const products = $('Read Products Sheet').all().map(i => i.json);
const snapshots = $('Read Snapshots').all().map(i => i.json);

const snapshotsByProduct = {};
for (const snap of snapshots) {
  const pid = snap.product_id;
  if (!pid) continue;
  if (!snapshotsByProduct[pid]) snapshotsByProduct[pid] = [];
  snapshotsByProduct[pid].push({
    run_date: snap.run_date,
    price: snap.price != null ? parseFloat(snap.price) : null,
    cost_per_serving: snap.cost_per_serving != null ? parseFloat(snap.cost_per_serving) : null,
    availability: snap.availability || 'unknown',
    normalization_quality: snap.normalization_quality || 'unresolvable',
  });
}
for (const pid of Object.keys(snapshotsByProduct)) {
  snapshotsByProduct[pid].sort((a, b) => a.run_date.localeCompare(b.run_date));
}

const enrichedProducts = [];
for (const product of products) {
  const pid = product.product_id;
  if (!pid) continue;
  const history = snapshotsByProduct[pid] || [];
  const latest = history[history.length - 1] || null;
  const baseline = history[0] || null;
  let priceDeltaPct = null, cpsDeltaPct = null;
  if (latest?.price != null && baseline?.price != null && baseline.price > 0)
    priceDeltaPct = parseFloat(((latest.price - baseline.price) / baseline.price * 100).toFixed(2));
  if (latest?.cost_per_serving != null && baseline?.cost_per_serving != null && baseline.cost_per_serving > 0)
    cpsDeltaPct = parseFloat(((latest.cost_per_serving - baseline.cost_per_serving) / baseline.cost_per_serving * 100).toFixed(2));
  const snapshotsByDay = {};
  for (const snap of history) snapshotsByDay[snap.run_date] = snap;
  enrichedProducts.push({
    product_id: pid, competitor_name: product.competitor_name,
    vitamin: product.vitamin, vitamin_code: product.vitamin_code,
    product_name: product.product_name, normalization_quality: product.normalization_quality,
    snapshots_by_day: snapshotsByDay, days_with_data: history.length,
    price_latest: latest?.price ?? null, price_baseline: baseline?.price ?? null, price_delta_pct: priceDeltaPct,
    cps_latest: latest?.cost_per_serving ?? null, cps_baseline: baseline?.cost_per_serving ?? null, cps_delta_pct: cpsDeltaPct,
    latest_availability: latest?.availability ?? 'unknown', latest_date: latest?.run_date ?? null,
  });
}

const allDates = [...new Set(snapshots.map(s => s.run_date))].sort();
const dateHeaders = allDates.map(d => d.slice(5));
const headerRow = `| Product | ${dateHeaders.join(' | ')} | Δ% |`;
const separatorRow = `|---|${'---|'.repeat(dateHeaders.length + 1)}`;
const dataRows = enrichedProducts.map(p => {
  const cells = allDates.map(d => {
    const snap = p.snapshots_by_day[d];
    return (snap?.cost_per_serving != null) ? '$' + snap.cost_per_serving.toFixed(4) : '—';
  });
  const deltaStr = p.cps_delta_pct !== null ? (p.cps_delta_pct >= 0 ? '+' : '') + p.cps_delta_pct + '%' : '—';
  return `| ${p.competitor_name} ${p.vitamin_code} | ${cells.join(' | ')} | ${deltaStr} |`;
});
const summaryTableMd = [headerRow, separatorRow, ...dataRows].join('\n');

return [{ json: {
  products: enrichedProducts, summary_table_md: summaryTableMd, all_dates: allDates,
  run_stats: {
    total_products: enrichedProducts.length,
    products_with_data: enrichedProducts.filter(p => p.days_with_data > 0).length,
    products_with_change: enrichedProducts.filter(p => p.price_delta_pct !== null && Math.abs(p.price_delta_pct) >= 0.1).length,
    date_range_start: allDates[0] || null, date_range_end: allDates[allDates.length - 1] || null,
  },
} }];
```

---

### `n8n_detect_changes.js`
```javascript
const { products } = $input.first().json;
const now = new Date().toISOString();
const changes = [];

for (const p of products) {
  if (!p.product_id) continue;
  const base = { timestamp: now, product_id: p.product_id, competitor_name: p.competitor_name,
    vitamin: p.vitamin, product_name: p.product_name, normalization_quality: p.normalization_quality };

  if (p.price_latest !== null && p.price_baseline !== null && p.price_delta_pct !== null) {
    if (Math.abs(p.price_delta_pct) >= 0.1) {
      changes.push({ ...base, change_type: 'price_change',
        value_before: Number(p.price_baseline).toFixed(2), value_after: Number(p.price_latest).toFixed(2),
        pct_delta: p.price_delta_pct });
    }
  }
  if (p.cps_latest !== null && p.cps_baseline !== null && p.cps_delta_pct !== null && p.normalization_quality === 'verified') {
    if (Math.abs(p.cps_delta_pct) >= 0.1) {
      changes.push({ ...base, change_type: 'cost_per_serving_change',
        value_before: Number(p.cps_baseline).toFixed(4), value_after: Number(p.cps_latest).toFixed(4),
        pct_delta: p.cps_delta_pct });
    }
  }
  const snapDates = Object.keys(p.snapshots_by_day || {}).sort();
  if (snapDates.length >= 2) {
    const firstAvail = p.snapshots_by_day[snapDates[0]].availability;
    const lastAvail = p.snapshots_by_day[snapDates[snapDates.length - 1]].availability;
    if (firstAvail && lastAvail && firstAvail !== lastAvail)
      changes.push({ ...base, change_type: 'availability_change', value_before: firstAvail, value_after: lastAvail, pct_delta: null });
  }
}

if (changes.length === 0) return [{ json: { no_changes: true } }];
return changes.map(c => ({ json: c }));
```

---

### `n8n_parse_analysis_response.js`
```javascript
const response = $input.first().json;
let rawText = '';
try { rawText = response.content[0].text || ''; }
catch (e) {
  return [{ json: { parse_error: true, error_detail: 'No content in Claude response',
    executive_summary: 'Analysis unavailable — Claude response was empty.',
    significant_changes: [], cluster_analysis: [], watch_list: [],
    tokens_used: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0) } }];
}

rawText = rawText.replace(/^```json?\s*/m, '').replace(/\s*```$/m, '').trim();

let analysis;
try { analysis = JSON.parse(rawText); }
catch (e) {
  return [{ json: { parse_error: true, error_detail: `JSON parse failed: ${e.message}`,
    raw_response: rawText.slice(0, 500),
    executive_summary: 'Analysis unavailable — response could not be parsed.',
    significant_changes: [], cluster_analysis: [], watch_list: [],
    tokens_used: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0) } }];
}

return [{ json: {
  parse_error: false, error_detail: null,
  executive_summary: typeof analysis.executive_summary === 'string' ? analysis.executive_summary : 'No summary provided.',
  significant_changes: Array.isArray(analysis.significant_changes) ? analysis.significant_changes : [],
  cluster_analysis: Array.isArray(analysis.cluster_analysis) ? analysis.cluster_analysis : [],
  watch_list: Array.isArray(analysis.watch_list) ? analysis.watch_list : [],
  tokens_input: response.usage?.input_tokens || 0, tokens_output: response.usage?.output_tokens || 0,
  tokens_used: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0),
  claude_raw_json: JSON.stringify(analysis),
} }];
```

---

### `n8n_build_email_digest.js`
```javascript
const analysis = $input.first().json;
const rawChanges = $('Detect Changes').all().map(i => i.json);
const runStats = $('Aggregate Snapshots').first().json.run_stats || {};
const changes = rawChanges.filter(c => !c.no_changes);

if (changes.length === 0 && !analysis.significant_changes?.length) return [{ json: { has_changes: false } }];

const SEP = '━'.repeat(40);
const dateStr = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
const subject = `Vitamin Price Monitor — Week of ${dateStr}`;
const lines = [];

lines.push(`VITAMIN PRICE MONITOR — Week of ${dateStr}`, '');
if (analysis.executive_summary && !analysis.parse_error) {
  lines.push('EXECUTIVE SUMMARY', analysis.executive_summary, '');
}

const sigChanges = analysis.significant_changes || [];
if (sigChanges.length > 0) {
  lines.push(SEP, 'SIGNIFICANT CHANGES', SEP);
  for (const sc of sigChanges) {
    const rawMatch = changes.find(c => c.product_id === sc.product_id && c.change_type === 'cost_per_serving_change')
      || changes.find(c => c.product_id === sc.product_id && c.change_type === 'price_change');
    const label = `${rawMatch?.competitor_name || ''} — ${rawMatch?.product_name || sc.product_id}`.trim();
    lines.push(`  ${label}`);
    if (rawMatch?.change_type === 'cost_per_serving_change') {
      const dir = rawMatch.pct_delta >= 0 ? '+' : '';
      lines.push(`  Cost/serving: $${rawMatch.value_before} → $${rawMatch.value_after}  (${dir}${rawMatch.pct_delta.toFixed(1)}%)  ✓ verified`);
    } else if (rawMatch?.change_type === 'price_change') {
      const dir = rawMatch.pct_delta >= 0 ? '+' : '';
      lines.push(`  Price: $${rawMatch.value_before} → $${rawMatch.value_after}  (${dir}${rawMatch.pct_delta.toFixed(1)}%)`);
    }
    if (sc.insight) lines.push(`  Claude: "${sc.insight}"`);
    lines.push('');
  }
}

const highlightedIds = new Set(sigChanges.map(s => s.product_id));
const otherChanges = changes.filter(c => !highlightedIds.has(c.product_id));
if (otherChanges.length > 0) {
  lines.push(SEP, 'OTHER CHANGES', SEP);
  const byVitamin = {};
  for (const c of otherChanges) {
    if (!byVitamin[c.vitamin]) byVitamin[c.vitamin] = {};
    if (!byVitamin[c.vitamin][c.product_id]) byVitamin[c.vitamin][c.product_id] = { competitor: c.competitor_name, name: c.product_name, changes: [] };
    byVitamin[c.vitamin][c.product_id].changes.push(c);
  }
  for (const [vitamin, products] of Object.entries(byVitamin)) {
    lines.push(`  ${vitamin.toUpperCase()}`);
    for (const [, prod] of Object.entries(products)) {
      lines.push(`    ${prod.competitor} — ${prod.name}`);
      for (const c of prod.changes) {
        if (c.change_type === 'cost_per_serving_change') lines.push(`    Cost/serving: $${c.value_before} → $${c.value_after}  (${(c.pct_delta >= 0 ? '+' : '') + c.pct_delta.toFixed(1)}%)  ✓`);
        else if (c.change_type === 'price_change') lines.push(`    Price: $${c.value_before} → $${c.value_after}  (${(c.pct_delta >= 0 ? '+' : '') + c.pct_delta.toFixed(1)}%)`);
        else if (c.change_type === 'availability_change') lines.push(`    Availability: ${c.value_before} → ${c.value_after}`);
      }
    }
    lines.push('');
  }
}

const clusterAnalysis = analysis.cluster_analysis || [];
if (clusterAnalysis.length > 0) {
  lines.push(SEP, 'COMPETITIVE POSITION', SEP);
  for (const ca of clusterAnalysis) {
    const gap = ca.gap_to_next_pct != null ? `  (+${ca.gap_to_next_pct}% vs next)` : '';
    lines.push(`  ${ca.vitamin}   Cheapest: ${ca.cheapest_product_id}  $${Number(ca.cost_per_serving).toFixed(4)}/serving${gap}`);
  }
  lines.push('');
}

const watchList = analysis.watch_list || [];
if (watchList.length > 0) {
  lines.push(SEP, 'WATCH LIST', SEP);
  for (const w of watchList) lines.push(`  ⚠ ${w.product_id}: ${w.reason}`);
  lines.push('');
}

lines.push(SEP, 'DATA QUALITY', SEP);
lines.push(`  ${runStats.products_with_data || '?'}/${runStats.total_products || '?'} products scraped. ${analysis.tokens_used ? analysis.tokens_used + ' tokens used.' : ''}`);

const body_text = lines.join('\n');
const body_html = `<pre style="font-family:monospace;font-size:13px;line-height:1.6;">${body_text}</pre>`;
return [{ json: { has_changes: true, subject, body_text, body_html } }];
```

---

## Claude Sonnet Analysis Prompt

**System prompt** (paste into the "System" field of the HTTP Request body):
```
You are a pricing analyst for a supplement business. You receive weekly cost-per-serving data for competitor vitamin products, normalized to the same unit. Your job is to identify what is strategically significant — not just report every number change. Return ONLY valid JSON matching the schema provided. No explanations outside the JSON.
```

**User prompt** (build dynamically in n8n Set node, then reference as `{{ $json.user_prompt }}`):
```
Analyze this week's vitamin competitor pricing data.

DATE RANGE: {{ date_range_start }} to {{ date_range_end }}
PRODUCTS TRACKED: {{ total_products }}

COST-PER-SERVING TABLE:
{{ summary_table_md }}

Return a JSON object:
{
  "executive_summary": "<2-3 sentence plain-English summary>",
  "significant_changes": [{ "product_id": "", "change_type": "price_drop|price_increase|availability_change|competitive_shift", "insight": "<why it matters>" }],
  "cluster_analysis": [{ "vitamin": "", "cheapest_product_id": "", "cost_per_serving": 0.0, "gap_to_next_pct": 0.0 }],
  "watch_list": [{ "product_id": "", "reason": "" }]
}

Rules: significant_changes only if >= 5% OR strategically notable. cluster_analysis: one entry per vitamin. watch_list: flag data quality issues or anomalies. Empty arrays if nothing to report.
```

---

## Google Sheets — Tab & Column Reference

**Tab: `products`**
```
product_id | url | competitor_name | competitor_code | vitamin | vitamin_code | product_name | form | variant_notes | servings_per_container | serving_size_raw | serving_size_value | primary_unit | normalization_quality | availability | scrape_allowed | requires_browser | extraction_method | consecutive_errors | last_successful_scrape | date_added | added_by
```

**Tab: `snapshots`**
```
snapshot_id | product_id | run_date | price | cost_per_serving | cost_per_unit | availability | normalization_quality | extraction_method | scraper_version
```

**Tab: `changes`**
```
timestamp | product_id | competitor_name | vitamin | product_name | change_type | value_before | value_after | pct_delta | normalization_quality
```

**Tab: `analysis`**
```
run_date | products_scraped | products_errored | changes_detected | claude_summary | claude_raw_json | tokens_used | run_duration_seconds
```

---

## Phase 1 Seed Rows (paste into `products` tab — fill these columns only, leave the rest blank)

| url | competitor_name | competitor_code | vitamin | vitamin_code | form | requires_browser | date_added | added_by |
|---|---|---|---|---|---|---|---|---|
| https://www.nowfoods.com/products/supplements/vitamin-d3-1000-iu-softgels | NOW Foods | NOW | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.nowfoods.com/products/supplements/vitamin-d3-5000-iu-softgels | NOW Foods | NOW | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.lifeextension.com/vitamins-supplements/item01751/vitamin-d3 | Life Extension | LE | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.lifeextension.com/vitamins-supplements/item01718/vitamin-d3 | Life Extension | LE | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.thorne.com/products/dp/vitamin-d3 | Thorne | THRN | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |

---

## VPS Details

- Host: Hostinger VPS
- n8n URL: https://n8n.srv1164193.hstgr.cloud
- Current issue: docker-compose.yml is broken from a failed Trafilatura experiment — n8n is currently down. Needs to be replaced with the new `config/docker-compose.yml`.
- Traefik is already configured at host level for SSL.

---

## Key Environment Variables (set in `config/.env`)

```
N8N_HOST=n8n.srv1164193.hstgr.cloud
TIMEZONE=America/New_York
N8N_ENCRYPTION_KEY=<your existing key or generate new>
ANTHROPIC_API_KEY=sk-ant-api03-...
VITAMIN_MONITOR_SHEET_ID=<from your Google Sheet URL>
VITAMIN_MONITOR_RECIPIENT=masaunnelson@gmail.com
```

---

## Start

I'm ready to begin. Start me at **Phase 1: VPS Setup**. Tell me exactly what to do first.
