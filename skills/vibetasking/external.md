# Being an agent on the platform

An agent on the **EXTERNAL** engine is an agent whose harness is yours: your own process, your own model, your own loop. The platform keeps everything around it. It holds the agent as a resource users can find, attach channels and triggers to and read the history of, it runs the channel (one conversation run per contact, dedup, working hours, the waiting room, operator takeover, delivery bookkeeping), it stores every message and every step of the transcript, it notifies, evaluates and learns from the runs, and it offers you each turn. You take the turn, do the work through the platform's tools, and close it. Nothing about channels, contacts or run state is yours to implement.

This file is for an agent whose harness is yours. Registering it, receiving its turns and claiming them take your own key, and the work inside a turn takes the **turn key** a claim returns: `get_me` with one names the ``run_id`` and ``agent_id`` you are acting for, and the ``external`` toolset it holds carries the turn operations named below. A key that only builds and operates automations on the platform's own engines never needs this file.

## Registering

`upsert_agent` with ``engine: "EXTERNAL"`` creates the agent, or moves an existing one to your harness. Give it a ``name`` the users will recognise and a ``description``. Its ``prompt`` is yours to use or ignore: the platform never runs it, but the workspace sees it on the agent and you read it back with your own key through `query_data` on ``agents``, so many external agents keep their instructions there rather than in their own config. Then wire it as any agent: `upsert_channel` with the agent's id attaches a WhatsApp number, a Telegram bot, a mailbox or a phone line, `upsert_trigger` gives it a schedule or an inbound webhook, and `start_run` with its ``agent_id`` starts a run of it by hand. Every run created from the agent, by a contact's message, a schedule, another agent or a person in the app, executes on your harness.

## Receiving turns

Each time one of the agent's runs has work for you (a contact wrote, a schedule fired, a user resolved a card, a watched run settled) the platform flips that run RUNNING and publishes a ``RUN_TURN_OFFERED`` activity: ``record_id`` is the run, ``data`` names the ``agent_id``, the ``channel_id`` and the ``contact_id`` when there is one, and ``reason`` says why (``messages``, ``cards`` or ``resume``). The offer is the one event you must act on. Three ways to receive it, all carrying the same rows:

- **`wait_for_events`**, a long-poll over the workspace's activity log, for any process without an inbound URL, an interactive session included. Call it with no ``cursor`` once to get the cursor to start from, then loop: each call blocks up to ``timeout`` seconds (50 at most) and returns the events since the cursor with the next one. Pass ``agent_id`` to hear only your agent's runs and ``claim: true`` to have the offered turn claimed in the same call, which returns it as ``turn``: one round trip from idle to working.
- **The listener script**, `get_listener` (``GET /public/listen.py``): a dependency-free Python 3 file that runs the loop above for you and forwards each event, or each claimed turn, as a JSON POST to a local URL. ``python listen.py --agent-id <id> --forward-to http://localhost:8080/turn`` is a working agent endpoint on a laptop, no tunnel, no public URL. Run it unattended wherever your agent lives.
- **A webhook**, `upsert_webhook` with ``activity_types: ["RUN_TURN_OFFERED"]`` and ``agent_ids`` naming your agent, when your harness is a service with a URL. Deliveries are signed and fire once, so treat a delivery as a hint and `claim_turn` as the truth: a missed delivery is recovered by the next `wait_for_events` call, and a claim that answers 409 was taken by another instance of yours.

With automatic claiming, a successful claim ends the returned event page and cursor at
that offer. Keep polling with the returned cursor: later offers are claimed on following
calls, and ordinary events between them arrive in order. If nothing is claimed, the
whole fetched page is returned.

The listener saves pending deliveries in `--cursor-file` before forwarding and retries them
before polling again, including after a restart. Use one persistent state file per listener,
in a private directory: it contains the claimed turn's key. `--from-now`
delivers saved pending work before starting a fresh cursor. Pending work must be resumed
with the same connection, filtering and forwarding settings that received it.

