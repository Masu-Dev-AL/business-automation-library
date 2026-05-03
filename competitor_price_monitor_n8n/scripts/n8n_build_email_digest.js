// n8n Code node — Build Email Digest
// Runs after Parse Claude Response in the Weekly Analysis workflow.
//
// Input ($input):  Claude analysis from n8n_parse_analysis_response.js
// Also reads:      $('Detect Changes').all()        — raw change records
//                  $('Aggregate Snapshots').first()  — run stats
//
// Output: { has_changes, subject, body_text, body_html }

const analysis = $input.first().json;
const rawChanges = $('Detect Changes').all().map(i => i.json);
const runStats = $('Aggregate Snapshots').first().json.run_stats || {};

// Filter out the no_changes sentinel
const changes = rawChanges.filter(c => !c.no_changes);

if (changes.length === 0 && !analysis.significant_changes?.length) {
  return [{ json: { has_changes: false } }];
}

const SEP = '━'.repeat(40);
const dateStr = new Date().toLocaleDateString('en-US', {
  month: 'short', day: 'numeric', year: 'numeric'
});
const subject = `Vitamin Price Monitor — Week of ${dateStr}`;

const lines = [];

// ── Header ──
lines.push(`VITAMIN PRICE MONITOR — Week of ${dateStr}`);
lines.push('');

// ── Executive Summary (Claude narrative) ──
if (analysis.executive_summary && !analysis.parse_error) {
  lines.push('EXECUTIVE SUMMARY');
  lines.push(analysis.executive_summary);
  lines.push('');
}

// ── Significant Changes (Claude-highlighted, sorted by impact) ──
const sigChanges = analysis.significant_changes || [];
if (sigChanges.length > 0) {
  lines.push(SEP);
  lines.push('SIGNIFICANT CHANGES');
  lines.push(SEP);

  for (const sc of sigChanges) {
    // Find the matching raw change record for price values
    const rawMatch = changes.find(
      c => c.product_id === sc.product_id && c.change_type === 'cost_per_serving_change'
    ) || changes.find(
      c => c.product_id === sc.product_id && c.change_type === 'price_change'
    );

    const label = `${rawMatch?.competitor_name || ''} — ${rawMatch?.product_name || sc.product_id}`.trim();
    lines.push(`  ${label}`);

    if (rawMatch?.change_type === 'cost_per_serving_change') {
      const dir = rawMatch.pct_delta >= 0 ? '+' : '';
      lines.push(`  Cost/serving: $${rawMatch.value_before} → $${rawMatch.value_after}  (${dir}${rawMatch.pct_delta.toFixed(1)}%)  ✓ verified`);
    } else if (rawMatch?.change_type === 'price_change') {
      const dir = rawMatch.pct_delta >= 0 ? '+' : '';
      lines.push(`  Price: $${rawMatch.value_before} → $${rawMatch.value_after}  (${dir}${rawMatch.pct_delta.toFixed(1)}%)`);
    }

    if (sc.insight) {
      lines.push(`  Claude: "${sc.insight}"`);
    }
    lines.push('');
  }
}

// ── All Other Changes (data changes Claude didn't flag as significant) ──
const highlightedIds = new Set(sigChanges.map(s => s.product_id));
const otherChanges = changes.filter(c => !highlightedIds.has(c.product_id));

if (otherChanges.length > 0) {
  lines.push(SEP);
  lines.push('OTHER CHANGES');
  lines.push(SEP);

  const VITAMIN_ORDER = ['Vitamin D3', 'Vitamin C', 'Vitamin B12', 'Vitamin B Complex',
    'Vitamin A', 'Vitamin E', 'Vitamin K2', 'Folate / B9', 'Biotin / B7'];
  const byVitamin = {};
  for (const c of otherChanges) {
    if (!byVitamin[c.vitamin]) byVitamin[c.vitamin] = {};
    if (!byVitamin[c.vitamin][c.product_id]) {
      byVitamin[c.vitamin][c.product_id] = { competitor: c.competitor_name, name: c.product_name, changes: [] };
    }
    byVitamin[c.vitamin][c.product_id].changes.push(c);
  }

  const vitaminsWithChanges = [
    ...VITAMIN_ORDER.filter(v => byVitamin[v]),
    ...Object.keys(byVitamin).filter(v => !VITAMIN_ORDER.includes(v)),
  ];

  for (const vitamin of vitaminsWithChanges) {
    lines.push(`  ${vitamin.toUpperCase()}`);
    for (const [, prod] of Object.entries(byVitamin[vitamin])) {
      lines.push(`    ${prod.competitor} — ${prod.name}`);
      for (const c of prod.changes) {
        if (c.change_type === 'cost_per_serving_change') {
          const dir = c.pct_delta >= 0 ? '+' : '';
          lines.push(`    Cost/serving: $${c.value_before} → $${c.value_after}  (${dir}${c.pct_delta.toFixed(1)}%)  ✓`);
        } else if (c.change_type === 'price_change') {
          const dir = c.pct_delta >= 0 ? '+' : '';
          lines.push(`    Price: $${c.value_before} → $${c.value_after}  (${dir}${c.pct_delta.toFixed(1)}%)`);
        } else if (c.change_type === 'availability_change') {
          lines.push(`    Availability: ${c.value_before} → ${c.value_after}`);
        }
      }
    }
    lines.push('');
  }
}

// ── Competitive Position (from Claude cluster_analysis) ──
const clusterAnalysis = analysis.cluster_analysis || [];
if (clusterAnalysis.length > 0) {
  lines.push(SEP);
  lines.push('COMPETITIVE POSITION');
  lines.push(SEP);
  for (const ca of clusterAnalysis) {
    const gap = ca.gap_to_next_pct != null ? `  (+${ca.gap_to_next_pct}% vs next)` : '';
    lines.push(`  ${ca.vitamin}   Cheapest: ${ca.cheapest_product_id}  $${Number(ca.cost_per_serving).toFixed(4)}/serving${gap}`);
  }
  lines.push('');
}

// ── Watch List (Claude flags) ──
const watchList = analysis.watch_list || [];
if (watchList.length > 0) {
  lines.push(SEP);
  lines.push('WATCH LIST');
  lines.push(SEP);
  for (const w of watchList) {
    lines.push(`  ⚠ ${w.product_id}: ${w.reason}`);
  }
  lines.push('');
}

// ── Data Quality ──
lines.push(SEP);
lines.push('DATA QUALITY');
lines.push(SEP);
const scraped = runStats.products_with_data || '?';
const total = runStats.total_products || '?';
const errored = typeof runStats.products_with_data === 'number' && typeof runStats.total_products === 'number'
  ? runStats.total_products - runStats.products_with_data
  : '?';
lines.push(`  ${scraped}/${total} products scraped successfully. ${errored} errors.`);
if (analysis.tokens_used) {
  lines.push(`  Claude analysis: ${analysis.tokens_used} tokens used.`);
}

const body_text = lines.join('\n');
const body_html = `<pre style="font-family:monospace;font-size:13px;line-height:1.6;">${body_text}</pre>`;

return [{ json: { has_changes: true, subject, body_text, body_html } }];
