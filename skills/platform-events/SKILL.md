---
name: platform-events
description: Make an agent react to platform events (a stranger waiting at a gated
  channel, a failed run, a low balance, a new finding) by pointing a webhook subscription
  at the agent's own inbound webhook trigger, with what each event admits and which
  tool does it
---

# Reacting to platform events

Every notable thing that happens in a workspace lands as an `activities` row: a contact parked by a channel's waiting room, a run that failed or paused, a balance running low, a finding the brain raised. Webhook subscriptions push those rows to a URL. An agent's inbound webhook trigger turns any POST to its URL into a run. Point the first at the second and the agent reacts to the event.

## Wiring it

1. Give the reacting agent an inbound webhook trigger: `upsert_trigger` with `agent_id` and `data` `{"webhook": {}}`. Keep the `webhook_url` from the response (`get_trigger_webhook` re-serves it).
2. Subscribe to the events: `upsert_webhook` with the workspace, `url` set to that `webhook_url`, `activity_types` naming only the kinds the agent handles, and `agent_ids` naming the agents whose runs it watches. Create the subscription as the owner of the watched agents (or make them public), since a run-tied event reaches a subscription only when its profile may see that run.
3. Write the agent's prompt around the events it receives: what each kind means, what to check, which tool settles it, and when to leave it to a person. The agent needs no sandbox for this. Every call in the table below is an API call, so a reaction is a few tool calls, not a build.

Each matching event starts one run with the delivery as the first message. Deliveries fire once and never retry, and a trigger accepts sixty per minute. When a burst of events should be handled by one run, set `coalesce_seconds` on the trigger.

Never subscribe an agent to `MESSAGE_INSERTED` or to the run state kinds (`RUN_QUEUED`, `RUN_EXECUTED`, `RUN_PENDING`, `RUN_CANCELED`) without a tight `agent_ids` filter: every message and every state change of every run would start a reaction. The platform drops a delivery whose subject is the reacting agent itself or one of its own runs, so an agent never reacts to what it did, but a subscription that watches everything still costs a run per event.

## What the agent receives

The first message is the delivery as JSON:

- `activity_type`: the kind, from the table below.
- `lifecycle`: `opened` when the event is new, `acknowledged` or `resolved` when a member or the platform closed it. React to `opened` and ignore the rest unless the prompt says otherwise.
- `severity`: `BLOCKING`, `WARNING`, `INFO` or null.
- `table_name` and `record_id`: what the event is about, and `record`, that row in full (a run, an agent, a billing account, an asset, a channel).
- `data`: the event detail that is not on the row, listed per kind below.
- `workspace_id`, `profile_id`, `created_at`.

## What each event admits

The right hand column names the operations that settle each kind. Read a run's conversation with `query_data` on `messages` filtered by `run_id`. Close an inbox card the agent handled on its own with `acknowledge_inbox_item`. Where a person has to finish (a payment, an OAuth grant, a document), the agent's job is to mint the URL and deliver it to the right person: `start_run` with a `contact_id` on a channel agent reaches them over WhatsApp, Telegram or email, and `send_message` reaches the owner in their own conversation.

