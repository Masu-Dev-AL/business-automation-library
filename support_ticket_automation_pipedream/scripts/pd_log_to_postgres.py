# pd_log_to_postgres.py
# Pipedream Step 5a — Insert the full ticket record into PostgreSQL
#
# Input:  pd.steps["normalize_ticket"]["$return_value"]
#         pd.steps["classify_ticket"]["$return_value"]
#         pd.steps["build_routing_decision"]["$return_value"]
# Output: {"db_id": int, "ticket_id": str}
#
# Packages: psycopg2-binary

import os
from datetime import datetime, timezone

import psycopg2


def handler(pd: "pipedream"):
    ticket         = pd.steps["normalize_ticket"]["$return_value"]
    classification = pd.steps["classify_ticket"]["$return_value"]
    routing        = pd.steps["build_routing_decision"]["$return_value"]

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur  = conn.cursor()

    cur.execute(
        """
        INSERT INTO tickets (
            ticket_id,
            submitter_name,
            submitter_email,
            subject,
            body,
            category,
            urgency,
            sentiment,
            sentiment_score,
            ai_reasoning,
            assigned_channel,
            response_time_hours,
            created_at,
            processed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            ticket["ticket_id"],
            ticket["name"],
            ticket["email"],
            ticket["subject"],
            ticket["body"],
            classification["category"],
            classification["urgency"],
            classification["sentiment"],
            classification["sentiment_score"],
            classification["reasoning"],
            routing["assigned_channel"],
            routing["response_time_hours"],
            ticket["received_at"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    row_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "db_id":     row_id,
        "ticket_id": ticket["ticket_id"],
    }
