// Make.com — Module 7: Send Gmail Auto-Reply
// Module type: Gmail > Send an Email
//
// Sends a personalised acknowledgement email to every lead immediately
// after their Typeform submission is processed.
//
// HOW TO USE:
// 1. Add a "Gmail > Send an Email" module
// 2. Connect your Gmail account via OAuth (Make handles auth — no API key needed)
// 3. Map the fields below to the corresponding Make expressions
//
// MODULE FIELD MAPPINGS:
// ┌─────────────────┬────────────────────────────────────────────────┐
// │ To              │ {{2.lead_email}}                               │
// │ Subject         │ See SUBJECT below                              │
// │ Content         │ HTML (paste EMAIL_BODY below)                  │
// │ From name       │ Sales Team   (or your preferred sender name)   │
// └─────────────────┴────────────────────────────────────────────────┘
// ─────────────────────────────────────────────────────────────────────────────

const SUBJECT = `Thanks for reaching out, {{2.lead_name}} — we'll be in touch`;

// ── Email Body (HTML) ─────────────────────────────────────────────────────────
// Paste this into the "Content" field of the Gmail module in Make.
// All {{variable}} references are Make expressions from Module 2 (normalize).

const EMAIL_BODY = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body      { font-family: Arial, sans-serif; font-size: 15px; color: #1a1a1a; background: #f4f4f4; margin: 0; padding: 0; }
    .wrapper  { max-width: 600px; margin: 32px auto; background: #ffffff; border-radius: 8px; overflow: hidden; }
    .header   { background: #1a1a2e; padding: 32px 40px; }
    .header h1 { color: #ffffff; font-size: 22px; margin: 0; }
    .body     { padding: 32px 40px; }
    .body p   { line-height: 1.6; margin: 0 0 16px; }
    .highlight { background: #f0f4ff; border-left: 4px solid #4f46e5; padding: 16px 20px; border-radius: 4px; margin: 24px 0; }
    .footer   { padding: 24px 40px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #6b7280; }
  </style>
</head>
<body>
  <div class="wrapper">

    <div class="header">
      <h1>Thanks for getting in touch</h1>
    </div>

    <div class="body">
      <p>Hi {{2.lead_name}},</p>

      <p>
        Thanks for submitting your details — we've received your enquiry and a member
        of our team will be reaching out shortly.
      </p>

      <div class="highlight">
        <strong>Your submission summary:</strong><br /><br />
        🏢 <strong>Company:</strong> {{2.company}}<br />
        👤 <strong>Role:</strong> {{2.role}}<br />
        💰 <strong>Budget:</strong> {{2.budget}}<br />
        💬 <strong>Challenge:</strong> {{2.challenge}}
      </div>

      <p>
        In the meantime, feel free to reply to this email if you have any questions.
      </p>

      <p>
        Looking forward to connecting,<br />
        <strong>The Sales Team</strong>
      </p>
    </div>

    <div class="footer">
      You're receiving this email because you submitted a form on our website.
    </div>

  </div>
</body>
</html>
`.trim();
