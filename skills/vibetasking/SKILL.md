---
name: vibetasking
description: Build, run and operate automations on the user's VibeTasking workspaces
  (agents, runs, integrations, channels, assets, triggers, data, billing, keys), from
  an MCP client or from a run's shell
---

# VibeTasking

VibeTasking is a cloud platform for building, refining, running, and monitoring agentic automations. Users brief LLM agents in natural language, and the platform runs them. An automation is made of agents, presets, integrations, channels, assets, triggers and webhooks, and a **run** is one execution of one. Through the platform's operations you author those resources, start and inspect runs, and read or mutate most of the underlying tables directly. A few resources (secrets, API keys, webhook secrets) are reachable only through their dedicated operations.

Every resource lives under a **workspace**. Your key acts as one profile, pinned to one workspace or reaching every workspace the profile belongs to.

This file is the map: how the operations reach you, where to start, which companion file covers which area, and how a new user or a client is set up. The companion files carry the body, one per area. Read this file first, then the file an ask needs before acting on that area.

## Two surfaces, one vocabulary

The same operations reach you two ways, and every file here is written once for both:

- **From an MCP client** (Claude Code, Codex, any MCP host) each operation is a tool of the VibeTasking MCP, and the tool's schema is its contract. Skills and packages are fetched with `get_skill` and `get_skill_file`, `get_package` and `get_package_file`. A client that installed the VibeTasking plugin holds the platform's skills already, each companion file in the skill's own folder beside its `SKILL.md`.
- **From a run's shell** the same operations are actions of the `vibetasking` command: `vibetasking <action> --json '{...}'`, with `vibetasking <action> --help` as the contract and `vibetasking --help full` as the whole reference. Skills and packages are files in the sandbox under ``system/skills/`` and ``system/packages/``. A large body travels by file, ``--json-file body.json``, so it never has to survive shell quoting. ``$OCEAN_RUN_ID`` in the shell environment is your own run id, cheaper than `get_me` when that is all you need.

Reading rules that hold in every file:

- A name in single backticks (`start_run`, `query_data`) is a platform operation: the MCP tool of that name, or `vibetasking <name>` from a run's shell. None of them is a tool of your own runtime.
- A name in double backticks (``shell_exec``, ``message_user``, ``start_run``) is a tool a run's agent holds, or a field or a value, named to describe that run from the outside.
- Where a file describes what a run's agent has and does, it describes a run from the outside. When you are yourself a run, the rest of your instructions describe what *you* have, and they win wherever the two differ.
- Where the two surfaces differ, the sentence says so in place, naming them "over the MCP" and "from a run". Six things differ: how a file gets into or out of an entity, how a toolkit tool is called without a run, what delegating to a run buys, how a channel connection or a credential is requested from the user, where a skill's companion script lands, and where a parameter contract lives.

## Where to start

