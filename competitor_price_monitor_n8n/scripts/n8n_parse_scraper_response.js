// n8n Code node — Parse Scraper API Response
// Runs after the "Call Scraper API" HTTP Request node in both the
// Onboarding and Daily Capture workflows.
//
// Input:  HTTP response from POST /scrape on scraper-api
// Output: validated fields + normalization_quality + cost metrics

const response = $input.first().json;

// If the scraper returned a network/fetch error, surface it cleanly
if (response.error) {
  return [{
    json: {
      ...response,
      normalization_quality: "unresolvable",
      cost_per_serving: null,
      cost_per_unit: null,
      parse_error: false,
      scraper_error: response.error,
    }
  }];
}

const price = response.price != null ? parseFloat(response.price) : null;
const servings = response.servings_per_container != null
  ? parseInt(response.servings_per_container, 10)
  : null;
const servingValue = response.serving_size_value != null
  ? parseFloat(response.serving_size_value)
  : null;

// Three-tier data quality
let normalizationQuality;
if (price !== null && servings !== null) {
  normalizationQuality = "verified";
} else if (price !== null || servings !== null) {
  normalizationQuality = "partial";
} else {
  normalizationQuality = "unresolvable";
}

// Cost metrics — only meaningful when both price and servings are present
const costPerServing = (price !== null && servings !== null && servings > 0)
  ? parseFloat((price / servings).toFixed(6))
  : null;

const costPerUnit = (costPerServing !== null && servingValue !== null && servingValue > 0)
  ? parseFloat((price / (servings * servingValue)).toFixed(8))
  : null;

return [{
  json: {
    product_id: response.product_id,
    url: response.url,
    product_name: response.product_name,
    price,
    servings_per_container: servings,
    serving_size_raw: response.serving_size_raw,
    serving_size_value: servingValue,
    serving_size_unit: response.serving_size_unit,
    availability: response.availability || "unknown",
    form: response.form,
    cost_per_serving: costPerServing,
    cost_per_unit: costPerUnit,
    normalization_quality: normalizationQuality,
    extraction_method: response.extraction_method,
    extraction_tier: response.extraction_tier,
    confidence: response.confidence,
    scraper_version: response.scraper_version,
    scraper_error: null,
    parse_error: false,
  }
}];
