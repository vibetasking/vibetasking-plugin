---
name: vibetasking
description: Build, run and operate automations on the user's VibeTasking workspaces
  (agents, runs, integrations, channels, assets, triggers, data, billing, keys), from
  an MCP client or from a run's shell
---

# VibeTasking

VibeTasking is a cloud platform for building, refining, running, and monitoring agentic automations. Users brief LLM agents in natural language, and the platform runs them. An automation is made of agents, presets, integrations, channels, assets, triggers and webhooks, and a **run** is one execution of one. Through the platform's operations you author those resources, start and inspect runs, and read each resource through its own operations. A few values (a secret's plaintext, an API key's token, a webhook's signing secret) are answered once, when they are made, and never read back.

Every resource lives under a **workspace**. Your key acts as one profile, pinned to one workspace or reaching every workspace the profile belongs to.

This file is the map: how the operations reach you, where to start, which companion file covers which area, and how a new user or a client is set up. The companion files carry the body, one per area, each holding its area's contracts, which change as the platform does, so what you remember of one may no longer hold.

## Two surfaces, one vocabulary

The same operations reach you two ways, and every file here is written once for both:

- **From an MCP client** (Claude Code, Codex, any MCP host) each operation is a tool of the VibeTasking MCP, and the tool's schema is its contract. Skills and packages are fetched with `get_skill` and `get_skill_file`, `get_package` and `get_package_file`. A client that installed the VibeTasking plugin holds the platform's skills already, each companion file in the skill's own folder beside its `SKILL.md`.
- **From a run's shell** the same operations are actions of the `vibetasking` command: `vibetasking <action> --json '{...}'`, with `vibetasking <action> --help` as the contract and `vibetasking --help full` as the whole reference. Skills and packages are files in the sandbox under ``system/skills/`` and ``system/packages/``. A large body travels by file, ``--json-file body.json``, so it never has to survive shell quoting. ``$OCEAN_RUN_ID`` in the shell environment is your own run id, cheaper than `get_me` when that is all you need.

Reading rules that hold in every file:

- A name in single backticks (`create_run`, `list_agents`) is a platform operation: the MCP tool of that name, or `vibetasking <name>` from a run's shell. None of them is a tool of your own runtime.
- A name in double backticks (``shell_exec``, ``message_user``, ``create_run``) is a tool a run's agent holds, or a field or a value, named to describe that run from the outside.
- Where a file describes what a run's agent has and does, it describes a run from the outside. When you are yourself a run, the rest of your instructions describe what *you* have, and they win wherever the two differ.
- Where the two surfaces differ, the sentence says so in place, naming them "over the MCP" and "from a run". Eight things differ: how a file gets into or out of an entity, how a toolkit tool is called without a run, what delegating to a run buys, how a channel connection or a credential is requested from the user, where a skill's companion script lands, where a parameter contract lives, how a run you start tells you it settled, and whether you can start a supervision run.

## Where to start