- **Resolve your workspace and profile.** Call `get_me`: it returns the ``workspace_id``, ``profile_id``, and ``scopes`` your key is bound to, plus the ``workspaces`` and ``partners`` the profile belongs to (discovery, not the key's reach). Every ``workspace_id`` / ``profile_id`` argument must match the key's binding, and ``scopes`` tells you up front what the key may do (``null`` = unrestricted). When the key is bound to a run it also returns that run's ``run_id``, ``preset_id``, and ``agent_id``. That ``agent_id`` is the authoritative answer to which agent you are running, so use it rather than an id you read off the user's screen.
- **Discover system presets.** `query_data` on ``presets`` filtered by ``workspace_id is null`` returns the global system presets your agents can attach to. The preset's ``data`` is what cascades into the run (``model``, ``reasoning_effort``, ``fallback_models``, ``language``, …). Pass the chosen ``preset_id`` to `upsert_agent`, or leave it unset so the agent follows the workspace's default preset (see **Choosing a tier** in `configuration.md`). You don't need to write the preset row (it's read-only to tenants), and you don't need a preset at all for a bare one-off run (see **Choosing the delegation target** in `delegating.md`).
- **Don't guess identifiers.** Discovery is a **three-step flow**. (1) `find_providers` searches integrations, channels, and assets and returns the exact ``type``/identifier to pass to upsert endpoints, plus a ``tool_count`` per integration as a hint of how many tools it carries. It does **not** embed the tools themselves. Integration entries do embed the event ``triggers`` the integration can fire agents from, each with the ``slug`` to pass as ``trigger_slug`` and, for Composio entries, the ``config_keys`` its ``trigger_config`` accepts, and this is the only place to discover them (see **Triggers** in `building.md`). (2) `list_toolkit_tools` takes a toolkit identifier as ``name`` (any backing: integration, asset, channel, or Composio/Pipedream slug) and lists that toolkit's tools, each tool's name and description (the names also being what ``tool_policies`` accepts). Pass ``provider`` (``NATIVE`` / ``COMPOSIO`` / ``PIPEDREAM``, from the `find_providers` entry) when the name exists under more than one, since an ambiguous name without it is rejected with the options. For ``MCP`` pass ``integration_id`` instead: the catalog lives on the connected server, so it's listed live per integration. (3) Over the MCP, `call_toolkit_tool` invokes one of those tools, the toolkit again as ``name`` and the tool as ``tool``. From a run, the toolkit's own command in your sandbox runs one of those tools, once its backing is linked to this run (see **Calling a toolkit tool directly vs. delegating** in `delegating.md`).
- **A tool you don't see.** Over the MCP, the tools are grouped into toolsets, and the URL a connection was added with picks which groups it serves: its ``toolsets`` parameter names them, comma separated, and a URL without it serves every group. With no tool for an ask, call `list_toolsets` before answering that it cannot be done, then act on what it reports:
  - A group not ``exposed`` was left out of the URL, which lives in the client's own MCP configuration, so authorizing, signing in or adding the account again changes nothing. When you can write files, edit that entry yourself: search the configuration for ``vibetasking`` (``.mcp.json`` in the project, or the client's own file such as ``~/.codex/config.toml``, ``.cursor/mcp.json``, ``.vscode/mcp.json``, ``~/.config/opencode/opencode.json``), set the URL's ``toolsets`` to the groups the user needs or drop the parameter, then say what you changed and ask the user to reconnect this MCP, since a client lists the tools only at connect. On a web client or a managed connector, give the user the whole URL to save instead, the reported ``url`` with ``?toolsets=`` and the groups they want, and say it replaces the URL their client holds.
  - A group ``exposed`` whose tools are still missing from your tool list means the client cached an older catalog. Ask the user to reconnect this MCP (in Claude Code, ``/mcp`` and reconnect, in Claude.ai, switch the connector off and on). The connection stays authorized.
  - A group ``exposed`` but not ``available`` keeps its tools in the catalog, and their calls fail until the fact its ``rule`` names holds. Some facts you can bring about yourself (`upsert_asset` for a Stripe, Site or LinkedIn asset, `upsert_agent` with ``engine`` ``EXTERNAL``), others the user or the platform does (an OWNER or ADMIN role, the partner program, the company's brain).
- **Inspect data shapes** with `describe_schema` before reading or writing tables. Column descriptions come from the database itself. Call it before your **first** `query_data` on a table instead of guessing a projection: most fields live inside the ``data`` JSON, not as columns (``integrations`` has no ``name`` column, nor ``data->>'name'``, keyed by ``type``/``provider``, while ``assets`` has no ``name`` column either but does carry one at ``data->>'name'``), and enum values are exact (``provider`` is ``NATIVE``/``COMPOSIO``/``PIPEDREAM``, never a service name). ``agents`` has no ``triggers`` column (triggers are rows on the ``triggers`` table, filtered by ``agent_id``).
- For ad-hoc reads/writes use the Data tools (`query_data`, `insert_data`, `update_data`, `delete_data`, and `call_rpc` for Postgres functions). See **Reading and writing data** in `data.md` for the query syntax and gotchas. Bulk-mutating runs, billing, or other live state through these is rarely the right move. Prefer the dedicated endpoints.
- **Files.** Call `list_files_in_entity` to discover the exact paths stored on a run/preset/agent (paths are relative, e.g. ``downloads/report.xls``). Over the MCP, then call `get_download_url` to obtain a short-lived signed URL and fetch the bytes yourself: there is deliberately no raw-bytes download tool, since bytes through a text tool channel would arrive corrupted. From a run, `download_file_from_entity` with that ``path`` lands the file in your sandbox (``output_path`` picks where). On either surface, when you need more than a couple of files, call `get_archive_url` instead: one signed URL for a zip of the entity's files (``prefix`` narrows it to one directory), fetched (with ``curl`` from a run) and unzipped in a single round trip.

## The files

A file whose area needs a fact about the account says so: skip it while the fact does not hold, and read it once it does.

- `runs.md`: a run's lifecycle, starting and messaging runs, channel contacts, parking a message on a schedule, replay and abridging.
- `agents.md`: the agent as an authored object and its artifact files.
- `configuration.md`: presets, the run configuration keys, tiers and models.
- `wiring.md`: connecting integrations, assets and channels, WhatsApp numbers, voice agents and custom channels.
- `runtime.md`: how the agent executes inside a run, needed to read a trace and to write prompts in the runtime's own terms.
- `delegating.md`: calling a toolkit tool directly versus delegating to a run, operating an asset by type, and choosing the delegation target.
- `data.md`: reading and writing platform rows, and reaching a database asset's own project.
- `building.md`: the build and iterate loop, the field rules, packages, writing agent prompts, fixing a misbehaving agent, routing agents and triggers.
- `operations.md`: secrets and the Vault, triage and the inbox, webhooks, API keys, billing (its account operations need an OWNER or ADMIN role), removing what was connected, workspace members, the company record, sharing, partner tools (a partner membership), conventions and worked examples.
- `brain.md`: the company brain, when the workspace's company has one.
- `external.md`: being an agent on the platform with your own harness, and acting inside a turn. The file for a turn key of an EXTERNAL agent's run, and the one to skip otherwise.

## First contact and billing

Start every session with `get_me`. It names your profile, the workspace the key is pinned to (``null`` for a key across every workspace), the ``workspaces`` the profile belongs to with the role held in each, and the ``partners`` it belongs to. Then `billing_status` on the workspace you will act in: the plan, the account type and the spendable balance govern everything that follows, and a fresh account starts on a trial balance. Everything runs on workspace credits, one credit being one cent ($0.01) of value.

Two shapes cover most users:

- **One workspace, one subscription.** The user builds for themselves. Build in their workspace. When the balance or the plan becomes the blocker, `list_plans` explains the plans and the credit packages with their prices, credits and run concurrency, then one `billing_checkout` link the user opens: the hosted checkout is the whole billing screen, and `billing_portal` manages the subscription and payment methods afterwards. Credit packages are sold only on an active subscription, so a workspace without a plan gets the subscription checkout. Nothing is charged by the calls themselves.
- **A builder working for clients.** The user builds automations for other companies. Each client gets its own workspace: `create_workspace` with the client's name, build there, then `invite_member` to bring the client in as ``ADMIN`` once the automation stands: the role you hold there too, and the highest an invitation grants, so the client runs the workspace, its members and its billing beside you. You are the new workspace's ``ADMIN``, and a key across every workspace reaches it at once. Billing takes one of two shapes, the user's decision: the client's own billing, the default, where you hand the client a `billing_checkout` link for their workspace, or the builder's own subscription backing every client workspace, by passing ``share_billing_with`` on `create_workspace` (a workspace whose billing you administer), so one subscription and one balance serve all of them and each keeps its own run concurrency. What the builder charges the client stays between them. A builder who belongs to a partner organisation passes ``partner_id`` too, which is what turns on the partner program's commission or pricing for that client (see **Partner tools** in `operations.md`).

A key pinned to one workspace cannot create or reach another: client work needs a connection across every workspace, or a key minted with `create_key` and no ``workspace_id``. A demo account that was never signed up cannot create workspaces, invite members, mint keys or buy: those operations answer 403 until the account is claimed in the app, so send the user there first.

## Mentions

A **mention** is an inline reference to another platform object, written as ``@[NAME](ref:TYPE:ID)`` with the type lowercase, one of ``agent``, ``preset``, ``run``, ``integration``, ``channel``, ``asset``, ``folder``, ``vault`` (a vault item), ``trigger``, ``case`` (an evaluation case), ``insight``. Any other shape is invalid. Mentions can appear in preset and agent prompts, in user messages, and in your own messages, and render as links in the app that open the object, each with the object's own icon beside its name (an agent's, preset's or folder's emoji, an integration's logo). Whenever your copy creates, changes, or discusses a specific platform object, write it as a mention rather than a bare name so it resolves to the real entity, in otherwise plain prose, and let the link carry the icon. A mention of an integration, asset, or channel carries that backing's id, which is also the ``--account <id>`` handle the agent passes to pick it when more than one of its type is connected. A mention of an agent carries the agent's id and doubles as the ``run_agent`` allow-list entry (see **Routing agents** in `building.md`).

---

Companion files, each in this skill's folder beside this file:
- agents.md
- brain.md
- building.md
- configuration.md
- data.md
- delegating.md
- external.md
- operations.md
- runs.md
- runtime.md
- wiring.md

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
