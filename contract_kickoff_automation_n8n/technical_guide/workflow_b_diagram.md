# Workflow B — Manual Reprocess

Manually triggered. Used when a contract was logged as `insufficient` or `failed` and needs to be retried — for example, after the client re-sends a text-based PDF or after correcting an extraction issue.

```mermaid
flowchart TD
    B1["🖱️ B1. Manual Trigger\nAccepts: contract_id · corrected PDF file path\nInput parameters set at trigger time"]
    B2["📊 B2. Read contracts sheet\nGoogle Sheets node\nLook up existing row by contract_id\nLoad original client fields"]
    B3["♻️ B3. Re-run extraction pipeline\nRe-enters at A4 (PDF → Text)\nSame logic: A4 → A5 → A6 → A7 → A8...\nOverwrites existing contracts row"]

    B1 --> B2 --> B3

    classDef trigger fill:#4CAF50,stroke:#2E7D32,color:white
    classDef node fill:#1565C0,stroke:#0D47A1,color:white

    class B1 trigger
    class B2,B3 node
```

## When to Use

| Scenario | Action |
|----------|--------|
| Client re-sent a text-based PDF after the original was a scanned image | Reprocess with corrected file path |
| Claude extraction failed due to malformed API response (transient error) | Retry with same contract |
| Contract had insufficient scope; client provided an amended version | Reprocess with new PDF |
| Asana project creation failed (API downtime) but extraction succeeded | Reprocess — Asana will be retried |

## Notes

- The reprocess workflow **overwrites** the existing row in the `contracts` tab — it does not append a new row.
- Task rows in the `tasks` tab are appended fresh — check for duplicate tasks in Asana if the project was partially created on the first run.
- The corrected PDF is read from a local file path on the n8n host — upload the PDF to the server before triggering.
