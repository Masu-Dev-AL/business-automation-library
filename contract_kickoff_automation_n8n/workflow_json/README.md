# Workflow JSON

This folder holds the exported n8n workflow definitions once built.

## Expected Files

| File | Workflow | Description |
|------|----------|-------------|
| `contract-kickoff-main.json` | Workflow A | Main contract ingestion — DocuSign Connect webhook through kickoff email |
| `contract-kickoff-reprocess.json` | Workflow B | Manual reprocess — retry a failed or insufficient contract |

## How to Export from n8n

1. Open the workflow in n8n
2. Click the **...** menu (top right) → **Export**
3. Select **Download** to save the JSON file
4. Place the downloaded file in this folder

## How to Import into n8n

1. In n8n, click **+** (new workflow) → **Import from File**
2. Select the JSON file from this folder
3. Configure all credentials (see `../technical_guide/prerequisites_checklist.md`)
4. Set all environment variables (see `../config/.env.example`)
5. Activate the workflow

## Important

All credentials, API keys, and environment variables must be configured in n8n before activating either workflow. The workflow JSON does not contain secrets — only the structure.