- **Resolve your workspace and profile.** Call `get_me`: it returns the ``workspace_id``, ``profile_id``, and ``scopes`` your key is bound to, plus the ``workspaces`` and ``partners`` the profile belongs to (discovery, not the key's reach). Every ``workspace_id`` / ``profile_id`` argument must match the key's binding, and ``scopes`` tells you up front what the key may do (``null`` = unrestricted). When the key is bound to a run it also returns that run's ``run_id``, ``preset_id``, and ``agent_id``. That ``agent_id`` is the authoritative answer to which agent you are running, so use it rather than an id you read off the user's screen.
- **Discover presets.** `list_presets` lists the workspace's presets and the platform's, a platform preset carrying a null ``workspace_id``. A preset's ``config`` is what cascades into the run (``models``, ``language``, …). Pass the chosen ``preset_id`` to `create_agent`, or leave it unset so the agent follows the workspace's default preset (see **Choosing a tier** in `configuration.md`). A platform preset is read only to you, and a bare one-off run needs no preset at all (see **Choosing the delegation target** in `delegating.md`). A preset you create replaces the tier for its agents: copy into it the ``config.models`` of the tier they should run on (see **A preset you create** in `configuration.md`).
- **Identifiers come from listings.** `list_providers` searches what a workspace can connect (``q``, and ``category`` set to ``integration``, ``channel`` or ``asset``), each entry with the exact ``type`` its create takes and a ``tool_count`` as a hint of how many tools it carries. It does **not** embed the tools themselves. Integration entries do embed the event ``triggers`` the integration can fire agents from, each with the ``slug`` to pass as ``trigger_slug`` and, for Composio entries, the ``config_keys`` its ``trigger_config`` accepts, and this is the only place to discover them (see **Triggers** in `building.md`). An integration entry's ``connection`` says what connecting it takes: ``available`` connects as usual, ``unavailable`` means the platform cannot connect it through that provider yet and refuses its create, so turn to another entry for the same app or to **When a remote handshake fails** in `wiring.md`, and ``not_needed`` means runs use it with no integration at all.
- **Finding a toolkit's tools.** `list_toolkit_tools` takes a toolkit identifier as ``name`` (any backing: integration, asset, channel, or Composio/Pipedream slug) and lists that toolkit's tools, each tool's name and description (the names also being what a backing's tool rules and an approval's ``exempt`` take). When you know the job but not the toolkit, `search_tools` ranks the workspace's connected tools against a plain-language ``q``, each hit carrying its ``parameters`` schema and the instance it runs on. Pass ``provider`` (``NATIVE`` / ``COMPOSIO`` / ``PIPEDREAM``, from the `list_providers` entry) when the name exists under more than one, since an ambiguous name without it is rejected with the options. For ``MCP`` pass ``integration_id`` instead: the catalog lives on the connected server, so it's listed live per integration.
- **Calling one.** Over the MCP, `call_toolkit_tool` invokes one of those tools, the toolkit as ``name``, the tool as ``tool`` and its arguments in ``args``. From a run, the toolkit's own command in your sandbox runs one of those tools, once its backing is linked to this run (see **Calling a toolkit tool directly vs. delegating** in `delegating.md`).
- **Telling VibeTasking support.** When the person asks you to tell VibeTasking about something, or a fault of the platform's own stands between them and what they want, `send_support_message` writes it to the support team. Say what happened, what they expected instead, and every id it concerns (runs, agents, triggers, the workspace), so the team needs nothing copied over. From a run, the message opens this run's own conversation with the team, and each answer reaches you as a notice that starts your next turn, so carry on with the work it concerns once it arrives. Without a run it joins the person's own support conversation, where the team answers and they read the reply. The person approves that very message on its card before it goes.
- **Writing to a colleague.** When the person wants a colleague told or asked something, `send_note` leaves it in that colleague's inbox from the person, whoever writes it. The colleague sees it in the app and by push and email, and a Coordinator listening to their inbox passes it on. Say what the person wants them to know or answer, with every id it concerns, since they may open nothing else. The person approves that very note on its card, where they can change it, before it goes. The colleague answers on the note or through their Coordinator, and the answer reaches the person's inbox, and this run as a notice that starts its next turn, as a support answer does.
- **Read resources through their operations.** Every resource answers its own representation: `list_*` pages through it newest first and filters by the fields it declares, `get_*` reads one in full, and `expand` embeds a related row (`get_agent` with ``expand=preset``). There are no tables to inspect and no `data` bags to dig through: a field the representation does not answer is not part of the platform's surface. See **Reading resources** in `data.md` for paging, filters, merges and the error shape.
- **Writes are merges.** An `update_*` changes only the fields it is sent, a null clearing a field that may be cleared. Send ``If-Match`` with the ``etag`` you read to refuse a write when the row moved since, and an ``Idempotency-Key`` on a create or a start so a retried call never does the work twice (a run's own calls send theirs on their own).
- **Files.** Every file lives on a disk: a run's, an agent's, a preset's or a shared one. `get_run`, `get_agent` and `get_preset` list the disks they see under ``mounts``, each with its ``disk_id``, and `list_files` with a ``disk_id`` lists the files stored there, each with its ``id`` and its ``path`` (relative, e.g. ``downloads/report.xls``, ``path`` for one file, ``path_prefix`` for one folder). `get_file` takes that id as its ``file_id``. Over the MCP, `get_file` answers a short-lived link to fetch the bytes yourself: there is deliberately no raw-bytes tool, since bytes through a text tool channel would arrive corrupted. From a run, `get_file` with the ``file_id`` and an ``output_path`` lands the file in your sandbox. On either surface, when you need more than a couple of files, call `create_file_archive` instead: one link to a zip of a disk's files (``path_prefix`` narrows it to one folder), fetched (with ``curl`` from a run) and unzipped in a single round trip. Writing files is `agents.md`'s **Resource files**.

## The files

A file whose area needs a fact about the account says so: skip it while the fact does not hold, and read it once it does.

- `runs.md`: a run's lifecycle, starting and messaging runs, channel contacts, parking a message on a schedule, replay and abridging.
- `agents.md`: the agent as an authored object and its artifact files.
- `configuration.md`: presets, the run configuration keys, tiers and models, and where the workspace's AI runs.
- `wiring.md`: connecting integrations, assets and channels, WhatsApp numbers, voice agents and custom channels.
- `confidential.md`: keeping data out of the AI's reach when the person asks for it: an integration's protected fields, and a custom integration for an API no provider offers.
- `runtime.md`: how the agent executes inside a run, needed to read a trace and to write prompts in the runtime's own terms.
- `delegating.md`: delegating to a run, operating an asset by type, and choosing the delegation target.
  - Over the MCP, it also covers calling a toolkit tool directly instead.
- `data.md`: reading resources (paging, filters, expanding), merges and errors.
  - It also covers reaching a database asset's own project.
- `building.md`: the build and iterate loop, changing what existing agents do (their history first, a change tested on an ordinary input too, a check some agents cannot make), watching what runs (cases, standing approvals, a supervisor), the field rules, packages, writing agent prompts, fixing a misbehaving agent, routing agents and triggers.
- `webhooks.md`: a webhook to any HTTP destination: the ``filter`` expression that also narrows triggers, watches and MCP subscriptions, the request template, its escaping and secrets, previewing one, echo loops, and recipes for Slack, Discord, Teams and Google Chat.
  - Its recipes also cover PagerDuty, Linear, Twilio and a JSON API.
- `operations.md`: triage and the inbox, notifications, webhooks, API keys, removing what was connected, workspace members, a demo workspace's company record and the connect pages' branding, sharing, conventions and worked examples.
  - It also covers secrets and the Vault.
  - It also covers billing (plans and payment need the OWNER role, credits an ADMIN), referrals and partner tools (a partner membership).
- `sites.md`: web apps on a SITE asset, built one way: deploying and editing a site, its server code and secrets, signing people in through the database's auth and its email sender, data and files on the SUPABASE asset, calling the API from the app, and selling with the STRIPE asset.
- `disks.md`: named disks (what the app calls Knowledge), making and sharing them, attaching them to agents to read or write, searching their files and citing them, teaching them, and the brain and its curator.
- `app.md`: what a person does in the app and in the Chrome extension with no operation behind it: recording a task to show how it is done, the extension, connecting their own computer and putting an agent on it, dictating and talking with the Coordinator, taking over a channel conversation, the workspace's AI providers, and the Academy.

## First contact and billing

Then `get_billing` on the workspace you will act in: the plan, the account type and the spendable balance govern everything that follows, and a fresh account starts on a trial balance.

Everything runs on workspace credits, one credit being one cent ($0.01) of value.

Two shapes cover most users:

- **One workspace, one subscription.** The user builds for themselves, in their own workspace.
- **A builder working for clients.** The user builds automations for other companies. Each client gets its own workspace: `create_workspace` with the client's name, build there, then `create_invitation` to bring the client in as ``OWNER`` once the automation stands: the role you hold there too, so the client runs the workspace, its members and its billing beside you, and can release you. You are the new workspace's ``OWNER``, and a key across every workspace reaches it at once.

A key pinned to one workspace cannot create or reach another: client work needs a connection across every workspace, or a key minted with `create_key` and no ``workspace_id``. A demo account that was never signed up cannot create workspaces, invite members, mint keys or buy: those operations answer 403 until the account is claimed in the app, so send the user there first.

## Mentions

A **mention** is an inline reference to another platform object, written as ``@[NAME](ref:TYPE:ID)`` with the type lowercase, one of ``agent``, ``preset``, ``run``, ``integration``, ``channel``, ``asset``, ``folder``, ``vault`` (a vault item), ``trigger``, ``case`` (an evaluation case), ``insight``, ``disk`` for a named disk, and ``file`` for a file of one, whose id is the file's ``file_id`` with ``:<page>`` after it to open a PDF at that page, or ``@<second>`` to play a recording from that second (see `disks.md`). Any other shape is invalid. Mentions can appear in preset and agent prompts, in user messages, and in your own messages, and render as links in the app that open the object, each with the object's own icon beside its name (an agent's, preset's or folder's emoji, an integration's logo). Whenever your copy creates, changes, or discusses a specific platform object, write it as a mention rather than a bare name so it resolves to the real entity, in otherwise plain prose, and let the link carry the icon. A mention of an integration, asset, or channel carries that backing's id, which is also the ``--account <id>`` handle the agent passes to pick it when more than one of its type is connected. A mention of an agent carries the agent's id and doubles as the allow-list entry an ownerless run's ``create_run`` checks (see **Routing agents** in `building.md`).

---

Companion files, each in this skill's folder beside this file:
- agents.md
- app.md
- building.md
- confidential.md
- configuration.md
- data.md
- delegating.md
- disks.md
- operations.md
- runs.md
- runtime.md
- sites.md
- webhooks.md
- wiring.md

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
