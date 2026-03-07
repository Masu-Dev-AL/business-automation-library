# Build Log — Support Ticket Automation (Pipedream + Claude AI)

This file is a running issue tracker maintained during the build of this project.
Every issue reported here is reviewed and resolved in the technical guide to ensure
the guide is **proven build-ready** as of the video release date.

---

## How to Report an Issue

When you hit a problem during the build, add a row to the **Open Issues** table below with:

| Field | What to write |
|---|---|
| **#** | Next sequential number |
| **Date** | YYYY-MM-DD |
| **Section** | The technical guide section where the issue occurred (e.g. `3.2`, `3.6 Step 3`) |
| **Issue** | One-line description of what went wrong |
| **Error / Detail** | Paste the exact error message or describe the unexpected behavior |

Leave **Resolution** and **Guide Updated** blank — those get filled in when the issue is fixed.

---

## Open Issues

| # | Date | Section | Issue | Error / Detail | Resolution | Guide Updated |
|---|------|---------|-------|----------------|-----------|---------------|
| 1 | 2026-03-03 | 3.6 Step 3 | All steps from `classify_ticket` onward fail if environment variables aren't set first | Steps 3–5 depend on `ANTHROPIC_API_KEY`, `DATABASE_URL`, Slack webhooks, and SendGrid key. Building steps before setting env vars causes immediate test failures. | Move Section 3.7 (Environment Variables) to before Section 3.6 (Building the Workflow) so all credentials are in place before any step is tested. | No |
| 2 | 2026-03-04 | 6.2 | Easy to accidentally omit `POST` after `-X` in curl command | Running `curl -X https://...` instead of `curl -X POST https://...` throws `curl: (2) no URL specified` | Added warning callout in section 6.2 explaining that `-X` takes the method as its argument, not the URL. | Yes |
| 3 | 2026-03-04 | 3.6 Step 1 & Step 2 | Switched trigger from HTTP to Email for better demo/video experience | Email trigger field paths differ from assumed structure. Actual paths: name → `headers.from.text` (parsed), email → `headers["return-path"].value[0].address`, subject → `headers.subject`, body → `body.text` | Updated `pd_normalize_ticket.py` to read from correct header paths. Updated Step 1 in guide to use Email trigger. Added section 3.8 on connecting a real support email via forwarding. | Yes |

---

## Resolved Issues

| # | Date | Section | Issue | Resolution | Guide Updated |
|---|------|---------|-------|-----------|---------------|
| — | — | — | — | — | — |

---

## Build Notes

General observations during the build that are not bugs but worth documenting
(e.g. UI differences from guide, optional steps, tips discovered during testing).

| # | Date | Section | Note |
|---|------|---------|------|
| — | — | — | — |

---

*Last updated: 2026-03-04*
