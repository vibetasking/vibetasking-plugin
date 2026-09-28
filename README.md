# VibeTasking

[VibeTasking](https://vibetasking.com) is a cloud platform for building, running and monitoring agentic automations. People brief AI agents in plain language, and the platform runs them with the tools, integrations, channels and sandboxes the work needs.

This plugin connects your AI assistant to your VibeTasking account and teaches it how to operate the platform. With it, the assistant can create and refine agents, connect integrations and channels, start and inspect runs, read and write your workspace data, and set up workspaces, keys and billing for you.

## What it contains

- **The VibeTasking connector.** A remote MCP server at `https://api.vibetasking.com/mcp`. You sign in with your VibeTasking account the first time the assistant uses it, and you choose which workspace and permissions the connection gets. Every call acts on your account through that grant, and you can revoke it at any time from your API keys in the app.
- **Skills.** The `vibetasking` skill is the operating guide: the mental model, where to start, and one companion file per area (runs, agents, configuration, wiring, runtime, delegating, data, building, operations, brain, external agents). The other skills cover the toolkits the platform runs for you, such as documents, spreadsheets, presentations, Gmail, Slack and Google Drive.

## Install

- **Claude**: add VibeTasking from the directory under Customize, in claude.ai or the desktop app. It then works in chat, Cowork and Claude Code.
- **Other assistants**: this repository follows the [Agent Plugins](https://agent-plugins.org) format (`plugin.json`, `mcp.json` and `skills/` at the root), so any client that reads it can install the plugin from here.
- **Connector only**: any MCP client can add `https://api.vibetasking.com/mcp` as a remote server and sign in. The skills are then served by the connector itself.

## What it sends and where

The skills are text and scripts installed on your machine. Some skills carry helper scripts (for example to validate a generated document) that run locally, and only when the assistant runs them. The connector sends the requests the assistant makes to `api.vibetasking.com`, which acts on your VibeTasking account under the permissions you granted. Nothing else is sent anywhere.

## Privacy and support

- Privacy policy: https://vibetasking.com/privacy
- Terms: https://vibetasking.com/terms
- Support: info@vibetasking.com

This repository is generated from the VibeTasking platform's own skills on every release. Changes made here directly are overwritten.
