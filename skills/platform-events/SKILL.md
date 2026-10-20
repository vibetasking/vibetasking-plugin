---
name: platform-events
description: Make an agent react to platform events (a stranger waiting at a gated
  channel, a failed run, a low balance, a new finding) with an activity trigger, with
  what each event admits and which tool does it
---

# Reacting to platform events

Every notable thing that happens in a workspace lands as an activity: a contact parked by a channel's waiting room, a run that failed or paused, a balance running low, a document added to Knowledge. An activity trigger turns them into runs: at most once an hour it starts one run of its agent over the activities that arrived since its last sweep and match its filters.

## Wiring it

1. Give the reacting agent an activity trigger: `create_trigger` with `agent_id`, `activity` naming the `activity_types` the agent handles, `agent_ids` naming the agents whose runs it watches when it watches only some, `severities` when only some matter, and a `prompt` saying what to do with what arrives.
2. Write the agent's prompt around the events it receives: what each kind means, what to check, which tool settles it, and when to leave it to a person. The agent needs no sandbox for this. Every call in the table below is an API call, so a reaction is a few tool calls, not a build.

Each fire carries every matching activity since the last one, so a burst is one run. A trigger never fires on the reacting agent's own activity or on a rehearsal's, so an agent never reacts to what it did. Never fire an agent on `MESSAGE_INSERTED` or on the run state kinds (`RUN_QUEUED`, `RUN_EXECUTED`, `RUN_PENDING`, `RUN_CANCELED`) without a tight `agent_ids` filter: every message and every state change of every run would land in its fires. A system outside the platform hears the same activities through a webhook subscription (`create_webhook`), which delivers each one as it happens.

## What the agent receives

The first message is the trigger's prompt, then the fire's payload as JSON:

- `since` and `until`: the hour, or so, it covers.
- `count`: how many activities matched, of which `activities` carries the newest hundred.
- Each activity: `id`, `type` (from the table below), `severity` (`BLOCKING`, `WARNING`, `INFO` or null), `table` and `record_id` (what it is about), `surfaced_at`, and `data`, the detail listed per kind below with the `run_id` and `agent_id` it names.

An activity may have been handled since it arrived: read its state with `get_activity` before acting on it, and read the record it is about with that record's own get operation.

## What each event admits

The right hand column names the operations that settle each kind. Read a run's conversation with `list_messages` filtered by `run_id`. Close an inbox card the agent handled on its own with `acknowledge_activity`. Where a person has to finish (a payment, an OAuth grant, a document), the agent's job is to mint the URL and deliver it to the right person: `start_conversation` on a channel reaches them over WhatsApp, Telegram or email, and `send_message` reaches the owner in their own conversation.

