// n8n Code node — Parse robots.txt
// Runs in the Onboarding workflow after fetching robots.txt via HTTP Request.
//
// Input:  HTTP response from GET {domain}/robots.txt
// Output: { scrape_allowed: "yes"|"no"|"unknown", matched_rule: string|null }
//
// Note: For accuracy the scraper-api's POST /robots endpoint is preferred.
// This Code node is a lightweight fallback for use directly in n8n without
// calling the sidecar (e.g. if the sidecar is temporarily unreachable).

const response = $input.first();
const statusCode = response.json?.statusCode ?? response.statusCode ?? 200;
const body = response.json?.body ?? response.body ?? '';

// 404 means no robots.txt — crawling is allowed by convention
if (statusCode === 404) {
  return [{ json: { scrape_allowed: 'yes', matched_rule: 'no robots.txt found' } }];
}

// Other HTTP errors — treat as unknown
if (statusCode >= 400) {
  return [{ json: { scrape_allowed: 'unknown', matched_rule: `http_error_${statusCode}` } }];
}

const robotsText = typeof body === 'string' ? body : JSON.stringify(body);
const userAgent = 'Mozilla/5.0';  // the agent used by the scraper

let currentAgents = [];
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
    currentAgents = [value.toLowerCase()];
    inRelevantBlock = currentAgents.includes('*') || currentAgents.includes(userAgent.toLowerCase());
  } else if (inRelevantBlock) {
    if (key === 'disallow' && value) disallowedPaths.push(value);
    if (key === 'allow' && value) allowedPaths.push(value);
  }
}

// Check product URL path — passed via $('Extract Domain').first().json.path
const productPath = $('Extract Domain').first()?.json?.path ?? '/';

// Allow rules take precedence over Disallow
for (const path of allowedPaths) {
  if (productPath.startsWith(path)) {
    return [{ json: { scrape_allowed: 'yes', matched_rule: `Allow: ${path}` } }];
  }
}

for (const path of disallowedPaths) {
  if (path === '/' || productPath.startsWith(path)) {
    return [{ json: { scrape_allowed: 'no', matched_rule: `Disallow: ${path}` } }];
  }
}

return [{ json: { scrape_allowed: 'yes', matched_rule: null } }];
