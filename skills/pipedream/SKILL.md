---
name: pipedream
description: Pipedream action discovery and shell usage
---

# Pipedream

Thousands of third-party services (Gmail, Slack, Google Sheets, etc.) through a unified CLI.

## Commands

```bash
pipedream gmail --help                  # list actions for an app
pipedream gmail send_email --help       # show parameters for an action
pipedream gmail send_email --json '{"to": "user@example.com", "subject": "Hi", "body": "Hello"}'
pipedream google_sheets add_single_row --json '{"sheetId": "1abc...", "cells": ["a", "b"]}'
```

You can also pipe JSON via stdin: `echo '{"param": "value"}' | pipedream <app> <action>`

## Discovery

1. Check `<integrations>` in your system prompt. Listed services are already connected by the user, and the integration name gives you the app name. Go directly to step 3.
2. Grep `system/pipedream/toolkits.json` for keywords (compact toolkit names and descriptions), or have a sub-agent explore it more broadly.
3. `pipedream <app> --help`: list available actions and their descriptions for an app.
4. `pipedream <app> <action> --help`: show parameters for an action.

Recipe shortcut: skip discovery when your recipe provides a known successful approach.

## Tips & Tricks

- Some parameters offer remote options (channel ids, sheet ids, pipeline ids). When you already know the id (from a prior read action), pass it directly. Otherwise call the app's `configure_prop` action to list the valid label/value pairs:

```bash
pipedream gmail configure_prop --json '{"action": "gmail_add_label_to_email", "prop_name": "addLabelIds"}'
```

- Most query actions have parameters that allow you to apply filters or paginate their results. Use them. Third-party services can have tons of data, and it's not practical to read all of it at once. Apply strict filters, gradually relaxing them if required.

- When no parameter filters what you need, pipe the action's output through shell tools instead of reading it raw. Always `tee` the full output to a file first, so a missed match doesn't force a repeat call:

```bash
pipedream gmail list_emails --json '{"maxResults": 100}' | tee emails.json | grep -i -B3 -A8 miguel
```
