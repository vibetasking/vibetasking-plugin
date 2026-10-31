# Webhooks to any destination

A webhook POSTs each activity its lists match (see **Webhooks** in `operations.md`). Two optional fields make one serve any HTTP destination with no code between them: a ``filter`` deciding which activities it sends, and a request ``template`` shaping what it sends. One webhook can post a Slack message for every contact message on one channel, open and close a PagerDuty incident with an inbox item, or update a CRM record. You write both: the person asking rarely knows a destination's format, and the recipes below carry it. The same ``filter`` narrows an ACTIVITY trigger (``activity.filter`` on `create_trigger` and `update_trigger`), an inbox watch (`create_watch` and `update_watch`) and an MCP event subscription (``arguments.filter`` on `events/subscribe`).

## The filter

``filter`` is one Jinja2 expression, written without ``{{ }}``, that is true or false. The webhook, trigger or watch acts only on an activity its lists match and its ``filter`` holds for. Null, or left out, keeps everything the lists match.

```
record.role == 'USER' and run.channel_id == '01013614-9543-4188-9378-29b0dcb6540c'
activity.severity == 'BLOCKING' and run.preset_id == '…'
activity.type == 'RUN_FAILED' and activity.data.variant in ['retry', 'fix_mcp']
'urgente' in (record.content or '') | lower
```

A field the activity does not have reads as undefined, which is false and equal to nothing, so ``run.channel_id == '…'`` is simply false on an activity about no run. Ids are compared as strings. Keep ``activity_types`` and the other lists on the webhook as well: they prune before the expression runs, and the expression refines what they let through.

## What both read

