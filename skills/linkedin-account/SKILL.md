---
name: linkedin-account
description: Direct messaging, connections, invitations both ways, people/company/job
  search, posts, and job postings through the workspace's connected LinkedIn account
  — the `linkedin` CLI (LinkedinToolkit, Unipile-backed). Not `composio linkedin`
  (OAuth company-page posting, a different account and action catalog) and not the
  browser-automation `linkedin` skill (session fallback for runs with no connected
  account).
---

# LinkedIn account (LinkedinToolkit)

The CLI is `linkedin` (bare, no `composio` prefix): `linkedin <action> --json '{...}'`,
`linkedin <action> --help` for a specific action's parameters. It reaches the LINKEDIN
channel or asset linked to this run through a clean Unipile-backed API — no browser to
drive.

## Two other things also answer to "linkedin" — don't try them first

- **`composio linkedin <action>`** is a *different* toolkit (`LinkedinComposioToolkit`,
  the official LinkedIn OAuth API) with its own connected account. This skill's toolkit
  now covers posting too, so reach for `composio linkedin` only when the workspace has
  that integration connected and no LINKEDIN seat, or for its ad-targeting and
  share-stats reads. If the task is messaging, connections, search, or invitations,
  the table below is the one you want and `composio linkedin --help` is a dead end.
- **`python system/skills/linkedin/run.py <action>`** is the browser-automation skill
  (`system/skills/linkedin/SKILL.md`). It covers runs with **no** connected account,
  plus what this toolkit cannot reach: company employees, the feed, and notifications.

## Actions

Conversation:

