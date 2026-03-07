# pd_send_reply_email.py
# Pipedream Step 5c — Send an auto-reply acknowledgement to the ticket submitter via SendGrid
#
# Input:  pd.steps["normalize_ticket"]["$return_value"]
#         pd.steps["build_routing_decision"]["$return_value"]
# Output: {"status_code": int, "message_id": str, "recipient": str}
#
# Packages: requests

import os
import requests


SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def handler(pd: "pipedream"):
    ticket  = pd.steps["normalize_ticket"]["$return_value"]
    routing = pd.steps["build_routing_decision"]["$return_value"]

    response = requests.post(
        SENDGRID_API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}",
            "Content-Type":  "application/json",
        },
        json={
            "personalizations": [
                {
                    "to": [{"email": ticket["email"], "name": ticket["name"]}],
                }
            ],
            "from": {
                "email": os.environ["SENDGRID_FROM_EMAIL"],
                "name":  os.environ.get("SENDGRID_FROM_NAME", "Support Team"),
            },
            "subject": f"Re: {ticket['subject']} [{ticket['ticket_id']}]",
            "content": [
                {"type": "text/html", "value": routing["email_html"]}
            ],
        },
        timeout=10,
    )

    return {
        "status_code": response.status_code,
        "message_id":  response.headers.get("X-Message-Id", ""),
        "recipient":   ticket["email"],
    }