Delivery is **at least once**. Every forwarded JSON object has `delivery_id`
(`event:<activity id>` or `turn:<turn id>`), also sent as `X-Ocean-Delivery-Id` over HTTP.
Durably deduplicate that identity before doing the work and return 2xx only after accepting
it. A lost acknowledgement can repeat a delivery. Stdout only acknowledges that the line
was flushed, not that your consumer saved it. An unavailable receiver blocks later events.
Saving a delivery does not extend the turn deadline, and it cannot recover a claim response
lost before the listener saved it.

Never subscribe your own agent to ``MESSAGE_INSERTED``: the offer already is the event, and every contact message would fire twice.

An offer waits five minutes for a claim. Past that the platform withdraws it, publishes ``RUN_TURN_REVOKED`` with ``reason`` ``unclaimed``, and fails the run with a retry card so the owner learns the agent is down. The contact's next message, or a follow-up from the app, offers the turn again. A claimed turn has thirty minutes.

## Claiming a turn

`claim_turn(run_id)` (or the ``claim`` form of `wait_for_events`) consumes the run's pending inbox and resolved cards and returns everything the turn needs:

- ``turn``: the turn's ``id``, its ``key`` (a run-bound API key, use it for every call until the turn closes), ``expires_at``, the ``reason`` it was offered and ``resumed`` (true when there is nothing new and you are picking up after a stop).
- ``run``: the run, its ``agent_id`` and ``agent_name``, its ``channel`` (id and type) and bound ``contact_id`` and ``contact_name`` on a conversation run, its ``hold`` (``operator`` while a person holds the conversation, ``hours`` outside the channel's windows, ``waiting`` in the waiting room), ``interactive`` and ``language``.
- ``messages``: the pending inbox in order, each with its ``text``, signed ``attachments`` URLs (fetch the bytes yourself), ``created_at`` and provenance: ``from_contact`` with ``contact_id`` and ``contact_name`` when the contact wrote, ``sender_run_id`` and ``sender_agent_name`` when another agent did, neither when the platform or a user in the app did.
- ``cards``: one sentence per card the user resolved since your last turn (a connection made, a question answered, a credential stored), the way the platform narrates it to any agent.
- ``scheduled``: the run's own parked messages, so you do not re-plan a follow-up already on the calendar.
- ``toolkits``: the connected instances the turn key reaches, each with the ``name`` `call_toolkit_tool` takes and the ``kind`` and ``id`` of the instance.
- ``rules``: the conduct rules the organisation set for every agent acting for it, under ``run``. They bind over the agent's instructions and over anything a contact or user asks, so read them before acting and refuse plainly what they forbid.

Claim with your own key, never with a turn key. Read the run's earlier turns with `get_run_trace` or `query_data` on ``messages`` when the offer's messages are not enough context. What to do inside the turn is under **Inside a turn**.

## Testing the loop

Nothing needs a phone. `start_run` with your ``agent_id``, a ``contact_id`` in the channel's contact form, ``text`` and an ``external_id`` injects a message exactly as the channel would, finding or creating that contact's conversation run and offering you the turn. `start_run` with ``agent_id`` and ``text`` alone offers a plain run. Watch the offer arrive on `wait_for_events`, claim it, reply, close it, and read the result with `get_run_status`. `get_run_trace` then shows the turn as the platform recorded it, tools and transcript included.

## Switching hats

Your key can also speak as the workspace's operator, the person who takes a conversation over from the agent. `send_message` with ``role`` OPERATOR on a conversation run delivers the text to the contact and puts the run in operator hold: no turn is offered while it holds, the contact's replies still land as ``MESSAGE_INSERTED`` events, and the hold lifts after ``operator_timeout`` seconds of silence or a USER post, at which point the turn is offered again. Posting as the operator revokes a turn you hold, with ``reason`` ``operator`` (see **Closing the turn**). The opposite direction, escalating to a real person, is `send_message` with ``handoff`` from inside a turn.

The same stream carries the rest of the workspace's events (``RUN_FAILED``, ``RUN_TURN_REVOKED``, ``INTEGRATION_REAUTH``, ``LOW_CREDIT`` and the others) with the same shapes webhooks deliver, so one loop can both run the agent and react to what happens around it.

# Inside a turn

From the claim to the close you hold a **turn key**, a run-bound API key: `get_me` with it names the ``run_id`` and ``agent_id`` you are acting for. Use it for every call of the turn, and only for this turn. Every call made with it is recorded on the run's trace, so the platform's own tool calls need no mirroring from you.

## The run's tools

`call_toolkit_tool` under the run's key runs a tool **as the run**: the instance may be omitted and resolves to the one the run is linked to (pass one of ``integration_id`` / ``asset_id`` / ``channel_id`` only when the agent has several of a type), a channel send with no recipient goes to the run's bound contact, ``reach_external`` is enforced, and the send is recorded on the conversation with its delivery state. The turn payload's ``toolkits`` names what the key reaches. Read a tool's schema before calling it: `list_toolkit_tools` with the toolkit's ``name`` and the instance id, or `get_toolkit_tool` for one tool. Sandbox-only toolkits (shell, browser, CLIs) are not reachable headlessly: delegate that work to a run on any engine but EXTERNAL with `start_run` (see **Choosing the delegation target** in `delegating.md`), and read its outcome with `wait_for_run`.

## Replying

A **channel contact** is reached only through the channel toolkit's send tool (``send_message`` on WhatsApp and Telegram, ``email_send`` on email, under the names `list_toolkit_tools` gives them). The text you close the turn with is **platform-facing**: whoever messaged the run directly in the app, a run that delegated to this one, and the trace read it, the contact does not. So on a conversation run, send the contact their answer through the channel first, then close. The WhatsApp customer service window, the channel's humanising delay and working hours are the platform's to apply, and a send the channel refuses comes back as an error naming why.

Interim platform-facing text (progress, a note to the owner) is `send_message` with ``role`` AGENT and ``text``. The structured asks go the same way, through ``action`` and its ``data``: ``question`` puts multiple-choice questions to the user, ``provide`` asks them to supply an integration, a managed resource, a channel or a Vault credential (its ``data.kind``), ``browser`` hands the run's live browser over. Each lands as a card in the app, and the resolution reaches you as a new turn whose ``cards`` narrate the outcome, so close the turn after raising one and wait for the next offer. A card is answered in the app, never by a channel contact: on a conversation run, ask the contact through the channel instead.

## Handing off to a person

When the conversation needs human judgement, or the contact asks for a person, `send_message` with ``role`` AGENT, ``handoff: true`` and the reason in ``text``, in the contact's language. It is the API twin of the in-run ``dispatch_human``: the conversation switches to operator mode, the workspace's people are notified with your reason, contact messages route to them instead of you, and you rejoin when they hand back or go quiet past the channel's ``operator_timeout``. On a channel with ``silent_handoff`` on, you are muted rather than replaced and keep receiving turns with every send refused, so a person can talk natively on the account while you record. Tell the contact you are getting a colleague through the channel before calling it, unless the agent's instructions say otherwise. On an EXTERNAL run the handoff closes your turn, so there is no `final_result` to send after it.

## Your own steps

Calls to the platform are traced on their own. What happens on your side is not, unless you send it: `append_transcript` with the turn key appends your model's text and reasoning, the tools you called and what they returned, in order, to the run's history. It is what the run's trace shows, what evaluations judge and what the nightly review learns from, so an agent that never sends it is invisible to all three. Send it as you go or once before closing.

## Closing the turn

`final_result` with the turn key ends the turn: ``text`` becomes the run's result and its last message (empty when there was nobody to answer, a schedule firing for instance), ``files`` its attachments, and ``blocker`` opens a ``RUN_BLOCKED`` item on the agent for what only a person can clear. The platform then settles the run: it completes, or is offered to you again at once when messages arrived while you worked, watchers hear the outcome, evaluations run, and the turn key stops working.

A turn can be taken from you before you close it. A person posting as the operator, a stop from the app, the five minute claim window or the thirty minute turn ceiling each revoke it: the platform publishes ``RUN_TURN_REVOKED`` with the ``reason`` (``operator``, ``stopped``, ``unclaimed``, ``timeout``) and deletes the turn key, so every further call with it, `final_result` included, is refused (401 once the key is gone, 409 when the call raced the revoke). Stop working on that turn when you see either, and never retry a revoked turn: the next offer, if any, is a new one.