| Event | `data` | What the agent can do | Operations |
|---|---|---|---|
| `CHANNEL_WAITING` | `channel_id`, `contact_id`, `contact_name` | Read the held messages, judge the contact against the admission rules, admit or turn away. Leave it undecided when unsure and the card stays for a person. | `waiting_decision` with `approve` or `reject` |
| `RUN_FAILED` with `variant` `retry`, `grow_sandbox`, `fix_mcp`, `maintenance`, `wrong_environment` | `variant` | Read the trace and the cost, fix the agent when the failure is its configuration, then re-dispatch. | `get_run_trace`, `get_run_costs`, `upsert_agent`, `send_message` |
| `RUN_FAILED` with `variant` `update_payment`, `credit_topup`, `insufficient_credits` | `variant` | Mint the URL and get it to the owner: the subscription checkout while `billing_status` shows no `plan` (credits are sold only on one), the credit package checkout or the portal otherwise. | `billing_status`, `billing_checkout`, `billing_portal` |
| `RUN_WAITING` with `variant` `cost_guard` or `raise_limit` | `variant` | Raise the ceiling on the agent, or on this run alone, then re-dispatch. | `upsert_agent` with `data_patch.credit_limit`, or `call_rpc` `merge_run_data` with `a_run_id` and `a_patch` `{"credit_limit": n}` or `{"cost_guard_ack": true}`, then `send_message` |
| `RUN_WAITING` with `variant` `insufficient_credits` | `variant` | As the payment variants of `RUN_FAILED`. | `billing_checkout` |
| `RUN_INTERRUPTED` on a question | | Answer it. | `send_message` |
| `RUN_INTERRUPTED` on a human handoff | | Speak as the human with `role` `OPERATOR`, or hand the conversation back to its agent with a USER post. | `send_message` |
| `RUN_INTERRUPTED` on a connection, an asset or a secret request | | Mint the OAuth URL for the owner, link the asset, store the secret. A browser step needs a person. | `upsert_integration`, `upsert_asset`, `upsert_secret` |
| `RUN_BLOCKED` | `blocker`, `run_id` | Read the blocker, fix the agent, run it again. | `upsert_agent`, `start_run` |
| `LOW_CREDIT` | `credit_low`, `credit_high`, `credit_limit` | Get the checkout URL to the owner, or turn auto-recharge on when the owner has said so. | `billing_checkout`, `billing_recharge_update` |
| `AUTO_PURCHASE_FAILED` | `reason`, `workspace_id` | Get the portal URL to the owner. | `billing_portal` |
| `ASSET_RENEWAL_FAILED` | `reason`, `credits_required`, `credits_available` | Get the portal URL to the owner, or release the asset when it is no longer wanted. | `billing_portal`, `upsert_asset` |
| `INTEGRATION_REAUTH` | `toolkit_slug` | Mint the reconnect URL and get it to the owner. | `upsert_integration` |
| `CHANNEL_DISCONNECTED` | `channel_type`, `reason`, plus the channel's identifiers | Mint the reconnect link for the channel's type and get it to the owner. | `whatsapp_connect_link`, `instagram_connect_link`, `messenger_connect_link`, `slack_connect_link`, `linkedin_connect_link` |
| `WEBHOOK_FAILING` | | Read the recent `deliveries`, then disable the subscription or repoint it. | `query_data`, `upsert_webhook` |
| `EVALUATION_FAILED`, `EVALUATION_ERRORED` | `run_id` | Re-evaluate, tighten the case, or fix the prompt that failed it. | `evaluate_run` with `force`, `upsert_case`, `upsert_agent` |
| `TRIGGER_MISSED` | `expected_at` | Fire the run the schedule missed. | `start_run` with `agent_id` |
| `TRIGGER_LIMIT` | | Get the upgrade URL to the owner, re-enable the trigger once the plan changed. | `billing_checkout`, `upsert_trigger` with `enabled` |
| `SECRET_REDACTED` | `kinds`, `sources` | Stop the run and tell the owner which credential to rotate. | `stop_run`, `send_message` |
| `SECRET_REFUSED` | `names`, `destination`, `surface`, and `credentials` (`vault_item`, `host`) when a host on a Vault item would open it | Add the host to the credential's hosts only when its owner confirms it. | `upsert_vault_item` or `upsert_secret` with `allowed_hosts` |
| `CALL_MISSED` | `contact_id`, `channel_id` | Call the contact back, or text a follow-up. | `start_run` with `contact_id` on a voice or text channel agent |
| `BUNDLE_UPDATED` | `status`, `failure_reason` or `valid_until` | Collect what the rejection asks for from the owner, then resubmit. | `POST /public/bundles/{bundle_id}/documents`, `POST /public/bundles/{bundle_id}/submit` |
| `TOLLFREE_VERIFICATION_UPDATED` | `e164`, `status`, `rejection_reasons` | Resubmit the verification with the corrected answers. | `submit_tollfree_verification` |
| `STRIPE_ACCOUNT_UPDATED` | `charges_enabled`, `disabled_reason`, `currently_due` | Mint the onboarding link and get it to the owner. | `stripe_onboarding_link` |
| `STRIPE_DISPUTE_CREATED` | `dispute_id`, `amount`, `reason`, `evidence_due_by` | Read the dispute and brief the owner before the deadline. Evidence is submitted by a person in Stripe. | `get_stripe_disputes` |
| `COST_DRIFT` | `direction`, `ratio`, the medians | Read the agent's recent `charges`, then tighten its credit limit or model. | `query_data`, `upsert_agent` |
| `INSIGHT_RAISED` | `insight_id`, `title`, `body`, `suggestion` | Apply the suggestion or dismiss it. | `claim_insight`, `upsert_agent`, `review_insight` |
| `BRAIN_DIGEST` | `headlines`, `new`, `open` | Read the findings and hand one to the right agent. | `GET /public/brain/findings`, `POST /public/brain/findings/{finding_id}/handoff` |
| `RUN_COMPLETED`, with `agent_ids` set | | Chain the next step on the result. | `get_run_status`, `start_run` |
| `ENTITY_UPDATED` on an agent | `prompt` with `old` and `new` when the prompt changed | Review the edit, revert or approve it. | `upsert_agent` |
| `ENTITY_CREATED` | | Check a new agent's configuration. | `upsert_agent` |

Everything else in the activity vocabulary is timeline only and admits no action.
