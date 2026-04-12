// Make.com — Module 4: Build Routing Decision
// Module type: Tools > Set Multiple Variables
//
// Maps lead country → territory → Slack webhook + rep @mention.
// Also builds the full Slack message string using Claude's scoring output.
//
// HOW TO USE:
// 1. Add a "Tools > Set Multiple Variables" module after the JSON Parse module
// 2. Use Make's switch() function to implement the territory lookup
//    (see Make expressions at the bottom of this file)
// 3. The slack_message variable is used directly in the Slack HTTP module body
// ─────────────────────────────────────────────────────────────────────────────

// ── Territory Map ─────────────────────────────────────────────────────────────
// Maps each Typeform country dropdown value to a territory slug.
// Add or remove countries as needed — slugs must match TERRITORY_CONFIG keys.

const TERRITORY_MAP = {
  // North America
  "United States":  "north_america",
  "Canada":         "north_america",
  "Mexico":         "north_america",

  // Europe
  "United Kingdom": "europe",
  "Germany":        "europe",
  "France":         "europe",
  "Spain":          "europe",
  "Italy":          "europe",
  "Netherlands":    "europe",
  "Sweden":         "europe",
  "Norway":         "europe",
  "Denmark":        "europe",
  "Switzerland":    "europe",
  "Belgium":        "europe",
  "Austria":        "europe",
  "Portugal":       "europe",
  "Poland":         "europe",
  "Ireland":        "europe",
  "Finland":        "europe",

  // Asia-Pacific
  "India":          "asia",
  "Japan":          "asia",
  "China":          "asia",
  "Singapore":      "asia",
  "South Korea":    "asia",
  "Australia":      "asia",
  "New Zealand":    "asia",
  "Indonesia":      "asia",
  "Malaysia":       "asia",
  "Thailand":       "asia",
  "Philippines":    "asia",
  "Vietnam":        "asia",
  "Hong Kong":      "asia",
  "Taiwan":         "asia",
};

// ── Territory Config ──────────────────────────────────────────────────────────
// Stores the label, rep name, and Slack webhook env var per territory.
// Webhook URLs are stored as Make connections / environment variables.

// ── Rep handle note ───────────────────────────────────────────────────────────
// rep_handle uses plain text names by default (no real Slack accounts needed).
// To upgrade to real @mentions, replace each rep_handle value with the user's
// Slack member ID in the format <@U0123456789> (found in Slack profile → More → Copy member ID).

const TERRITORY_CONFIG = {
  north_america: {
    label:       "North America",
    rep_name:    "Sarah Mitchell",
    rep_handle:  "Sarah Mitchell",
    slack_env:   "SLACK_WEBHOOK_NORTH_AMERICA",
  },
  europe: {
    label:       "Europe",
    rep_name:    "James Hartley",
    rep_handle:  "James Hartley",
    slack_env:   "SLACK_WEBHOOK_EUROPE",
  },
  asia: {
    label:       "Asia-Pacific",
    rep_name:    "Priya Chen",
    rep_handle:  "Priya Chen",
    slack_env:   "SLACK_WEBHOOK_ASIA",
  },
  other: {
    label:       "Other",
    rep_name:    "Manager",
    rep_handle:  "Manager",
    slack_env:   "SLACK_WEBHOOK_GENERAL",
  },
};

// ── Priority Label ────────────────────────────────────────────────────────────

const PRIORITY_LABEL = {
  hot:  "🔥 HOT",
  warm: "🟡 WARM",
  cold: "🔵 COLD",
};

// ── Routing Logic ─────────────────────────────────────────────────────────────

const country       = "{{2.country}}";
const territory     = TERRITORY_MAP[country] || "other";
const config        = TERRITORY_CONFIG[territory];
const priority_tier = "{{4.priority_tier}}";   // from JSON Parse module (Module 4)

// Output variables to set in Make (Set Multiple Variables):
const territory_label  = config.label;          // e.g. "North America"
const rep_name         = config.rep_name;        // e.g. "Sarah Mitchell"
const rep_handle       = config.rep_handle;      // e.g. "@sarah.mitchell"
const priority_label   = PRIORITY_LABEL[priority_tier] || "🔵 COLD";

// ── Slack Message ─────────────────────────────────────────────────────────────
// Set this as a "slack_message" variable in Make.
// References variables from Module 2 (normalize) and Module 4 (JSON parse).

const slack_message = `
${rep_handle} — New lead assigned ${priority_label}

*{{2.company}}* | {{2.role}}
📍 {{2.country}} (${territory_label})
💰 Budget: {{2.budget}} | 👥 Size: {{2.company_size}}
💬 _"{{2.challenge}}"_

📊 ICP Score: {{4.icp_score}}/10 | Intent Score: {{4.intent_score}}/10
✅ {{4.recommended_action}}
`.trim();

// ─────────────────────────────────────────────────────────────────────────────
// MAKE EXPRESSIONS — copy these into your Set Multiple Variables module:
//
// territory_label:
//   {{switch(2.country; "United States"; "North America"; "Canada"; "North America";
//     "Mexico"; "North America"; "United Kingdom"; "Europe"; "Germany"; "Europe";
//     "France"; "Europe"; "India"; "Asia-Pacific"; "Japan"; "Asia-Pacific";
//     "Singapore"; "Asia-Pacific"; "Other")}}
//
// rep_handle (plain text — no real Slack accounts required):
//   {{switch(5.territory_label; "North America"; "Sarah Mitchell";
//     "Europe"; "James Hartley"; "Asia-Pacific"; "Priya Chen"; "Manager")}}
//
// To upgrade to real @mentions, replace each value with <@SLACK_MEMBER_ID>:
//   {{switch(5.territory_label; "North America"; "<@U0123456789>";
//     "Europe"; "<@U0123456790>"; "Asia-Pacific"; "<@U0123456791>"; "<@U0123456792>")}}
//
// priority_label:
//   {{switch(4.priority_tier; "hot"; "🔥 HOT"; "warm"; "🟡 WARM"; "🔵 COLD")}}
//
// slack_webhook_url:
//   {{switch(5.territory_label; "North America"; "<SLACK_WEBHOOK_NORTH_AMERICA>";
//     "Europe"; "<SLACK_WEBHOOK_EUROPE>"; "Asia-Pacific"; "<SLACK_WEBHOOK_ASIA>";
//     "<SLACK_WEBHOOK_GENERAL>")}}