| Event | `data` | What the agent can do | Operations |
|---|---|---|---|
| `CHANNEL_WAITING` | `channel_id`, `contact_id`, `contact_name` | Read the held messages, judge the contact against the admission rules, admit or turn away. Leave it undecided when unsure and the card stays for a person. | `settle_waiting_run` with `decision` `approve` or `reject` |
| `RUN_FAILED` with `variant` `retry`, `grow_sandbox`, `fix_mcp`, `fix_model`, `maintenance`, `wrong_environment` | `variant` | Read the trace and the cost, fix the agent when the failure is its configuration (its model, for `fix_model`), then re-dispatch. | `get_run_trace`, `get_run_costs`, `update_agent`, `send_message` |
| `RUN_FAILED` with `variant` `update_payment`, `credit_topup`, `insufficient_credits` | `variant` | A record of one run parked on the balance or the payment method, with no severity. The workspace's one `CREDITS_EXHAUSTED` or `AUTO_PURCHASE_FAILED` row is what to act on. | |
| `RUN_WAITING` with `variant` `cost_guard` or `raise_limit` | `variant` | Raise the ceiling on the agent, or on this run alone, then re-dispatch. A message after a `cost_guard` card lets the run carry on past the guard. | `update_agent` or `update_run` with `config.credit_limit`, then `send_message` |
| `RUN_WAITING` with `variant` `insufficient_credits` | `variant` | As the payment variants of `RUN_FAILED`. | |
| `RUN_INTERRUPTED` on a question | | Answer it. | `send_message` |
| `RUN_INTERRUPTED` on a human handoff | | Speak as the human with `role` `OPERATOR`, or hand the conversation back to its agent with a USER post. | `send_message` |
| `RUN_INTERRUPTED` on a connection, an asset or a secret request | | Mint the OAuth URL for the owner, link the asset, store the secret. A browser step needs a person. | `create_connection`, `quote_asset` and `create_asset`, `create_secret` |
| `RUN_BLOCKED` | `blocker`, `run_id` | Read the blocker, fix the agent, run it again. | `update_agent`, `retry_run` |
| `RUN_ANOMALOUS` | `departures`, `reason` | The run departed from its agent's usual (its cost, its turns, its tool errors or what it answered) and a review judged it worth a look. Read the run, fix the agent when the departure is its doing, and close the card. | `get_run_trace`, `get_run_costs`, `update_agent`, `acknowledge_activity` |
| `RUN_DISLIKED` | `comment` when the person left one | A person gave the run a thumbs down. Read the run and the comment, fix the agent's prompt, or ask its owner what went wrong. | `get_run`, `list_messages`, `update_agent`, `send_message` |
| `LOW_CREDIT` | `credit_low`, `credit_high`, `credit_limit` | Get the checkout URL to the owner, or turn auto-recharge on when the owner has said so. | `create_checkout_session`, `update_billing` |
| `CREDITS_EXHAUSTED` | `runs`, `count`, `variants`, and `funded_at` once credits came back | Runs of the workspace wait on its balance. Without `funded_at`, mint the URL and get it to the owner: the subscription checkout while `get_billing` shows no `plan` (credits are sold only on one), the credit package checkout otherwise. With it, tell the owner the credits are back and how many runs wait: resuming them is a person's call, from the app. | `get_billing`, `create_checkout_session`, `send_message` |
| `AUTO_PURCHASE_FAILED` | `reason`, `workspace_id`, and `runs` and `count` for the runs parked until it is paid | On `limit_reached` the monthly cap is spent: raise `credit_limit` when the owner has said so, or ask them to. Otherwise get the portal URL to the owner, to add a card on `no_payment_method` or update it on `payment_failed`. | `update_billing`, `create_billing_portal_session` |
| `ASSET_RENEWAL_FAILED` | `reason` `renewal_error`, `invoice_id`, `renewal_id` | A renewal could not be processed and waits on the platform's operators. Nothing is owed yet, so tell the owner and leave it. | |
| `INTEGRATION_REAUTH` | `toolkit_slug` | Mint the reconnect URL and get it to the owner. | `create_connection` with the integration's `integration_id` |
| `CHANNEL_DISCONNECTED` | `channel_type`, `reason`, plus the channel's identifiers | A revoked or removed WhatsApp grant takes a new link from `create_connection` of `type` `WHATSAPP`, and a dropped LinkedIn account one of `type` `LINKEDIN`, sent to the owner. A Meta restriction, violation or ban is lifted by Meta alone, and a mailbox reconnects from the app, so brief the owner on those. | `create_connection`, `send_message` |
| `ENGINE_ACCOUNT_REFUSED` | `type` and `name` on an API account, `engine` on a subscription | One of the workspace's own AI accounts was refused, its key or token revoked or expired: an API key, a cloud tenancy or its Claude Code or Codex subscription. What ran on an API account moves to the next provider its configuration names and stops where none is left. A subscription's turns stop, or carry on with VibeTasking's subscriptions in credits where the agent, its preset or the run sets `critical`. Either holds until a person who manages the workspace's credentials sets the account again in the app's settings: tell the admins which account. | `send_message` |
| `WEBHOOK_FAILING` | | Read the subscription, then disable it or repoint it. | `get_webhook`, `update_webhook` |
| `EVALUATION_FAILED`, `EVALUATION_ERRORED` | `run_id` | Re-evaluate, tighten the case, or fix the prompt that failed it. | `evaluate_run` with `force`, `update_case`, `update_agent` |
| `TRIGGER_MISSED` | `expected_at` | Fire the run the schedule missed. | `fire_trigger` |
| `TRIGGER_LIMIT` | | Get the upgrade URL to the owner, re-enable the trigger once the plan changed. | `create_checkout_session`, `update_trigger` with `enabled` |
| `SECRET_REDACTED` | `kinds`, `sources` | Stop the run and tell the owner which credential to rotate. | `stop_run`, `send_message` |
| `SECRET_REFUSED` | `names`, `destination`, `surface`, and `credentials` (`vault_item`, `host`) when a host on a Vault item would open it | Add the host to the credential's hosts only when its owner confirms it. | `update_vault_item` or `update_secret` with the host in `data.allowed_hosts` |
| `SECRET_REJECTED` | `name`, `vault_item`, `host`, `status`, `error`, `description` | The token endpoint at `host` refused a TOKEN item's credential: a secret that expired or was revoked, a wrong client id, a scope it does not grant. Only a person holding a working credential can fix it, so tell the item's owner which item and what the endpoint said. It resolves itself once the endpoint hands out a token again. | `send_message` |
| `CALL_MISSED` | `contact_id`, `channel_id` | Call the contact back, or text a follow-up. | `place_call` on the voice channel, or `start_conversation` on a text one |
| `BUNDLE_UPDATED` | `status`, `failure_reason` or `valid_until` | Collect what the rejection asks for from the owner, then resubmit. | `add_bundle_document`, `submit_bundle` |
| `TOLLFREE_VERIFICATION_UPDATED` | `e164`, `status`, `rejection_reasons` | Resubmit the verification with the corrected answers. | `submit_tollfree_verification` |
| `STRIPE_ACCOUNT_UPDATED` | `charges_enabled`, `disabled_reason`, `currently_due` | Mint the onboarding link and get it to the owner. | `create_stripe_onboarding_link` |
| `STRIPE_DISPUTE_CREATED` | `dispute_id`, `amount`, `reason`, `evidence_due_by` | Read the dispute and brief the owner before the deadline. Evidence is submitted by a person in Stripe. | `list_stripe_disputes` |
| `AGENT_UNOWNED` | `profile_id`, `name` | The agent's author left the workspace, so its runs start without an owner and reach nothing a member owns. Who owns it next is a person's call: brief the admins with the agent's name. | `send_message` |
| `SUPERVISOR_STALLED` | `reason`, `overdue` | A supervisor stopped handling its agents' inbox items, which now reach their people. On `overdue`, on autonomous alone, it let items pass their deadline: list them, answer or close each, and it counts again. On `unseated` nobody seated owns it, as when the person it acts for left or support started it: an admin claims the run or gives it to a member. | `list_activities` with `holder_id` and `inbox`, `acknowledge_activity`, `update_run` with `profile_id` |
| `SUPPORT_ACCESSED` | `email` | VibeTasking staff opened a support session, which the workspace's support access setting allows: one activity per session, with no severity. Nothing to do unless the owner did not expect it: they switch support access off in the workspace's People settings. | none |
| `COST_DRIFT` | `direction`, `ratio`, the medians | Read the agent's recent runs and what they cost, then tighten its credit limit or model. | `list_runs`, `get_run_costs`, `update_agent` |
| `INSIGHT_RAISED` | `insight_id`, `title`, `body`, `suggestion` | Apply the suggestion or dismiss it. | `claim_insight`, `review_insight` (with the reviewed `prompt` for a prompt fix), `update_agent` |
| `RUN_COMPLETED`, with `agent_ids` set | | Chain the next step on the result. | `get_run`, `create_run` |
| `ENTITY_UPDATED` on an agent | `prompt` with `old` and `new` when the prompt changed | Review the edit, revert or approve it. | `list_edits`, `revert_change` |
| `ENTITY_CREATED` | | Check a new agent's configuration. | `get_agent`, `update_agent` |
| `ASSET_RELEASE_SCHEDULED` | `release_at`, `count`, `assets`, and on an unpaid renewal `reason` `renewal_missed`, `cause`, `credits_owed` | On `renewal_missed` one asset's renewal is unpaid, and the next credits the account gains pay it and lift the release: get a credit checkout URL to the owner before `release_at`, or raise the monthly limit on `cause` `limit_reached` when the owner has said so. Otherwise the plan ended: get the plan checkout URL to the owner before `release_at`, since taking a plan again cancels the release. | `get_billing`, `create_checkout_session`, `update_billing` |
| `SECRET_SHADOWED` | `ignored`, `kept` | Tell the owner which vault items reach the agent under one name, so they rename or unassign one. | `send_message` |

Everything else in the activity vocabulary is timeline only and admits no action.
