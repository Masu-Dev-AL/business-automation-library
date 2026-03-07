# pd_build_routing_decision.py
# Pipedream Step 4 — Map AI classification to Slack channel, SLA target, and message payload
#
# Input:  pd.steps["normalize_ticket"]["$return_value"]
#         pd.steps["classify_ticket"]["$return_value"]
# Output: routing dict (slack_webhook_url, assigned_channel, response_time_hours,
#                       slack_text, email_html)

import os


# SLA targets by urgency override (takes precedence over category defaults)
URGENCY_SLA_HOURS = {
    "critical": 1,
    "high":     4,
    "medium":   8,
    "low":      24,
}

URGENCY_EMOJI = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
}

CHANNEL_CONFIG = {
    "billing": {
        "name":        "#support-billing",
        "webhook_env": "SLACK_WEBHOOK_BILLING",
    },
    "technical": {
        "name":        "#support-technical",
        "webhook_env": "SLACK_WEBHOOK_TECHNICAL",
    },
    "shipping": {
        "name":        "#support-shipping",
        "webhook_env": "SLACK_WEBHOOK_SHIPPING",
    },
    "general": {
        "name":        "#support-general",
        "webhook_env": "SLACK_WEBHOOK_GENERAL",
    },
}


def handler(pd: "pipedream"):
    ticket         = pd.steps["normalize_ticket"]["$return_value"]
    classification = pd.steps["classify_ticket"]["$return_value"]

    category = classification["category"]
    urgency  = classification["urgency"]

    channel   = CHANNEL_CONFIG.get(category, CHANNEL_CONFIG["general"])
    sla_hours = URGENCY_SLA_HOURS.get(urgency, 24)
    emoji     = URGENCY_EMOJI.get(urgency, "⚪")

    # ── Slack message ────────────────────────────────────────────────────────
    slack_text = (
        f"{emoji} *New Support Ticket* [{urgency.upper()}]\n\n"
        f"*Ticket ID:* `{ticket['ticket_id']}`\n"
        f"*From:* {ticket['name']} ({ticket['email']})\n"
        f"*Subject:* {ticket['subject']}\n"
        f"*Category:* {category.title()}\n"
        f"*Response Target:* {sla_hours} hour(s)\n"
        f"*Sentiment:* {classification['sentiment'].title()} "
        f"({classification['sentiment_score']:+.2f})\n\n"
        f"*AI Reasoning:* _{classification['reasoning']}_"
    )

    # ── Auto-reply email HTML ─────────────────────────────────────────────────
    email_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <p>Hi {ticket['name']},</p>
        <p>
          Thank you for reaching out. We have received your support request and assigned
          it ticket number <strong>{ticket['ticket_id']}</strong>.
        </p>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
          <tr style="background: #f5f5f5;">
            <td style="padding: 8px 12px; font-weight: bold;">Ticket ID</td>
            <td style="padding: 8px 12px;">{ticket['ticket_id']}</td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold;">Subject</td>
            <td style="padding: 8px 12px;">{ticket['subject']}</td>
          </tr>
          <tr style="background: #f5f5f5;">
            <td style="padding: 8px 12px; font-weight: bold;">Category</td>
            <td style="padding: 8px 12px;">{category.title()}</td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold;">Expected Response</td>
            <td style="padding: 8px 12px;">Within {sla_hours} hour(s)</td>
          </tr>
        </table>
        <p>
          Our {category} support team will review your request and respond within
          the timeframe above. If your issue is urgent, please reply to this email
          with <strong>URGENT</strong> in the subject line.
        </p>
        <p>Thank you for your patience.</p>
        <p>Best regards,<br/>Support Team</p>
      </body>
    </html>
    """

    return {
        "slack_webhook_url":  os.environ[channel["webhook_env"]],
        "assigned_channel":   channel["name"],
        "response_time_hours": sla_hours,
        "slack_text":         slack_text,
        "email_html":         email_html,
    }
