# Google Sheets Setup

## Tab 1: `products` — Column Headers

```
product_id | url | competitor_name | competitor_code | vitamin | vitamin_code | product_name | form | variant_notes | servings_per_container | serving_size_raw | serving_size_value | primary_unit | normalization_quality | availability | scrape_allowed | requires_browser | extraction_method | consecutive_errors | last_successful_scrape | date_added | added_by
```

### Column Reference

| Column | Description |
|---|---|
| `product_id` | Auto-generated on onboarding. Format: `{COMP}-{VIT}-{SEQ}` (e.g. `NOW-D3-001`) |
| `url` | Full product page URL — the only field the user fills in to start onboarding |
| `competitor_name` | Human-readable name (e.g. "NOW Foods") |
| `competitor_code` | Short code (see reference below) |
| `vitamin` | Full vitamin name (e.g. "Vitamin D3") |
| `vitamin_code` | Short code (see reference below) |
| `product_name` | Scraped from page — auto-filled on onboarding |
| `form` | softgel, capsule, tablet, gummy, liquid, powder, other |
| `variant_notes` | Free text — e.g. "subscribe & save only" |
| `servings_per_container` | Extracted from Supplement Facts table on onboarding |
| `serving_size_raw` | Raw serving size text — e.g. "1 Softgel" |
| `serving_size_value` | Active vitamin dose amount — e.g. 5000 (for 5000 IU D3) |
| `primary_unit` | IU, mcg, mg — unit for cost-per-unit normalization |
| `normalization_quality` | verified / partial / unresolvable — see below |
| `availability` | in_stock / out_of_stock / limited / unknown |
| `scrape_allowed` | yes / no / unknown — set from robots.txt check on onboarding |
| `requires_browser` | TRUE if site requires JS rendering (Playwright); FALSE otherwise |
| `extraction_method` | json_ld / meta_tags / table_parse / haiku_fallback — last successful tier |
| `consecutive_errors` | Counter — incremented on each scrape failure; reset to 0 on success |
| `last_successful_scrape` | ISO date of last successful price extraction |
| `date_added` | ISO date row was added |
| `added_by` | "initial" for seed rows; user name or "system" for auto-onboarded rows |

**Note:** `price`, `cost_per_serving`, `cost_per_unit`, and `last_checked` have been moved to the `snapshots` tab. The products tab is now the product registry only — time-series data lives in snapshots.

**Normalization Quality:**
- `verified` — both price and servings_per_container present; cost-per-serving is reliable
- `partial` — one of price or servings is missing; included in digest but flagged
- `unresolvable` — neither could be extracted; excluded from monitoring

---

## Tab 2: `snapshots` — Column Headers (NEW)

```
snapshot_id | product_id | run_date | price | cost_per_serving | cost_per_unit | availability | normalization_quality | extraction_method | scraper_version
```

**Append-only.** One row per product per daily run. Never updated after writing.

| Column | Description |
|---|---|
| `snapshot_id` | `{product_id}_{YYYYMMDD}` — unique per (product, day) |
| `product_id` | Foreign key to products tab |
| `run_date` | ISO date — e.g. `2026-04-30` |
| `price` | Current price in USD |
| `cost_per_serving` | `price / servings_per_container` — blank if normalization_quality = unresolvable |
| `cost_per_unit` | `price / (servings * serving_size_value)` — blank if serving_size_value missing |
| `availability` | in_stock / out_of_stock / limited / unknown |
| `normalization_quality` | verified / partial / unresolvable |
| `extraction_method` | Which tier produced the price on this run |
| `scraper_version` | Scraper service version string |

---

## Tab 3: `changes` — Column Headers (unchanged)

```
timestamp | product_id | competitor_name | vitamin | product_name | change_type | value_before | value_after | pct_delta | normalization_quality
```

Written to by the Weekly Analysis workflow after comparing the latest snapshot to the week-ago baseline.

| `change_type` values | Description |
|---|---|
| `price_change` | Raw price moved >= 0.1% |
| `cost_per_serving_change` | Normalized cost moved >= 0.1% (verified quality only) |
| `availability_change` | Stock status changed between first and last snapshot in the window |

---

## Tab 4: `analysis` — Column Headers (NEW)

```
run_date | products_scraped | products_errored | changes_detected | claude_summary | claude_raw_json | tokens_used | run_duration_seconds
```

One row per weekly analysis run. Stores the full Claude JSON response for auditing.

---

## Phase 1 Seed Rows (products tab)

To onboard: add these rows to the products sheet with **only** the columns below filled in.
Leave everything else blank — the onboarding workflow fills it in automatically within 5 minutes.

| url | competitor_name | competitor_code | vitamin | vitamin_code | form | requires_browser | date_added | added_by |
|---|---|---|---|---|---|---|---|---|
| https://www.nowfoods.com/products/supplements/vitamin-d3-1000-iu-softgels | NOW Foods | NOW | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.nowfoods.com/products/supplements/vitamin-d3-5000-iu-softgels | NOW Foods | NOW | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.lifeextension.com/vitamins-supplements/item01751/vitamin-d3 | Life Extension | LE | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.lifeextension.com/vitamins-supplements/item01718/vitamin-d3 | Life Extension | LE | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |
| https://www.thorne.com/products/dp/vitamin-d3 | Thorne | THRN | Vitamin D3 | D3 | softgel | FALSE | 2026-04-30 | initial |

---

## Competitor & Vitamin Code Reference

### Competitor Codes
| Name | Code |
|---|---|
| NOW Foods | NOW |
| Life Extension | LE |
| Thorne | THRN |
| Vitamin Shoppe | VS |
| GNC | GNC |

### Vitamin Codes
| Vitamin | Code | Primary Unit |
|---|---|---|
| Vitamin D3 | D3 | IU |
| Vitamin C | C | mg |
| Vitamin B12 | B12 | mcg |
| Vitamin B Complex | BCOM | mg (B1 anchor) |
| Vitamin A | A | IU |
| Vitamin E | E | IU |
| Vitamin K2 | K2 | mcg |
| Folate / B9 | FOL | mcg DFE |
| Biotin / B7 | BIO | mcg |

### product_id Format
`[COMPETITOR_CODE]-[VITAMIN_CODE]-[SEQ]`
Examples: `NOW-D3-001`, `THRN-B12-001`, `LE-C-003`
