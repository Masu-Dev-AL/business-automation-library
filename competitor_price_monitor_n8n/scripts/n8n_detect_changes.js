// n8n Code node — Detect Price Changes
// Runs in the Weekly Analysis workflow after n8n_aggregate_snapshots.js.
//
// Input:  one item from Aggregate Snapshots node (products array with 7-day history)
// Output: array of change records — one item per detected change across all products
//         Returns empty array if no changes detected (triggers IF node downstream).

const { products } = $input.first().json;
const now = new Date().toISOString();
const changes = [];

for (const p of products) {
  if (!p.product_id) continue;

  const base = {
    timestamp: now,
    product_id: p.product_id,
    competitor_name: p.competitor_name,
    vitamin: p.vitamin,
    product_name: p.product_name,
    normalization_quality: p.normalization_quality,
  };

  // Price change — threshold 0.1% to filter floating-point noise
  if (p.price_latest !== null && p.price_baseline !== null && p.price_delta_pct !== null) {
    if (Math.abs(p.price_delta_pct) >= 0.1) {
      changes.push({
        ...base,
        change_type: 'price_change',
        value_before: Number(p.price_baseline).toFixed(2),
        value_after: Number(p.price_latest).toFixed(2),
        pct_delta: p.price_delta_pct,
      });
    }
  }

  // Cost-per-serving change — verified quality only, threshold 0.1%
  if (
    p.cps_latest !== null &&
    p.cps_baseline !== null &&
    p.cps_delta_pct !== null &&
    p.normalization_quality === 'verified'
  ) {
    if (Math.abs(p.cps_delta_pct) >= 0.1) {
      changes.push({
        ...base,
        change_type: 'cost_per_serving_change',
        value_before: Number(p.cps_baseline).toFixed(4),
        value_after: Number(p.cps_latest).toFixed(4),
        pct_delta: p.cps_delta_pct,
      });
    }
  }

  // Availability change — compare oldest vs latest snapshot in the 7-day window
  const snapDates = Object.keys(p.snapshots_by_day || {}).sort();
  if (snapDates.length >= 2) {
    const firstAvail = p.snapshots_by_day[snapDates[0]].availability;
    const lastAvail = p.snapshots_by_day[snapDates[snapDates.length - 1]].availability;
    if (firstAvail && lastAvail && firstAvail !== lastAvail) {
      changes.push({
        ...base,
        change_type: 'availability_change',
        value_before: firstAvail,
        value_after: lastAvail,
        pct_delta: null,
      });
    }
  }
}

// Return one item per change; or a single no-changes sentinel so the IF node works
if (changes.length === 0) {
  return [{ json: { no_changes: true } }];
}

return changes.map(c => ({ json: c }));