| action | args | returns / notes |
|---|---|---|
| `whoami` | — | own `member_id`, `name`, `public_identifier`, `headline`, `premium_features`, and the `organizations` (company pages) this account can act as — cheapest auth check |
| `list_conversations` | `limit` (default 20), `cursor` | inbox, most recent first: `chat_id`, `contact_member_id`, `name`, `unread`, `last_activity` |
| `get_conversation` | `limit` (default 20), `chat_id` | the messages of **this run's bound conversation**, oldest first, each with `from_me` and `message_id`. Pass `chat_id` (from `list_conversations`) to read a thread not bound to this run |
| `send_message` | `text` (req), `recipient` (member id, defaults to the run's bound contact), `subject` (InMail only) | picks the transport itself: a plain DM to a 1st-degree connection, InMail to anyone else while credits last. An InMail send reports `transport` and `inmail_credits_left` and spends one credit |
| `get_inmail_balance` | — | remaining InMail credits per pool (`premium`, `sales_navigator`, `recruiter`), null meaning no such subscription. Check it before sizing an outreach batch that reaches beyond 1st-degree connections |
| `send_file` | `file_path` (sandbox-relative, 15MB max), `recipient` | needs an existing chat — send a text message first if this conversation has none |
| `react_to_message` | `message_id` (req), `emoji` (req, the emoji itself) | react to a message in the conversation |
| `edit_message` | `message_id` (req), `text` (req) | own messages only, within 60 minutes of sending |
| `delete_message` | `message_id` (req) | own messages only, within 60 minutes of sending |

Profiles and search:

| action | args | returns / notes |
|---|---|---|
| `get_profile` | `identifier` (req: `/in/<handle>` slug or member id), `sections` (csv, e.g. `experience,education,skills`) | a member's profile |
| `get_company` | `identifier` (req: `/company/<name>` slug or organization id) | a company page's profile (description, industry, followers) |
| `search_people` | `keywords`, `url`, or `filters` (one required), `limit` (default 10), `cursor` | `{hits:[{member_id, name, headline, location, public_identifier, network_distance}], search, total, cursor}` — a null `cursor` means results are exhausted. `search` says which product ran, and a Sales Navigator or Recruiter hit carries `sales_navigator_id` or `recruiter_id` in place of `member_id` |
| `search_companies` | `keywords`, `url`, or `filters`, `limit`, `cursor` | company hits. `search` says which product ran |
| `search_jobs` | `keywords`, `url`, or `filters`, `limit`, `cursor` | job listings with `job_id`, `title`, `company`, `location`, `url` |
| `search_posts` | `keywords`, `url`, or `filters`, `limit`, `cursor` | posts matching the query by content |
| `list_search_parameters` | `type` (req: `LOCATION`, `INDUSTRY`, `COMPANY`, `SCHOOL`, `JOB_TITLE`, …), `keywords`, `category` (default `people`), `limit` | the `{id, title}` pairs a search `filters` field takes, scoped to the product the `category`'s search runs on |

Network and invitations:

| action | args | returns / notes |
|---|---|---|
| `list_relations` | `limit` (default 50), `cursor` | 1st-degree connections, newest first |
| `list_followers` | `limit` (default 50), `cursor` | who follows this account |
| `list_following` | `limit` (default 50), `cursor` | who this account follows |
| `send_invitation` | `member_id` (req), `note` (300 chars max) | connection request |
| `list_sent_invitations` | `limit` (default 50, 100 max) | pending sent invitations, each with `invitation_id` |
| `cancel_invitation` | `invitation_id` (req, from `list_sent_invitations`) | withdraw a stale invitation. LinkedIn blocks re-inviting the same person for weeks afterwards |
| `list_received_invitations` | `limit` (default 50) | pending invitations others sent this account, each with `invitation_id`, the inviter, and any note |
| `accept_invitation` | `invitation_id` (req) | accept — the sender becomes a 1st-degree connection |
| `decline_invitation` | `invitation_id` (req) | decline, without notifying the sender |
| `endorse_skill` | `member_id` (req), `skill_endorsement_id` (req, from `get_profile` with `sections="skills"`) | endorse one skill on a member's profile |

Posts:

| action | args | returns / notes |
|---|---|---|
| `create_post` | `text` (req), `file_paths` (sandbox-relative), `external_link`, `mentions`, `as_organization` | publish as the member, or as a company page with an organization id from `whoami` |
| `list_posts` | `identifier` (defaults to the account itself), `is_company`, `limit`, `cursor` | a member's or company page's posts with counters |
| `get_post` | `post_id` (req) | one post's text and counters |
| `comment_on_post` | `post_id` (req), `text` (req), `reply_to_comment_id`, `mentions`, `as_organization` | comment, or reply to a comment |
| `react_to_post` | `post_id` (req), `reaction` (like/celebrate/support/love/insightful/funny), `comment_id`, `as_organization` | react to a post or one of its comments |
| `list_post_comments` | `post_id` (req), `comment_id`, `limit`, `cursor` | a post's comments, or a comment's replies |
| `list_post_reactions` | `post_id` (req), `comment_id`, `limit`, `cursor` | who reacted and how |
| `list_member_comments` | `identifier` (req), `limit`, `cursor` | comments a member has written |
| `list_member_reactions` | `identifier` (req), `limit`, `cursor` | reactions a member has left |

Jobs and recruiting (job postings work on any account; pipeline actions need Recruiter,
`save_lead` needs Sales Navigator):

| action | args | returns / notes |
|---|---|---|
| `list_job_postings` | `category` (active/draft/closed), `limit`, `cursor` | the account's job postings |
| `create_job_posting` | `title`, `location`, `workplace` (ON_SITE/HYBRID/REMOTE), `description` (all req), `company_name` or `company_id`, `employment_status`, `screening_questions`, `auto_rejection_template` | creates a **draft**, nothing goes live |
| `get_job_posting` | `job_id` (req), `service` (CLASSIC/RECRUITER) | state, counters, cost |
| `edit_job_posting` | `job_id` (req) + any create field | only passed fields change |
| `publish_job_posting` | `draft_id` (req), `mode` (FREE default), `budget` | **PROMOTED modes spend the company's real LinkedIn job budget** — only with the user's explicit ask and budget |
| `solve_job_checkpoint` | `draft_id` (req), `code` (req) | answer the verification code LinkedIn emails on publish |
| `close_job_posting` | `job_id` (req), `service` | close a live posting |
| `list_job_applicants` | `job_id` (req), `keywords`, `sort_by`, `limit`, `cursor` | applicants with `profile_id` and rating |
| `get_job_applicant` | `applicant_id` (req) | full record: contact info, work experience |
| `download_applicant_resume` | `applicant_id` (req) | saves the resume into the sandbox, returns the path |
| `save_lead` | `member_id` (req), `list_id` | save as a Sales Navigator lead |
| `add_candidate_to_pipeline` | `member_id` (req), `hiring_project_id` (req), `stage`, `applicant` | add to a Recruiter hiring project |
| `move_candidate_stage` | `member_id`, `hiring_project_id`, `stage` (all req) | UNCONTACTED/CONTACTED/REPLIED |
| `reject_applicant` | `member_id`, `hiring_project_id`, `reason` (all req), `message` | optionally notifies the applicant |
| `list_hiring_projects` | `limit`, `cursor` | Recruiter hiring projects |
| `get_hiring_project` | `project_id` (req) | one project, with its job posting |

`recipient`/`member_id` everywhere takes a LinkedIn member id (`ACoAA…`), a Sales Navigator
id (`ACwAA…`), or a `/in/<handle>` vanity slug. The last two are resolved to the member id
for you, at the cost of one profile read, so pass a member id when you already hold one.
Relations, invitations and profiles always report the member id, so a Sales Navigator id
never matches them: key people you store by `public_identifier`, or by the member id
`get_profile` returns.

## Search products

`search_people` runs on **Sales Navigator** when the account subscribes to it, else
**Recruiter**, else LinkedIn's **classic** search, and the result's `search` key says
which one ran. `search_companies` runs on Sales Navigator or classic. Jobs and posts
only exist on classic.

Faceted searches take a `filters` object in the running product's shape: classic
takes arrays of ids (`{"location": ["102299470"], "network_distance": [1]}`), Sales
Navigator include/exclude objects (`{"location": {"include": ["102299470"]}}`).
Resolve the ids with `list_search_parameters` first, passing the same `category` you
are about to search, since ids are scoped per product too.

## Company-page channels

A channel bound to one of the account's company pages replies as that page, and a page
can only answer people who wrote to it first, so on such a channel `send_message` never
opens new conversations and the invitation and search actions are absent. Posting as the
page works from anywhere via `as_organization`.

## Limits

LinkedIn caps invitations at roughly 80-100/day on paid accounts (~5/month on free
accounts with a note attached); profile reads are safe up to about 100/day. A 429 raises
as a rate-limit retry telling you to stop that action type for now rather than retry —
respect it instead of looping.
