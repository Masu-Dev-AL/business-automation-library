# pd_post_to_slack.py
# Pipedream Step 5b — POST the routed ticket notification to the correct Slack channel
#
# Input:  pd.steps["build_routing_decision"]["$return_value"]
#         pd.steps["normalize_ticket"]["$return_value"]
# Output: {"status_code": int, "channel": str}
#
# Packages: requests

import requests


def handler(pd: "pipedream"):
    routing = pd.steps["build_routing_decision"]["$return_value"]
    ticket  = pd.steps["normalize_ticket"]["$return_value"]

    response = requests.post(
        routing["slack_webhook_url"],
        json={"text": routing["slack_text"]},
        timeout=10,
    )

    return {
        "status_code": response.status_code,
        "channel":     routing["assigned_channel"],
        "ticket_id":   ticket["ticket_id"],
    }
