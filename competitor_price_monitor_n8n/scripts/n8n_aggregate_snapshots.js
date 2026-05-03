// n8n Code node — Aggregate Snapshots for Weekly Analysis
// Runs in the Weekly Analysis workflow after reading the products sheet
// and the last-7-days slice of the snapshots sheet.
//
// Input (from two preceding nodes, accessed via node name):
//   $('Read Products Sheet').all()   — product registry
//   $('Read Snapshots').all()        — snapshot rows (last 7 days)
//
// Output: one item containing:
//   products         — enriched product list with 7-day history attached
//   summary_table_md — markdown table for Claude prompt
//   run_stats        — counts for the analysis tab

const products = $('Read Products Sheet').all().map(i => i.json);
const snapshots = $('Read Snapshots').all().map(i => i.json);

// Index snapshots by product_id → sorted array of {run_date, price, cost_per_serving, availability}
const snapshotsByProduct = {};
for (const snap of snapshots) {
  const pid = snap.product_id;
  if (!pid) continue;
  if (!snapshotsByProduct[pid]) snapshotsByProduct[pid] = [];
  snapshotsByProduct[pid].push({
    run_date: snap.run_date,
    price: snap.price != null ? parseFloat(snap.price) : null,
    cost_per_serving: snap.cost_per_serving != null ? parseFloat(snap.cost_per_serving) : null,
    availability: snap.availability || "unknown",
    normalization_quality: snap.normalization_quality || "unresolvable",
  });
}

// Sort each product's snapshots chronologically
for (const pid of Object.keys(snapshotsByProduct)) {
  snapshotsByProduct[pid].sort((a, b) => a.run_date.localeCompare(b.run_date));
}

// Enrich products with their snapshot history and computed deltas
const enrichedProducts = [];
for (const product of products) {
  const pid = product.product_id;
  if (!pid) continue;

  const history = snapshotsByProduct[pid] || [];
  const latest = history[history.length - 1] || null;
  const baseline = history[0] || null;  // oldest in 7-day window = comparison point

  let priceLatest = latest?.price ?? null;
  let priceBaseline = baseline?.price ?? null;
  let priceDeltaPct = null;
  if (priceLatest !== null && priceBaseline !== null && priceBaseline > 0) {
    priceDeltaPct = parseFloat(((priceLatest - priceBaseline) / priceBaseline * 100).toFixed(2));
  }

  let cpsLatest = latest?.cost_per_serving ?? null;
  let cpsBaseline = baseline?.cost_per_serving ?? null;
  let cpsDeltaPct = null;
  if (cpsLatest !== null && cpsBaseline !== null && cpsBaseline > 0) {
    cpsDeltaPct = parseFloat(((cpsLatest - cpsBaseline) / cpsBaseline * 100).toFixed(2));
  }

  // Build snapshots_by_day map for the table
  const snapshotsByDay = {};
  for (const snap of history) {
    snapshotsByDay[snap.run_date] = snap;
  }

  enrichedProducts.push({
    product_id: pid,
    competitor_name: product.competitor_name,
    vitamin: product.vitamin,
    vitamin_code: product.vitamin_code,
    product_name: product.product_name,
    normalization_quality: product.normalization_quality,
    snapshots_by_day: snapshotsByDay,
    days_with_data: history.length,
    price_latest: priceLatest,
    price_baseline: priceBaseline,
    price_delta_pct: priceDeltaPct,
    cps_latest: cpsLatest,
    cps_baseline: cpsBaseline,
    cps_delta_pct: cpsDeltaPct,
    latest_availability: latest?.availability ?? "unknown",
    latest_date: latest?.run_date ?? null,
  });
}

// Collect all unique run dates in the window (for table columns)
const allDates = [...new Set(snapshots.map(s => s.run_date))].sort();
const dateHeaders = allDates.map(d => d.slice(5));  // MM-DD for column headers

// Build markdown summary table (cost_per_serving, formatted as $X.XXXX)
const headerRow = `| Product | ${dateHeaders.join(' | ')} | Δ% |`;
const separatorRow = `|---|${'---|'.repeat(dateHeaders.length + 1)}`;
const dataRows = enrichedProducts.map(p => {
  const cells = allDates.map(d => {
    const snap = p.snapshots_by_day[d];
    if (!snap || snap.cost_per_serving === null) return '—';
    return '$' + snap.cost_per_serving.toFixed(4);
  });
  const deltaStr = p.cps_delta_pct !== null
    ? (p.cps_delta_pct >= 0 ? '+' : '') + p.cps_delta_pct + '%'
    : '—';
  const label = `${p.competitor_name} ${p.vitamin_code}`;
  return `| ${label} | ${cells.join(' | ')} | ${deltaStr} |`;
});

const summaryTableMd = [headerRow, separatorRow, ...dataRows].join('\n');

// Run stats
const totalProducts = enrichedProducts.length;
const productsWithData = enrichedProducts.filter(p => p.days_with_data > 0).length;
const productsWithChange = enrichedProducts.filter(
  p => p.price_delta_pct !== null && Math.abs(p.price_delta_pct) >= 0.1
).length;

return [{
  json: {
    products: enrichedProducts,
    summary_table_md: summaryTableMd,
    all_dates: allDates,
    run_stats: {
      total_products: totalProducts,
      products_with_data: productsWithData,
      products_with_change: productsWithChange,
      date_range_start: allDates[0] || null,
      date_range_end: allDates[allDates.length - 1] || null,
    },
  }
}];
