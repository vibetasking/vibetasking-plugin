---
name: gmail
description: Known composio gmail action parameters, compose actions send to recipient_email
  from the address the conversation reached or from_email, attach via files, and fetch_emails
  payload rules
---

# Gmail (GmailComposioToolkit)

The CLI name is `composio gmail`. Use `composio gmail <action> --help` for an
action's parameters before your first call to it.

## Known action names and parameters

- Fetching one message is `fetch_message_by_message_id --json '{"message_id": "<id>"}'`,
  not `id`.
- The compose actions (`send_email`, `create_email_draft`, `update_draft`,
  `reply_to_thread`) send to `recipient_email`, not `to`, as in
  `send_email --json '{"recipient_email": "<addr>", "subject": "<subject>", "body": "<text>", "files": ["<path>"]}'`.
  They attach local files via `files`, an array of sandbox-relative paths.
  This platform replaces composio's own `attachment` field with `files` in
  the schema, so trust what `--help` shows on these actions over composio's
  published docs. `forward_message` sends to `recipients`, a list.
- Answer a conversation inside its thread with `reply_to_thread` (or a draft
  with `create_email_draft` and its `thread_id`), never with `send_email`,
  which starts a new conversation.
- A reply, a forward and a draft in a thread go out from the address the
  conversation reached: a client who wrote to one of the account's "Send mail
  as" aliases gets the reply from that alias, with its own signature. A new
  message goes out from the account's default address. Name
  another address in `from_email` only when the person asks for one, as in
  `reply_to_thread --json '{"thread_id": "<thread id>", "recipient_email": "<addr>", "message_body": "<text>", "from_email": "<alias>"}'`.
  `list_send_as` lists the addresses the account sends as. The answer's
  `from` says which address the message went out from.
- Each message carries the sender's Gmail signature, added for you, so end
  the body with the closing and the name, never a signature written out by
  hand.
- Filters cannot be created or deleted here: Google requires the
  `gmail.settings.basic` scope, which this connection does not hold, so no
  filter action is offered. Write the rules as an Atom XML file the user
  imports in Gmail (Settings, Filters and Blocked Addresses, Import filters),
  or tell them the rule to set up in Gmail's settings.

## Fetching email

On `fetch_emails`, leave `include_payload` off unless you actually need the
full payload or attachments, and use `verbose: false` when you don't. The
first call in a run that passes `include_payload: true` is rejected with a
retry-able error asking you to confirm you need it. Passing it again on the
next call goes through.
