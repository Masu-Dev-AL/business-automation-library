# pd_normalize_ticket.py
# Pipedream Step 2 — Normalize raw email trigger payload into a structured ticket object
#
# Input:  pd.steps["trigger"]["event"] (Pipedream Email trigger)
# Output: normalized ticket dict with a generated ticket_id

import uuid
from datetime import datetime, timezone


def handler(pd: "pipedream"):
    event = pd.steps["trigger"]["event"]
    headers = event.get("headers", {})

    # Parse name and email from "John Smith <john@example.com>" format
    from_text = (headers.get("from", {}).get("text") or "")
    name = from_text.split(" <")[0].strip() if " <" in from_text else from_text.strip()

    # Extract email from from.value array, fall back to parsing from_text
    from_value = headers.get("from", {}).get("value", [{}])
    email = (from_value[0].get("address") if from_value else None) or ""
    if not email and " <" in from_text:
        email = from_text.split(" <")[1].rstrip(">").strip()

    # Generate a short, readable ticket ID
    ticket_id = "TKT-" + uuid.uuid4().hex[:8].upper()

    return {
        "ticket_id":   ticket_id,
        "name":        name,
        "email":       email.strip().lower(),
        "subject":     (headers.get("subject") or "").strip(),
        "body":        (event.get("body", {}).get("text") or "").strip(),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
