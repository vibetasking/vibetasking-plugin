---
name: google-chat
description: Google Chat messaging through the composio CLI. Resolving a human space
  name to its spaces/{id} resource name, the create_message payload shape and its
  32k byte text limit, replying inside an existing thread with thread_name, starting
  an agent on a space's new messages with a poll, and the --account selector for workspaces
  with more than one Google Chat integration
---

# Google Chat (GoogleChatComposioToolkit)

The CLI name is `composio google_chat`. These shapes are complete: call them
as written. For any other action, `composio google_chat <action> --help`
shows its parameters.

## Resolving a space name to its resource name

An action that targets a space takes its `spaces/{id}` resource name, never
the display name a user gives you ("Admin", "Marketing", "Facturación"). List
spaces once and match the display name client-side instead of guessing an id:

```bash
composio google_chat list_spaces --json '{"page_size": 1000}' > spaces.json
```

`page_size` defaults to 100 and caps at 1000, so take the whole list in one
call rather than paginating a small workspace. Grep or `jq` the saved file for
the display name rather than re-listing to apply a filter you can already
apply locally.

## Sending a message

```bash
jq -n --arg parent "spaces/AAAAAAAAAAA" --arg text "..." '{parent: $parent, text: $text}' > message.json
composio google_chat create_message --json-file message.json
```

- `parent` is the `spaces/{id}` resource name from `list_spaces`, not the
  bare id and not the display name.
- `text` is capped at 32,000 bytes.

`create_message`'s response is the created message itself, `name`,
`createTime` and `text` included, so it already confirms the send. Reach for
`list_messages` (`parent`, the space resource name) or `get_message` (`name`,
the full `spaces/{id}/messages/{id}` resource name the send returned) only
when a caller specifically needs to re-read a prior message, not as a default
verification step after every send.

## Replying in a thread

A reply lands under the message it answers when `create_message` names that
message's thread by its resource name, the `thread.name` every message
`list_messages` returns carries:

```bash
jq -n --arg parent "spaces/AAAAAAAAAAA" --arg thread "spaces/AAAAAAAAAAA/threads/BBBBBBBBBBB" --arg text "..." \
  '{parent: $parent, thread_name: $thread, text: $text}' > reply.json
composio google_chat create_message --json-file reply.json
```

- `thread_name` reaches any thread of the space, one a person started
  included. `thread_key` names only a thread this integration started under
  that same key, and any other key starts a new thread.
- When the thread is not found the reply fails instead of posting a new
  message in the space. `message_reply_option`
  `REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD` posts it as a new message then.
- The answer is the created message, its `thread.name` and
  `threadReply: true` included.

## Starting an agent on new messages

Google Chat publishes no event for a new message, so a poll trigger watches
a space instead (**Triggers** in the `vibetasking` skill): its `cron`
checks the space, and each message newer than the last one taken starts a
run, the message as its payload. The account the integration connects must
be a member of the space.

```json
{
  "agent_id": "<agent>",
  "integration_id": "<google chat integration>",
  "cron": "* * * * *",
  "poll": {
    "tool": "GOOGLE_CHAT_LIST_MESSAGES",
    "arguments": {"parent": "spaces/AAAAAAAAAAA", "orderBy": "create_time desc", "page_size": 100},
    "items": "messages",
    "id": "name",
    "time": "createTime",
    "filter": "'users/123' in (item.annotations or []) | selectattr('type', 'equalto', 'USER_MENTION') | map(attribute='userMention.user.name') | list"
  },
  "prompt": "Answer the message in its thread."
}
```

- The filter keeps the messages that mention one user, here `users/123`.
  `item.sender.name == 'users/123'` keeps one person's messages instead,
  as in a direct message space. Without a filter every new message starts
  a run.
- `list_members` on the space gives each person's `users/{id}`.
- The payload is the message whole: reply with its `thread.name` as
  `thread_name` to answer in its thread.

## Multiple integrations

When the workspace has more than one Google Chat integration, pass
`--account <id>` to pick which one a call runs against. Omit it when only one
is connected.
