---
name: composio
description: Composio action discovery and shell usage
---

# Composio

1000+ third-party services (Gmail, Slack, Google Sheets, etc.) through a unified CLI.

## Commands

```bash
composio gmail --help                 # list actions for a toolkit
composio gmail fetch_emails --help    # show parameters for an action
composio gmail fetch_emails --json '{"query": "from:user@example.com", "max_results": 5}'
composio slack send_message --json '{"channel": "#general", "text": "Hello"}'
```

You can also pipe JSON via stdin: `echo '{"param": "value"}' | composio <toolkit> <action>`

For a payload built from other commands' output (e.g. `jq`), or any large body, don't pipe straight into `--json @-` and don't inline it — quoting/escaping is fragile and fails silently on nested quotes. Write the JSON to a file and pass `--json-file`, which reads it byte-for-byte:

```bash
jq -n --arg id "$ticket_id" '{ticket_id: $id, comment_public: false}' > payload.json
composio zendesk update_zendesk_ticket --json-file payload.json
```

`--json`/`--json-file` payloads are parsed as JSON, not Python: use lowercase `true`/`false`/`null`, not Python's `True`/`False`/`None`. If you're assembling the payload with a Python snippet, run it through `json.dumps` (or hand-write the literal) rather than interpolating Python's `repr` of a bool/`None`.

## Discovery

1. Check `<integrations>` in your system prompt. Listed services are already connected by the user, and the integration name gives you the toolkit name. Go directly to step 3.
2. Grep `system/composio/toolkits.json` for keywords (compact toolkit names and descriptions), or have a sub-agent explore it more broadly.
3. `composio <toolkit> --help`: list available actions and their descriptions for a toolkit.
4. `composio <toolkit> <action> --help`: show parameters for an action.

Get an action's exact shape before your first call to it in this run, from one of two places. When the service has its own skill (check your skill index), read the skill: a command it spells out with arguments is complete, call it as written with no `--help` round trip. For any other action, run `--help` first instead of guessing a name from what "sounds right" (e.g. a REST-API-style name).

Recipe shortcut: skip discovery when your recipe provides a known successful approach.

## Don't chain mutating calls with `&&`

When applying the same mutation across several records (e.g. updating 8 tickets), don't chain the `composio` invocations with `&&` in one shell call. `&&` stops at the first failure, so one bad field or argument on record 3 silently drops records 4-8 with no update attempted at all — and the truncated output can look like a clean run at a glance. Issue each mutating call separately (or loop with per-call status checks) so a single failure doesn't take out the rest of the batch, and you can see exactly which records still need the update.

## Harmless startup warning

You may see a log line like `toolkit_name_to_class failed for ComposioToolkit: ModuleNotFoundError: No module named 'ocean.toolkits.composio.'` right before a composio call executes. This is expected — it's the platform falling back to the shell CLI path — not an error in your command. Ignore it and proceed.

## Tips & Tricks

- Most query actions have parameters that allow you to apply filters or paginate their results. Use them. Third-party services can have tons of data, and it's not practical to read all of it at once, as most of it won't be relevant for the task at hand. Apply strict filters, gradually relaxing them if required.

- When no parameter filters what you need, pipe the action's output through shell tools instead of reading it raw. Always `tee` the full output to a file first, so a missed match doesn't force a repeat call:

```bash
composio gmail fetch_emails --json '{"max_results": 100}' | tee emails.json | grep -i -B3 -A8 miguel
```

Action output is pretty-printed JSON: `jq` selects whole records, `grep` only matching lines. If your filter comes up empty, re-search the saved file before calling the action again.