- ``activity``: the activity as `get_activity` answers it: ``id``, ``type``, ``severity``, ``status``, ``table_name``, ``record_id``, ``run_id``, ``agent_id``, ``profile_id``, ``data`` (its kind's detail, see the ``platform-events`` skill), ``holder_id``, ``surfaced_at``, ``acknowledged_at``, ``resolved_at``, ``action``, ``created_at``.
- ``record``: the row it is about, as its own get operation answers it, read as the webhook's owner. For ``MESSAGE_INSERTED`` it is the message, with ``role`` (``USER`` a person or a contact, ``AGENT``, ``OPERATOR`` a member who took the conversation over, ``SYSTEM``), ``content``, ``attachments`` and ``channel``. Null when the owner cannot read it or it has no representation.
- ``run``: the run it concerns as `get_run` answers it (``id``, ``name``, ``state``, ``hold``, ``channel_id``, ``contact``, ``contact_name``, ``agent_id``, ``preset_id`` and the rest), null when there is none.
- ``channel``: the run's channel as `get_channel` answers it (``type``, ``address``, and on a CUSTOM channel ``custom``, whose ``custom.name`` is its name), null when there is none.
- ``workspace``: ``id`` and ``name``.
- ``delivery``: ``id``, the same on every retry and equal to the ``webhook-id`` header, and ``lifecycle``: ``opened``, ``acknowledged`` or ``resolved``. Null in a trigger's or a watch's filter.
- ``links.app``: the item's page in the app: the run's conversation when there is a run, else the workspace.
- ``items`` (a template only): the activities the request carries, oldest first, each with its ``activity``, ``record``, ``run``, ``channel`` and ``links``. One, the delivery's own, unless its group gathers (below).
- ``kept`` (a template only): what the group's last answer kept, null when nothing was or the webhook groups nothing.

## The template

A webhook with a ``template`` sends the request it renders instead of the activity's envelope. It takes ``version`` 3, and beside the template:

- ``format``: ``JSON`` (the default), ``FORM`` or ``TEXT``, which sets the ``Content-Type`` and how every value is escaped (below).
- ``method``: ``POST`` (the default), ``PUT`` or ``PATCH``.
- ``headers``: name to value, each value a template too, such as ``{"Authorization": "Bearer {{ secret('CRM_KEY') }}", "Idempotency-Key": "{{ delivery.id }}"}``. ``Content-Type``, ``Content-Length``, ``Host`` and any ``webhook-*``, ``X-Ocean-*`` or ``X-MCP-*`` header are the platform's and are refused.
- ``url``: the scheme and host are literal text, ``https://`` and a host before any ``{{`` or ``{%``, and the path and query may hold values, each percent-encoded: ``https://api.example.com/contacts/{{ run.contact }}``.

The template is full Jinja2: ``{{ }}``, ``{% if %}``, ``{% for %}`` with ``loop``, ``{% set %}``, ``{% macro %}``, tests, filters and whitespace control. ``include``, ``import`` and ``extends`` load nothing, since a template stands alone. An unknown name fails the render rather than printing nothing, so guard what an activity may lack: ``{% if run %}…{% endif %}``, or ``run.name | default('a run', true)``.

### Escaping by format

Every ``{{ }}`` output is escaped for the webhook's ``format``. Literal text is sent as written.

- ``JSON``: a string is escaped to sit inside a JSON string, so ``"text": "{{ record.content }}"`` stays valid whatever a contact wrote. A whole JSON value (an object, a list, a number) goes in with ``tojson`` and no quotes around it: ``"details": {{ activity.data | tojson }}``. A ``tojson`` value inside quotes breaks the body. The rendered body must parse as JSON or the render fails. There is no ``safe``.
- ``FORM``: each value is percent-encoded: ``To={{ run.contact }}&Body={{ record.content }}``. Literal text is not encoded, so a literal that needs it (a phone number's ``+``, which a form reads as a space) goes through an expression: ``From={{ '+15551234567' }}``.
- ``TEXT``: sent as is.
- A header value is sent as is, and a line break in one fails the render.

### Filters

Beside Jinja2's own (``default``, ``truncate``, ``replace``, ``join``, ``map``, ``lower``, ``upper``, ``tojson``, ``urlencode`` and the rest):

- ``entities`` replaces ``&``, ``<`` and ``>`` with ``&amp;``, ``&lt;`` and ``&gt;``, the three characters Slack treats as control characters.
- ``markdown`` puts a backslash before each ASCII punctuation character Markdown reads (``\`*_{}[]()#+-.!|~>``), so a CommonMark renderer shows the text as typed.
- ``datetime(format, timezone)`` formats a timestamp in an IANA zone: ``{{ activity.created_at | datetime('%d %b %H:%M', 'Europe/Madrid') }}``. Both arguments are optional, ``'%Y-%m-%d %H:%M'`` and ``'UTC'`` by default.

``truncate`` keeps up to five characters past its length and cuts back to the last space before the cut unless told otherwise, so a text whose last such space comes early (a few words, then a long link) loses everything after it. Hold a hard limit with ``truncate(2000, killwords=True, leeway=0)``.

### Secrets

A credential the destination takes outside its URL (an API key, an integration key) goes in as ``{{ secret('NAME') }}``, anywhere in the headers or the body. ``NAME`` is a literal string: a workspace secret's name, or a Vault field's ``exposed_name``. It resolves only when both hold, checked when the webhook is saved and again at every send:

- **The webhook's owner may use it.** A workspace secret, or a Vault item the owner owns, that is shared with the workspace, that is granted to them, or whose owner they oversee.
- **It may go to the webhook's host without asking.** The host is in the item's ``allowed_hosts`` (a workspace secret's ``data.allowed_hosts``), or the item carries ``any_host``, or the workspace secret is bound to no host.

Store such a credential as a Vault item whose ``allowed_hosts`` names the destination's host (`create_vault_item`), owned by the person who owns the webhook or shared with the workspace. Only a plain value or a TOTP code can be sent, never a TOKEN item, a certificate or a connection. The value never passes through the template: ``secret()`` renders a placeholder the platform fills as the request leaves, escaped for where it stands, so nothing in the template can read it, and the stored delivery and the preview show ``${NAME}``. In the URL's path the value keeps its slashes, so a secret may hold a path: ``https://hooks.slack.com/services/{{ secret('SLACK_SUPPORT_WEBHOOK') }}`` sends a Slack webhook kept as a Vault item bound to ``hooks.slack.com``. In the query it is percent-encoded whole.

### The URL is written once

A Slack, Discord, Teams or Google Chat webhook URL is itself the credential. So once a webhook with a template is saved, its ``url`` reads as its origin followed by ``/…`` (``https://hooks.slack.com/…``), and the rest is never answered again. To change it, send the whole URL again. Those destinations need no ``secret()``: the URL is all they ask for, unless the workspace already keeps it in the Vault, as **Secrets** shows.

## How a templated webhook is delivered

It is its own contract, not the envelope's:

- No verification request is sent: Slack, Teams and their kind cannot answer one.
- Each request carries the ``webhook-id``, ``webhook-timestamp`` and ``webhook-signature`` headers over the rendered body, and the ``X-Ocean-*`` headers. A destination that does not check them ignores them.
- It is retried only when the request provably did not land: no connection, or a 408, 429 or 503 answer. A timeout after the request went out, or any other answer, is final, because the destination may have acted on it, and a destination that ignores ``webhook-id`` would act twice: two Slack posts, two Linear issues. Where the destination takes its own idempotency key (PagerDuty's ``dedup_key``, an ``Idempotency-Key`` header an API documents), set it from ``{{ delivery.id }}`` or ``{{ activity.id }}``.
- A render that fails, or a secret refused at send (the owner lost access, the item's hosts changed), is final. Its reason is the delivery's ``error`` in `list_webhook_deliveries`, beside the ``request`` that went out (secrets as ``${NAME}``), and the owner hears of a failing webhook in the inbox as ``WEBHOOK_FAILING``.

### Groups: threads, tickets and bursts

Three optional fields beside the template make a conversation one thread or one record at the destination:

- ``key``: a template whose text names a group, ``{{ run.id }}`` for one per conversation. The deliveries whose key renders alike go one at a time, in the order their activities happened. Empty renders group nothing.
- ``gather``: seconds (1 to 300) a group's first delivery waits for more. Activities of its group arriving before its request goes out join it, and the template reads them all in ``items``: a contact's five quick messages become one post. The request goes within a minute after the wait.
- ``keep``: an expression over ``response`` (``status``, ``headers`` with lower case names, ``json``, the body parsed or null, and ``text``) taking a value from the destination's answer to a request that succeeded: ``response.json.ts`` (Slack), ``response.json.data.issueCreate.issue.id`` (Linear), ``response.headers.location``. The group's next request reads it as ``kept``, so it can reply in the thread or comment on the record the first one made. An answer without it keeps the last value.

``gather`` and ``keep`` take a ``key``. Read the parent's id where the destination answers a reply with its own: Slack answers a reply's ``ts`` beside its thread's in ``message.thread_ts``, so a thread keeps ``response.json.message.thread_ts or response.json.ts``.

``accepted``, beside them and with no key needed, is an expression over the same ``response`` saying whether a destination that answered a success took the request: ``response.json.ok`` for Slack's Web API, which answers 200 with ``"ok": false`` and an ``error`` when it refuses a message. False, or an expression that fails on the answer, fails the delivery for good, the destination's words or the expression's error in its ``error``, and nothing is kept from it. Without it any 2xx counts as delivered. ``list_webhook_deliveries`` shows a gathered request's other activities in ``gathered``, and `preview_webhook` answers the ``key`` the activity renders and what its group last kept.

A version 3 webhook **without** a template can carry the related rows instead: ``expand`` names any of ``record``, ``run`` and ``channel``, and each rides in the delivery's ``data`` beside the activity's own fields (``data.record``, ``data.run``, ``data.channel``), so a receiver needs no second read.

## Writing one

1. Read what the destination takes (the recipes below, or its own documentation) and what it needs from the user: a URL they create there, a key to store as a Vault item bound to its host.
2. Draft the filter and the template, and render them with `preview_webhook`. It takes the draft (``url``, ``version``, ``method``, ``format``, ``template``, ``headers``, ``filter``, ``expand`` and the lists), or a saved webhook's ``webhook_id`` with only the fields you change, and an ``activity_id`` to render one activity, by default the latest one the lists match, preferring one the filter matches. It answers the activity it rendered (``activity_id``, ``activity_type``, ``activity_created_at``), ``matched``, the ``request`` as it would go out (``method``, ``url``, ``headers``, ``body``, secrets as ``${NAME}``, and a saved webhook's URL as its origin alone), an ``error`` naming the ``field``, the ``message`` and the template ``line``, and ``warnings``, each with a ``code``: ``reads_no_channel`` for a message filter that names no channel, ``misspelt_field`` with the ``field`` none of the recent activities has. Nothing is sent.
3. Fix and render again until the request is what the destination documents. Preview against the kinds of activity the filter lets through, through ``activity_id``: an activity with no run exercises every guard.
4. The first real send reaches someone outside the platform, so show the user the rendered request and ask before you create the webhook.
5. `create_webhook` with ``version`` 3, or `update_webhook` on the webhook you previewed. Then read `list_webhook_deliveries` after the next matching activity: ``status_code``, ``error`` and ``request`` say how it went.

## Echo loops

Every message lands as ``MESSAGE_INSERTED``, whoever wrote it: a contact, the agent, a member answering, the platform. A destination that feeds back into the workspace turns each delivery into a new message: a Slack channel a VibeTasking Slack channel also reads, a CRM that messages the contact. A filter that lets that message through delivers it again, and again, without end. So a ``MESSAGE_INSERTED`` filter always names its channel and its role, ``record.role == 'USER' and run.channel_id == '…'``, and the preview warns about one that names no channel.

## Recipes

Each one names what the user creates at the destination, the request, and a template that follows the escaping above. Pair it with a filter that keeps only what the user asked for. The message recipes assume the filter of **Echo loops**, which names a channel and a role, so ``run`` and ``channel`` are always there.

### Slack

Source: [Sending messages using incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/), [Formatting message text](https://docs.slack.dev/messaging/formatting-message-text/), [Rate limits](https://docs.slack.dev/apis/web-api/rate-limits/).

- **At Slack:** a Slack app with **Incoming Webhooks** activated, then **Add New Webhook to Workspace** and the channel it posts to (for a private channel the user must be a member of it). The webhook posts to that one channel, as the app's name and icon, which cannot be overridden.
- **Request:** POST ``https://hooks.slack.com/services/T…/B…/…``, ``format`` ``JSON``, a ``text`` (required, Slack answers ``no_text`` without it) and optionally ``blocks``. Slack calls the URL a secret and revokes leaked ones.
- **Escaping:** Slack reads ``&``, ``<`` and ``>`` as control characters (links, mentions such as ``<!channel>``), so every value a contact or a person wrote goes through ``entities``. A contact who types ``<!channel>`` then pings nobody.
- **Limits:** one message per second per channel, short bursts allowed, a 429 with ``Retry-After`` past it. A block's ``text`` holds 3000 characters and a message with a block past it is refused whole, so a contact's words in a block go through ``truncate(2900, killwords=True, leeway=0)`` after ``entities``, which lengthens them. A cut can land inside an entity, which Slack then shows as text.
- **Threads:** a reply needs the parent's ``ts``, which an incoming webhook never answers, so each of its deliveries is its own message. For a thread per conversation, post with the Web API instead (below).

```jinja
{"text": "*{{ run.contact_name | default('A contact', true) | entities }}* on {{ (channel.custom.name if channel.custom else channel.type) | entities }}: {{ (record.content or '') | entities }}\n<{{ links.app }}|Open the conversation>"}
```

One thread per conversation, through ``chat.postMessage``. At Slack: a Slack app whose bot token holds ``chat:write`` (and ``chat:write.public`` to post where the bot is no member), the token kept as a Vault item bound to ``slack.com``, and the channel's id. POST ``https://slack.com/api/chat.postMessage``, headers ``{"Authorization": "Bearer {{ secret('SLACK_BOT_TOKEN') }}"}``, ``key`` ``{{ run.id }}``, ``keep`` ``response.json.message.thread_ts or response.json.ts``, ``accepted`` ``response.json.ok``, ``gather`` a few seconds. ``reply_broadcast`` shows a reply in the channel too, for people who follow the channel rather than the thread.

```jinja
{"channel": "C0123456789", "text": "{{ run.contact_name | default('A contact', true) | entities }} wrote"{% if kept %}, "thread_ts": "{{ kept }}"{% endif %}, "blocks": [{% for item in items %}{% if not loop.first %},{% endif %}{"type": "section", "text": {"type": "mrkdwn", "text": "> {{ (item.record.content or '') | entities | replace('\n', '\n> ') | truncate(2900, killwords=True, leeway=0) }}"}}{% endfor %}]}
```

### Discord

Source: [Webhook resource, Execute Webhook](https://docs.discord.com/developers/resources/webhook), [Allowed mentions object](https://docs.discord.com/developers/resources/message).

- **At Discord:** a webhook on the channel, whose URL carries its token: ``https://discord.com/api/webhooks/{webhook.id}/{webhook.token}``.
- **Request:** POST, ``format`` ``JSON``, ``content`` up to 2000 characters (or ``embeds``, up to 10). ``?thread_id=`` posts into a thread of the channel. The answer is a 204 unless ``?wait=true``.
- **Escaping:** set ``allowed_mentions`` to ``{"parse": []}``, so a contact's ``@everyone``, ``@here`` or role mention notifies no one.

```jinja
{"content": "{{ run.contact_name | default('A contact', true) }}: {{ (record.content or '') | truncate(1800, killwords=True, leeway=0) }}\n{{ links.app }}", "allowed_mentions": {"parse": []}}
```

### Microsoft Teams

Source: [Create an Incoming Webhook](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook), [Microsoft Teams connector, When a Teams webhook request is received](https://learn.microsoft.com/en-us/connectors/teams/), [Send messages in Teams using incoming webhooks](https://support.microsoft.com/en-us/office/send-messages-in-teams-using-incoming-webhooks-323660ec-12ca-40b1-a1d3-a3df47e808c4), [Format text in cards](https://learn.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-format).

- **At Teams:** Microsoft 365 Connectors are nearing deprecation, so a webhook is a workflow: on the channel, **More options**, **Workflows**, the template **Send webhook alerts to a channel**, then copy the webhook link it creates. Its trigger, **When a Teams webhook request is received**, must let **Anyone** post: the tenant options expect a signed in user's token, which a webhook cannot send. The workflow belongs to the person who made it, not to the channel, so a co-owner keeps it running if they leave.
- **Request:** POST, ``format`` ``JSON``, ``type`` ``message`` with ``attachments`` each holding an Adaptive Card: ``contentType`` ``application/vnd.microsoft.card.adaptive``, ``contentUrl`` null and the card in ``content``.
- **Escaping:** a ``TextBlock`` reads ``**bold**``, ``_italic_``, lists and ``[title](url)`` links, and ignores HTML.
- **Limits:** a message up to 28 KB.

```jinja
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
          {"type": "TextBlock", "text": "**{{ run.contact_name | default('A contact', true) }}** on {{ channel.custom.name if channel.custom else channel.type }}"},
          {"type": "TextBlock", "text": "{{ record.content or '' }}"},
          {"type": "TextBlock", "text": "[Open the conversation]({{ links.app }})"}
        ]
      }
    }
  ]
}
```

### Google Chat

Source: [Build a Google Chat app as a webhook](https://developers.google.com/workspace/chat/quickstart/webhooks), [Format messages](https://developers.google.com/workspace/chat/format-messages).

- **At Google Chat:** in a browser (not the mobile app), the space's menu, **Apps & integrations**, **Add webhooks**, a name, then **Copy link**. The URL is ``https://chat.googleapis.com/v1/spaces/SPACE_ID/messages?key=KEY&token=TOKEN``, and Google asks that its ``token`` be kept secret.
- **Request:** POST, ``format`` ``JSON``, a ``text``. Chat reads ``*bold*``, ``_italic_``, ``~strike~``, backquotes and ``<url|text>`` links in it.
- **One thread per conversation:** put ``thread.threadKey`` in the body and add ``&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD`` to the URL. A message whose key matches joins that thread, else it starts one, so keying on the run keeps each conversation in its own thread.
- **Limits:** one request per second per space, shared by every webhook in it.

```jinja
{"text": "*{{ run.contact_name | default('A contact', true) }}*: {{ record.content or '' }}\n<{{ links.app }}|Open the conversation>", "thread": {"threadKey": "{{ run.id if run else activity.id }}"}}
```

### PagerDuty

Source: [Send an alert event](https://docs.pagerduty.com/developer/send-alert-event), [Events API v2 overview](https://docs.pagerduty.com/developer/events-api-v2-overview).

- **At PagerDuty:** an Events API v2 integration on the service, whose 32 character Integration Key is the ``routing_key``. Store it as a Vault item bound to ``events.pagerduty.com``. No other auth header.
- **Request:** POST ``https://events.pagerduty.com/v2/enqueue``, ``format`` ``JSON``. A trigger needs ``payload.summary`` (up to 1024 characters), ``payload.source`` and ``payload.severity`` (``critical``, ``error``, ``warning`` or ``info``). An acknowledge or a resolve needs only the same ``routing_key`` and ``dedup_key`` as the trigger (up to 255 characters), and applies to an open alert with that key. A payload is at most 512 KB.
- **Lifecycle:** a webhook delivers an inbox item when it opens, is acknowledged and resolves, so ``delivery.lifecycle`` maps to ``trigger``, ``acknowledge`` and ``resolve``, and ``dedup_key`` set to the activity's id keeps every event about one inbox item on one alert, so the incident follows the item. PagerDuty answers 202 when it accepted an event. Filter on the severities that should page, such as ``activity.severity in ['BLOCKING', 'WARNING']``.

```jinja
{
  "routing_key": "{{ secret('PAGERDUTY_KEY') }}",
  "dedup_key": "{{ activity.id }}",
{% if delivery.lifecycle == 'opened' %}
  "event_action": "trigger",
  "payload": {
    "summary": "{{ activity.type }}: {{ run.name | default('a run', true) | truncate(900, killwords=True, leeway=0) }}",
    "source": "vibetasking",
    "severity": "{{ {'BLOCKING': 'critical', 'WARNING': 'warning'}.get(activity.severity, 'info') }}",
    "custom_details": {{ activity.data | tojson }}
  }
{% else %}
  "event_action": "{{ 'acknowledge' if delivery.lifecycle == 'acknowledged' else 'resolve' }}"
{% endif %}
}
```

### Linear

Source: [Linear GraphQL API, getting started](https://linear.app/developers/graphql), [the API schema in Linear's SDK](https://github.com/linear/linear-node-sdk/blob/master/schema.md) (``issueCreate(input: IssueCreateInput!)``).

- **At Linear:** a personal API key, stored as a Vault item bound to ``api.linear.app``, and the id of the team the issues go to.
- **Request:** POST ``https://api.linear.app/graphql``, ``format`` ``JSON``, the header ``Authorization`` holding the key with no ``Bearer`` before it (``Bearer`` is for OAuth tokens). Pass the issue as GraphQL variables, so a value is escaped once, as JSON, never inside the query text.
- **Idempotency:** Linear documents no idempotency key, which is why a templated webhook never retries a request that may have landed.

```jinja
{
  "query": "mutation CreateIssue($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id } } }",
  "variables": {
    "input": {
      "teamId": "THE_TEAM_ID",
      "title": "{{ run.name | default(activity.type, true) | truncate(200, killwords=True, leeway=0) }} failed",
      "description": "{{ activity.data.variant | default('', true) }} {{ links.app }}"
    }
  }
}
```

with ``headers`` ``{"Authorization": "{{ secret('LINEAR_KEY') }}"}`` and a filter such as ``activity.type == 'RUN_FAILED'``.

### Twilio SMS

Source: [Message resource, create a Message](https://www.twilio.com/docs/messaging/api/message-resource).

- **At Twilio:** the account's ``AccountSid``, a sending number (or a Messaging Service), and an API key's SID and secret. HTTP Basic auth sends ``base64(SID:secret)``, and a template cannot encode a secret it never reads, so store the base64 of ``SID:secret`` itself as a Vault item bound to ``api.twilio.com``.
- **Request:** POST ``https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json``, ``format`` ``FORM``, with ``To`` (E.164), ``From`` (or ``MessagingServiceSid``) and ``Body``, up to 1600 characters, an SMS over 160 GSM-7 characters being billed in segments. Write the numbers as expressions so their ``+`` is encoded.

```jinja
To={{ '+34600000000' }}&From={{ '+15551234567' }}&Body={{ (run.contact_name | default('A contact', true)) ~ ': ' ~ (record.content or '') | truncate(1500, killwords=True, leeway=0) }}
```

with ``headers`` ``{"Authorization": "Basic {{ secret('TWILIO_BASIC') }}"}``.

### A JSON API with a bearer token

Any API that takes a JSON body and a bearer token, a CRM updating the contact's record for instance. The token is a Vault item bound to the API's host, and the record's id rides in the path.

```jinja
{"last_message": "{{ record.content or '' }}", "last_message_at": "{{ activity.created_at }}", "conversation": "{{ links.app }}"}
```

with ``method`` ``PATCH``, ``url`` ``https://api.example.com/contacts/{{ run.contact }}``, and ``headers`` ``{"Authorization": "Bearer {{ secret('CRM_KEY') }}", "Idempotency-Key": "{{ delivery.id }}"}``, keeping the idempotency header only where the API documents one.