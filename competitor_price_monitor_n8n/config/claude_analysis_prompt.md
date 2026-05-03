# Claude Sonnet — Weekly Price Analysis Prompt

Used in the **Weekly Analysis** n8n workflow. Claude receives a pre-computed
data table (not raw HTML) and returns structured JSON for the email digest.

---

## System Prompt

```
You are a pricing analyst for a supplement business. You receive weekly
cost-per-serving data for competitor vitamin products, normalized to the
same unit (e.g. all Vitamin D3 compared in $/IU or $/serving).

Your job is to identify what is strategically significant — not just report
every number change. Focus on: meaningful price movements, competitive
position shifts, coordinated competitor behavior, and data reliability issues.

Return ONLY valid JSON matching the exact schema provided. No explanations
outside the JSON.
```

---

## User Prompt Template

Built dynamically in n8n before calling the API. Variables in `{{ }}` are
substituted by the n8n Code node prior to this HTTP Request.

```
Analyze this week's vitamin competitor pricing data.

DATE RANGE: {{ date_range_start }} to {{ date_range_end }}
PRODUCTS TRACKED: {{ total_products }}

COST-PER-SERVING TABLE (7-day history):
{{ summary_table_md }}

Return a JSON object with this exact structure:
{
  "executive_summary": "<2-3 sentence plain-English summary of the most important findings>",
  "significant_changes": [
    {
      "product_id": "<id>",
      "change_type": "price_drop|price_increase|availability_change|competitive_shift",
      "insight": "<one sentence explaining WHY this matters, not just WHAT changed>"
    }
  ],
  "cluster_analysis": [
    {
      "vitamin": "<vitamin name>",
      "cheapest_product_id": "<product_id>",
      "cost_per_serving": <float>,
      "gap_to_next_pct": <float or null>
    }
  ],
  "watch_list": [
    {
      "product_id": "<id>",
      "reason": "<brief reason — e.g. 'out of stock 4 of 7 days' or 'price seems anomalously low'>"
    }
  ]
}

Rules:
- significant_changes: only include changes >= 5% OR strategically notable (e.g. new cheapest option)
- cluster_analysis: one entry per vitamin type tracked
- watch_list: flag data quality issues, unusual volatility, persistent stockouts
- If no significant changes: set significant_changes to []
- If no watch items: set watch_list to []
```

---

## n8n HTTP Request Node Settings

| Field | Value |
|---|---|
| Method | POST |
| URL | `https://api.anthropic.com/v1/messages` |
| Auth | Header Auth — `x-api-key: {{ $env.ANTHROPIC_API_KEY }}` |
| Header | `anthropic-version: 2023-06-01` |
| Header | `content-type: application/json` |

### Request Body (JSON)

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 1500,
  "system": "{{ system_prompt }}",
  "messages": [
    {
      "role": "user",
      "content": "{{ user_prompt }}"
    }
  ]
}
```

---

## Expected Response Schema

```json
{
  "executive_summary": "NOW Foods dropped Vitamin D3 5000 IU by 28% — now the cheapest D3 option by a significant margin. Life Extension held steady across all products.",
  "significant_changes": [
    {
      "product_id": "NOW-D3-001",
      "change_type": "price_drop",
      "insight": "NOW Foods is now 31% cheaper than Thorne for equivalent D3 — a likely promotional push."
    }
  ],
  "cluster_analysis": [
    {
      "vitamin": "Vitamin D3",
      "cheapest_product_id": "NOW-D3-001",
      "cost_per_serving": 0.0281,
      "gap_to_next_pct": 31.2
    }
  ],
  "watch_list": [
    {
      "product_id": "LE-D3-002",
      "reason": "Out of stock 3 of 7 days this week"
    }
  ]
}
```

---

## Cost Estimate

| Phase | Input tokens | Output tokens | Cost |
|---|---|---|---|
| Phase 1 (5 products) | ~1,800 | ~600 | ~$0.012/week |
| Phase 3 (27 products) | ~4,500 | ~1,000 | ~$0.034/week |

Model pricing: claude-sonnet-4-6 at standard rates.
