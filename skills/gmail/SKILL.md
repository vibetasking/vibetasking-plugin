---
name: gmail
description: Known composio gmail action parameters, compose actions send to recipient_email
  and attach via files, and fetch_emails payload rules
---

# Gmail (GmailComposioToolkit)

The CLI name is `composio gmail`. Use `composio gmail <action> --help` for an
action's parameters before your first call to it.

## Known action names and parameters

- Fetching one message is `fetch_message_by_message_id` with `message_id`,
  not `id`.
- The four compose actions (`send_email`, `create_email_draft`,
  `update_draft`, `reply_to_thread`) send to `recipient_email`, not `to`.
  They attach local files via `files`, an array of sandbox-relative paths.
  This platform replaces composio's own `attachment` field with `files` in
  the schema, so trust what `--help` shows on these actions over composio's
  published docs.

## Fetching email

On `fetch_emails`, leave `include_payload` off unless you actually need the
full payload or attachments, and use `verbose: false` when you don't. The
first call in a run that passes `include_payload: true` is rejected with a
retry-able error asking you to confirm you need it. Passing it again on the
next call goes through.
