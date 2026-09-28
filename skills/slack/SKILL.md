---
name: slack
description: Known composio slack action names for user lookups, the obvious guesses
  are wrong
---

# Slack (SlackComposioToolkit)

The CLI name is `composio slack`. Use `composio slack <action> --help` for an
action's parameters before your first call to it.

## Known action names

Composio's action names don't match Slack's own API. Use the name on the
right, not the guess on the left:

- Finding a user by email is `find_user_by_email_address`, not
  `users_lookup_by_email`.
- There is no `search_user` action. For a name or handle search use
  `find_users`, or `list_all_users` if you need to filter client-side.
