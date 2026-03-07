# pd_classify_ticket.py
# Pipedream Step 3 — Call Claude API to classify ticket category, urgency, and sentiment
#
# Input:  pd.steps["normalize_ticket"]["$return_value"]
# Output: classification dict (category, urgency, sentiment, sentiment_score, reasoning)
#
# Packages: anthropic, pydantic

import os
import anthropic
from pydantic import BaseModel


class TicketClassification(BaseModel):
    category:        str    # billing | technical | shipping | general
    urgency:         str    # critical | high | medium | low
    sentiment:       str    # positive | neutral | negative
    sentiment_score: float  # -1.0 (most negative) to 1.0 (most positive)
    reasoning:       str    # one-sentence explanation of the classification


SYSTEM_PROMPT = """You are a support ticket classifier for a business.
Analyze the ticket subject and body, then return a JSON object with these exact fields:

- category: one of "billing", "technical", "shipping", "general"
  - billing: payments, invoices, refunds, subscriptions, pricing
  - technical: bugs, errors, integrations, API, product not working
  - shipping: delivery, tracking, returns, damaged goods
  - general: anything that doesn't fit the above categories

- urgency: one of "critical", "high", "medium", "low"
  - critical: system down, data loss, security breach, complete blocker
  - high: major feature broken, significant revenue impact, time-sensitive
  - medium: partial functionality affected, workaround exists
  - low: cosmetic issue, general question, nice-to-have

- sentiment: one of "positive", "neutral", "negative"
- sentiment_score: float from -1.0 (most negative) to 1.0 (most positive)
- reasoning: one sentence explaining why you chose this category and urgency"""


def handler(pd: "pipedream"):
    ticket = pd.steps["normalize_ticket"]["$return_value"]

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = f"""Please classify this support ticket.

Subject: {ticket["subject"]}

Body:
{ticket["body"]}"""

    response = client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_format=TicketClassification,
    )

    result = response.parsed_output

    return {
        "category":        result.category,
        "urgency":         result.urgency,
        "sentiment":       result.sentiment,
        "sentiment_score": result.sentiment_score,
        "reasoning":       result.reasoning,
    }
