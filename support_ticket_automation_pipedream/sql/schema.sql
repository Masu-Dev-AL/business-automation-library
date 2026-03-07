-- ─────────────────────────────────────────────────────────────────────────────
-- Support Ticket Automation - PostgreSQL Schema
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tickets (
    id                   SERIAL PRIMARY KEY,
    ticket_id            VARCHAR(20)     UNIQUE NOT NULL,   -- e.g. TKT-00042
    submitter_name       VARCHAR(255),
    submitter_email      VARCHAR(255)    NOT NULL,
    subject              TEXT            NOT NULL,
    body                 TEXT            NOT NULL,

    -- AI classification output
    category             VARCHAR(50),    -- billing | technical | shipping | general
    urgency              VARCHAR(20),    -- critical | high | medium | low
    sentiment            VARCHAR(20),    -- positive | neutral | negative
    sentiment_score      DECIMAL(3,2),   -- -1.00 to 1.00
    ai_reasoning         TEXT,           -- Claude's one-line explanation

    -- Routing output
    assigned_channel     VARCHAR(100),   -- Slack channel name
    response_time_hours  INTEGER,        -- SLA target in hours

    -- Timestamps
    created_at           TIMESTAMP       DEFAULT NOW(),
    processed_at         TIMESTAMP
);

-- Index for fast lookups by email and category
CREATE INDEX IF NOT EXISTS idx_tickets_email    ON tickets (submitter_email);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets (category);
CREATE INDEX IF NOT EXISTS idx_tickets_urgency  ON tickets (urgency);
CREATE INDEX IF NOT EXISTS idx_tickets_created  ON tickets (created_at DESC);
