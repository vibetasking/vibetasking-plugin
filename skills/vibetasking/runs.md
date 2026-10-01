# Runs

A **run** is one execution of a task inside the agent's sandbox: an agent's instructions, or an ad-hoc brief sent straight to `start_run`.

To attach files to the message that starts or feeds a run, pass a base64 ``files`` array (each ``{name, content_base64}``) to `start_run` or `send_message`. The agent finds them in its sandbox.

Lifecycle: ``READY`` → ``RUNNING`` → ``COMPLETED`` | ``FAILED`` | ``INTERRUPTED`` (paused mid-execution, resumes via ``WAITING``). ``CANCELED`` is the only fully terminal state. ``COMPLETED`` and ``FAILED`` runs can be re-dispatched by sending a follow-up message (`send_message`). To halt a run that's executing or waiting, call `stop_run(run_id)`. It interrupts the run and, by default, deletes any pending cron-scheduled messages so a later firing can't revive it (this is a pause to ``INTERRUPTED``, not the terminal ``CANCELED``). Wake a paused (``WAITING``/``INTERRUPTED``) run by sending it a message. `resume_run` is different: it replays a run from a chosen past tool call or an edited user message (debugging). To end a run for good, `cancel_run` moves it to ``CANCELED``: it is never dispatched again, its parked messages are deleted, and a channel contact's next message opens a fresh run. Cancel only when the run must end permanently. The agent's tool-call history lives in the ``histories`` table (gzipped JSON), not ``runs.data``. Poll a run cheaply with `get_run_status` (state, result, latest message), or `wait_for_run` to block server-side until it settles. `get_run_trace` gives the full tool-by-tool view, with any oversized argument or result cut short behind a marker naming its full length. It pages: while ``has_more`` is true pass ``cursor`` back as ``after``, which also tails a growing run without refetching. Pass ``search`` to filter entries server-side (case-insensitive substring over tool, args, result, reasoning): recalling one action from a long conversation, your own included, is one filtered call, never a page-through.

## Starting, messaging and stopping

- **Start a run.** `start_run` from an ``agent_id`` or a ``preset_id``, or re-dispatch an existing run via ``run_id``. Pass ``integration_ids`` / ``asset_ids`` to attach a workspace integration or asset to the run itself, so a one-off reaches a connected account, database, mailbox or hosted site without an agent holding it (not valid on a ``run_id`` re-dispatch, and only backings your own key reaches). Pair it with `wait_for_run` when you need the result before continuing your own work, and skip the wait when the hand-off is your last step.
- **Send a message into an existing run.** `send_message` posts a message into a run. Without ``cron`` it dispatches the run immediately. With ``cron`` the message is parked and delivered when the expression resolves (**Parking a message on a schedule** below).
- **Ask a run's contact to connect something.** `connect_link` mints a link, valid for a day, that the run's contact opens with no account to connect an integration (``kind: integration`` with ``types`` naming it, ``GMAIL``, or ``account`` to fix one the run already has), link a managed resource the run's owner may use (``kind: asset`` with ``types``, ``TWILIO``, owned runs only), or store a credential for that run (``kind: vault_item`` with ``name`` and ``type``). It takes the same request ``send_message`` takes with ``action: provide`` and nothing else: the page shows the connection the link names, and the run itself sends the ``url`` through its channel with any words the contact needs, and once the contact acts the run is told as a platform message. What the contact supplies serves that run alone, owned by the run's owner or by nobody. The run's ``allow_connections`` gates it like a card.
- **Stop a run.** `stop_run` interrupts a run. Idempotent, so calling it on an already-stopped run is fine.
- **Replay or compress a run (debugging).** `resume_run` replays a run from a past tool call (``from_tool_call_id``) or an edited user message, and waking a paused run is just `send_message`, not this. `abridge_run` compresses a long-lived run's history between turns. Both target *other* runs (a run cannot resume itself, and an executing run cannot be abridged), and both are VIBETASKING engine only: CLAUDE and CODEX runs reject them.

## Channel-attached agents

When `start_run` targets an agent connected to a channel, pass ``contact_id`` matching the channel type:

- **WhatsApp / SMS**: a phone number, with or without a leading ``+``. 7 to 15 digits.
- **Telegram**: a numeric chat_id. A ``@username`` does not work, because bots cannot start a chat with someone who has not first messaged them.
- **Instagram**: the contact's numeric IGSID (Instagram-scoped ID).
- **Messenger**: the contact's numeric PSID (page-scoped ID).
- **Slack**: a Slack conversation or user id (``C…``/``G…``/``D…``/``U…``).
- **Email**: a normal email address.
- **LinkedIn**: the contact's member id (``ACoAA…``). Profile URLs and ``in/slug`` handles are rejected.

When the agent serves more than one channel, or the ``contact_id`` format is valid for several (a phone number fits both WhatsApp and SMS), pass ``channel_id`` too. If the agent has no channel, do not pass ``contact_id``. A channel with no agent is reached with ``channel_id`` and ``contact_id`` and no ``agent_id``: its people answer its conversations, so it takes ``direct: true`` sends, and on a CUSTOM channel its router's injected messages, and nothing runs.

The ``text`` you pass is delivered to the target agent as a USER prompt. It is *not* the literal outbound payload, and it reaches the conversation marked as coming through your run. The target agent reads it and decides what to send to the contact through the channel. Phrase it as an instruction to that agent (e.g. "Greet the contact and confirm their appointment for Tuesday at 3pm").

## Parking a message on a schedule

`start_run` and `send_message` both accept a 5-field ``cron`` expression: the message is parked and delivered when the schedule first resolves, then the schedule clears itself, so a parked message fires **once**. Use it for reminders, follow-ups, or a delayed hand-off, including on your own run. Recurring work belongs on an agent ``trigger`` instead, same convention. Pass ``timezone`` (an IANA name like ``Europe/Madrid``) to write the cron in the user's local wall-clock time: the platform stores the UTC form and keeps the zone so DST offset changes re-anchor the schedule, so reading a trigger back shows the converted UTC expression, not the local one you wrote. When ``timezone`` is set, minute and hour must be single integers (``0 9 * * 1``, not ``*/15``). Scheduling takes the USER role only (the AGENT role cannot pass ``cron``), and a date-pinned cron whose moment has already passed is rejected rather than rolled to next year. Parked messages are ``messages`` rows with a non-null ``cron`` (`query_data` by ``run_id``). Rewriting a parked row's ``cron`` via `update_data` reschedules it. To cancel one, `delete_data` the row. Never null its ``cron`` instead: clearing the schedule is how the platform *delivers* a parked message, so that sends it rather than canceling it. `stop_run` also drops every parked message on a run, but it pauses the run to do it. Runs park messages to themselves too, an ownerless run through the ``schedule_message`` built-in (see **Self-scheduling** in `runtime.md`).

**Cron format.** 5-field standard cron: ``minute hour day-of-month month day-of-week``. Smallest granularity is one minute. The time shown in a run's context (e.g. ``14:30 (Europe/Madrid)``) is local, so prefer ``timezone`` over hand-converting. Omit it for cadences with no wall-clock anchor (every N minutes/hours) or when the user asked for UTC. For one-off future delivery, pick a cron that resolves to a single moment.

- Local 09:00 on weekdays, the user is in Madrid → ``"cron": "0 9 * * 1-5", "timezone": "Europe/Madrid"``.
- Every weekend at 9pm, but we want it in Australia → ``"cron": "0 21 * * 0,6", "timezone": "Australia/Sydney"``.
- Every 15 minutes (cadence, no anchor) → ``"cron": "*/15 * * * *"``, no ``timezone``.
