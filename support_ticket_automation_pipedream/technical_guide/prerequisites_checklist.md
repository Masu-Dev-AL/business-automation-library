# Prerequisites Checklist

## Before You Build

---

### Pipedream Account
- [ ] Sign up at pipedream.com (free)
- [ ] Create a new project: `support-ticket-automation`

---

### Neon PostgreSQL
- [ ] Sign up at neon.tech (free)
- [ ] Create a new project: `support-tickets`
- [ ] Run `sql/schema.sql` in the Neon SQL Editor
- [ ] Copy the connection string (`postgresql://...?sslmode=require`)

---

### Anthropic API Key
- [ ] Sign up at console.anthropic.com
- [ ] Create an API key named `support-ticket-automation`
- [ ] Copy the key (`sk-ant-...`)

---

### Slack Workspace
- [ ] Create four channels: `#support-billing` `#support-technical` `#support-shipping` `#support-general`
- [ ] Create a Slack App: `Support Ticket Router` at api.slack.com/apps
- [ ] Enable Incoming Webhooks
- [ ] Add a webhook for each channel (4 total)
- [ ] Copy all four webhook URLs

---

### SendGrid Account
- [ ] Sign up at sendgrid.com (free)
- [ ] Complete Single Sender Verification for your from address
- [ ] Create an API key with Mail Send permissions
- [ ] Copy the API key (`SG....`) — only shown once
