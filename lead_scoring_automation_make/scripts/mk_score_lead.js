// Make.com — Module 3: Score Lead with Claude AI ("claude-haiku-4-5")
// Module type: Anthropic > Create a Message
//
// Sends lead data to Claude and returns an AI-generated score, priority tier,
// and reasoning. Uses the native Make Anthropic module — no HTTP config needed.
//
// MODULE SETTINGS:
// ┌─────────────────────────────────────────────────────────────────┐
// │ Connection:  Create via Anthropic API key                       │
// │ Model:       claude-haiku-4-5-20251001                          │
// │ Max tokens:  512                                                │
// │ Role:        user                                               │
// │ Content:     paste the prompt below                             │
// └─────────────────────────────────────────────────────────────────┘
//
// Replace {{2.variable}} placeholders with Make expressions from Module 2.
// ─────────────────────────────────────────────────────────────────────────────

const requestBody = {
  model: "claude-haiku-4-5-20251001",
  max_tokens: 512,
  messages: [
    {
      role: "user",
      content: `You are a B2B sales qualification assistant. Score the following lead and return a JSON object only — no explanation, no markdown, no code fences.

LEAD DETAILS:
- Name:         {{2.lead_name}}
- Company:      {{2.company}}
- Role:         {{2.role}}
- Company Size: {{2.company_size}}
- Budget Range: {{2.budget}}
- Challenge:    {{2.challenge}}

SCORING CRITERIA:

ICP Fit Score (1–10):
- 9–10: Decision maker (C-Suite, VP, Director) at 51+ person company with $5k+ budget
- 7–8:  Manager or Team Lead at 11–50 person company with $1k–$5k budget
- 5–6:  Individual contributor or small team with some budget signal
- 1–4:  No budget signal, very early stage, or unclear authority

Intent Score (1–10):
- 9–10: Describes a specific urgent problem, mentions current tool failures, or indicates active evaluation
- 7–8:  Clear pain point articulated with some urgency implied
- 5–6:  General interest, exploring options
- 1–4:  Vague inquiry with no clear problem stated

Priority Tier rules:
- "hot":  ICP Score >= 7 AND Intent Score >= 7
- "warm": ICP Score >= 5 AND Intent Score >= 5 (and not hot)
- "cold": everything else

Recommended Action:
- hot:  "Call within 2 hours"
- warm: "Send personalised follow-up within 24 hours"
- cold: "Add to nurture sequence"

Return ONLY this JSON (no other text):
{
  "icp_score": <number 1-10>,
  "intent_score": <number 1-10>,
  "priority_tier": "<hot|warm|cold>",
  "recommended_action": "<string>",
  "reasoning": "<2–3 sentences explaining the scores>"
}`
    }
  ]
};

// ─────────────────────────────────────────────────────────────────────────────
// PARSING THE RESPONSE:
// After this module, add a "JSON > Parse JSON" module to extract fields.
// The Claude response text is at: {{3.content[].text}} (native Anthropic module).
// Confirm the exact path by checking Module 3's output in a test run.
// Parse that string as JSON to access: icp_score, intent_score, priority_tier,
// recommended_action, and reasoning in downstream modules.
