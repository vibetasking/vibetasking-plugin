# Web apps on a SITE asset

A SITE asset is a hosted website the platform runs on Cloudflare, served at the address in its ``url`` and at each of its ``data.domains`` hostnames under the platform's own domains. The platform deploys it, lists its deployments and keeps its secrets through the operations below. Use it for anything the user wants on the web: a landing page, a dashboard, a full app with sign in, a database and agentic features. Every app here is built the same way:

- **Pages and server code** on the SITE asset: its static files, plus a ``_worker.js`` or ``functions/`` for anything secret or privileged (**Server code**).
- **Sign in, data and files** on the workspace's SUPABASE asset: its auth signs people in, its Postgres holds the data behind row level security, and its storage keeps the files (**Signing people in**, **Data**, **Files**).
- **Agentic features** through the VibeTasking API, called from the server code with a key the site holds (**Calling the VibeTasking API from the app**).
- **Payments** through the workspace's STRIPE asset (**Selling on the site**).

An app never keeps its own passwords, sessions, signed cookies or code tables, never stores data in its secrets or in a spreadsheet it fetches, and never uses a SITE asset to hold files for another site. A shared password is for a throwaway preview only. One SUPABASE asset serves every app of a workspace, each app's tables named after it, so a new app asks for a database only when the workspace has none (`quote_asset` and `create_asset`, a priced asset the user confirms). When the user brings a Supabase project of their own, build on it the same way, in ``eu-central-1`` unless they are elsewhere.

## Where to host

Deploying needs a SITE asset. When one already fits the user's ask (judge by its name against what they want built), deploy to that one rather than provisioning a second. Provision a new one when nothing fits or the user wants a distinct site. A site costs nothing to hold, so provisioning needs no confirmation. Ask first only when the ask is ambiguous about where it should live.

## Where the source lives

From a run, each SITE asset has a folder of its own, ``sites/<reference>/`` (its ``reference`` is the site's name), in every conversation the asset reaches: linked to the agent, its preset or this conversation, or made by it. A site this conversation does not reach yet comes in when you link it (`add_run_asset` with your own ``run_id``, ``$OCEAN_RUN_ID`` in your shell, and the asset's id): its folder appears at once, holding the source. Work in that folder rather than rebuilding one from an archive or a bundle, which leaves the copy in this conversation's own files where the site never sees it. The source is saved as you work, so the next conversation that works on the site starts from what you left, and the asset's history keeps every version. A new site starts with an empty folder. Build output never goes there: build into ``.scratch/sites/<reference>/``, which no disk keeps and no reply carries (each deploy keeps its own bundle), and deploy that. A conversation with no person behind it reads the folder and cannot change it.

Over the MCP, start from the served bundle (`get_site_bundle_url`), edit, zip and deploy it, as **Operating an asset by type** in `delegating.md` says.

## Deploying

`deploy_site` with the asset's id publishes built output as the new production version. From a run it takes the sandbox ``directory`` of that output, saves ``sites/<reference>/`` and zips the directory itself. The site and the Cloudflare account it runs on are the platform's, never yours to name. `list_site_deployments` lists the history, and `rollback_site_deployment` with a deployment id from it serves an earlier one again, or redeploy fixed output.

- Build from ``sites/<reference>/`` into ``.scratch/sites/<reference>/`` and deploy that **built output directory**, the folder with ``index.html`` at its root, never the source tree. With Vite: ``npm run build -- --outDir ../../.scratch/sites/<reference> --emptyOutDir``, then `deploy_site` with ``.scratch/sites/<reference>``. A site of plain hand written HTML, CSS and JS with no build step deploys its folder as it is.
- The deployment comes back on success with its URL. The production site is the asset's ``url``, also served at each of its ``data.domains``. A deployment serves the moment it lands and has no address of its own.
- A site with no ``404.html`` at its root serves ``index.html`` for any path no file matches, so client side routing works as it is. Ship a ``404.html`` at the root for a real not found page instead. ``_headers`` and ``_redirects`` at the root apply as they always have.
- Every app ships a favicon: the platform wears it as the app's icon on its resource card, and an app without one shows a generic globe. Write a ``favicon.svg`` into the output directory holding one emoji that suits the app, ``<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🚀</text></svg>``, and declare it in the ``index.html`` head with ``<link rel="icon" type="image/svg+xml" href="/favicon.svg">``.
- The platform previews the production site inside an iframe on its resource card. Never ship an ``X-Frame-Options`` header (a ``_headers`` file with ``DENY`` or ``SAMEORIGIN`` blanks that preview). When the app needs clickjacking protection, set ``Content-Security-Policy: frame-ancestors 'self' https://app.vibetasking.com`` instead. A deploy whose headers block that preview answers with a ``frame_warning``. When it appears, fix the headers and redeploy before reporting success.
- Share the production URL with the user when the deploy succeeds, and check the deployed site with the browser when the change matters.

## Showing work in progress

From a run, to let the user try what you are building before it is deployed, run its dev server as a preview with ``share_preview`` and give them the link it returns. Someone outside the app, such as a client, needs a link of their own from ``share_link``, which opens with no account for a day. The platform keeps the preview running while the sandbox lives, wakes it when someone opens the link, and lets it sleep when nobody uses it. A preview is not hosting: deploy to the SITE asset for anything meant to last.

- The command installs as well as starts, so it still works after a rebuilt sandbox, and runs from the site's folder: ``cd sites/<reference> && npm ci && npm run dev -- --host 0.0.0.0 --port 5173``.
- The preview is served on its own host, which the command's environment carries as ``PREVIEW_HOST``. Vite rejects hosts it does not know, so allow it in ``vite.config``: ``server: { host: true, allowedHosts: [process.env.PREVIEW_HOST] }``. Next.js refuses its dev endpoints, hot reload included, to another origin, so add it to ``next.config``: ``allowedDevOrigins: [process.env.PREVIEW_HOST]``.
- A server that fails to start comes back as an error with the end of its output, and its whole output is in ``/tmp/.previews/``.

## Design

From a run, before you build a new site or redesign one, read ``system/skills/vibetasking/rules/frontend-design.md``: decide palette, type and layout for this subject before writing code, and check the plan against the generic looks it lists. A small edit keeps the design the site already has. Two readings of that guide here:

- Where it says to confirm the subject with the client, ask only when a person is behind the conversation. With nobody behind it, choose the subject, audience and job from the brief and say what you chose in your reply.
- Its critique pass runs on the preview: open the ``share_preview`` link with the browser, take a full page ``capture_screenshot``, and fix what you see before deploying.

## Editing an existing site

Edit the source in ``sites/<reference>/``, rebuild, and deploy. `deploy_site` names the revision of the folder the build came from, and a deploy is refused when the site serves a deployment built from a later revision than your copy holds: another conversation changed the source and deployed while you worked. When that happens, bring the folder up to date with ``refresh_files`` on ``sites/<reference>/``, check your changes still stand, rebuild and deploy again.

Every deploy also retains the exact bundle it published. `get_site_bundle_url` with the asset's id and a deployment's id (the ``canonical_deployment`` `list_site_deployments` answers, or another one from the same listing) returns a short lived download URL for that deployment's zip, which holds everything the deploy shipped, ``functions/`` and ``_worker.js`` included. Reach for it when the folder is empty but the site already serves something: unzip the served bundle into ``sites/<reference>/`` and work from there. It is what the site serves, built output when the site was built, so it is a starting point rather than the original source. A deployment made before retention existed has no bundle and answers 404: rebuild once from whatever sources remain.

A served deployment that names no revision was made outside the folder, such as an upload, and guards by its bundle instead: a deploy is refused until this conversation fetched that bundle. Fetch it, carry what differs into the source, and deploy.

## Custom domains

The production site always serves at its platform addresses. To also serve it from a domain the user owns, attach the hostname with `add_site_domain` (the asset's id plus the domain, such as ``www.example.com``), then have the user publish a CNAME record at that hostname pointing to the ``cname_target`` in the response. Cloudflare validates the record and issues the certificate on its own, and `list_site_domains` shows the progress: the domain serves once its ``status`` is ``active``. An apex domain (``example.com``) works only when the user's DNS provider supports a CNAME at the apex (ALIAS, ANAME or flattening), otherwise attach a subdomain like ``www``. `remove_site_domain` detaches it. An app that signs people in adds the new address to its database's redirect list (**Signing people in**).

## Server code

Browser bundles are public, so anything secret or privileged lives in server code, which deploys with the same bundle:

- A ``functions/`` directory next to the static output maps files to routes: ``functions/api/tasks.js`` serves ``/api/tasks``. Export ``onRequest(context)`` (or ``onRequestGet``, ``onRequestPost`` and the rest) and return a ``Response``.
- A ``_worker.js`` at the root runs instead of ``functions/``, as a Worker module that reaches the static files through ``env.ASSETS``.
- Server code reads secrets from ``context.env.NAME``. A secret is live the moment it is set, and every deploy keeps the site's secrets.

`list_site_secrets` lists a site's secret names, `set_site_secrets` sets them and `delete_site_secret` removes one. Set a secret yourself only with a value you hold, such as a key you made with `create_key` (**Calling the VibeTasking API from the app**).

A value from the user's own accounts (a Stripe key, a Microsoft client secret, a password) is never asked for in the conversation, where it stays in the transcript. Tell the user the secret's name and ask them to set it in the app: the site shows under Resources as a VibeApp, and its **VibeApp secrets** panel (**Secretos de la VibeApp** in Spanish), opened from its toolbar, takes a name and a value. It is not the workspace's Secrets, where the Vault's items live. Then check with `list_site_secrets` that the name is there before anything relies on it. Never set one from a Vault reference (``$NAME``): a closed field reaches the site as its stand-in, which is worthless there, so the user sets that value in the panel too. A site that moved from the old hosting may answer a deploy with 409 naming secrets that did not move: each is set again the same way, then you deploy.

## Signing people in

An app whose pages are not for everyone signs people in through its SUPABASE asset's auth. Each setting below is the project's auth configuration, read with `read_asset_api` and changed with `call_asset_api` (``method`` ``PATCH``) on ``v1/projects/{project_ref}/config/auth``, a change of only the fields you send.

1. **A sender.** The database sends its sign in emails (codes, links, invitations, password resets) only once it has a sender, and until then none is delivered. `set_database_mailer` with ``email_asset_id`` sends them from one of the workspace's mailboxes, made with `create_asset` (``type`` ``EMAIL``, free) when none fits, ``sender_name`` the app's name and ``emails_per_hour`` (30 when left out) shared by everyone signing in: raise it for an app a whole team opens at once. Later the name (``smtp_sender_name``) and the limit (``rate_limit_email_sent``) change in the auth settings like any other. When the user wants the emails sent from a server of their own, they set it in the app, in the database's **Emails** section, so its password never passes through the conversation. `get_asset` shows where they go out from as ``mailer`` in the database's ``details``.
2. **Its addresses.** ``site_url`` is the app's ``url``, and ``uri_allow_list`` holds every address the app answers at, each as ``https://<host>/**``: its ``data.domains`` and every custom domain. Read the list first and add to it, since the other apps on the same database keep theirs there.
3. **How people sign in.** By default an emailed code: ``signInWithOtp({ email })``, then ``verifyOtp({ email, token, type: "email" })``. A code works on any device and survives the link scanners some mail servers run. Write the magic link template (``mailer_subjects_magic_link`` and ``mailer_templates_magic_link_content``) in the user's language, showing ``{{ .Token }}``, and set ``mailer_otp_length`` to 6. An organization on Microsoft 365 or Google Workspace signs in with its own accounts instead, ``signInWithOAuth`` with the provider: ``external_azure_enabled`` with its app registration (``external_azure_client_id``, ``external_azure_url`` naming its tenant), or the Google fields. The registration's secret is the user's, so they enter it in the app, in the database's **Auth** settings, under the provider.
4. **Who gets in.** For an app only some people may open, keep a table of them (their ``email`` and ``role``) and refuse everyone else when their account would be created, with a Postgres function as the ``before-user-created`` hook: it takes the event (``event->'user'->>'email'``) and returns ``{}`` to allow or ``{"error": {"http_code": 403, "message": "..."}}`` to refuse, is executable by ``supabase_auth_admin`` and by nobody else, and is set with ``hook_before_user_created_enabled`` true and ``hook_before_user_created_uri`` as ``pg-functions://postgres/<schema>/<function>``. The app's admins add people to that table through the app, under its policies, so inviting someone needs no server key.
5. **What each person reads.** Every table the app touches has row level security, its policies on ``(select auth.uid())`` (wrapped so it runs once per query) and the people table for roles. The browser holds the session through ``@supabase/supabase-js``, and server code that acts for a person passes their access token on (``Authorization: Bearer <token>`` with the anon key) so the same policies hold there.

The project's other auth settings (sessions, rate limits, captcha) are in the same configuration, and the user sees them in the app under the database's **Auth** settings, the sender and every email's subject and body together in its **Emails** section, where each email also offers a recommended text in the user's language.

## Data

From a run, ``$SUPABASE_DB_URL`` is the database (``psql "$SUPABASE_DB_URL"``, see the `supabase` skill). Create the app's tables there, in ``public`` (the schema the project's API serves), their names starting with the app's when the database serves several apps, and write a policy for every table the browser touches: row level security is the app's security boundary. Read the ``security-`` and ``schema-`` rules the `supabase` skill points at before the first table and policy: a policy that calls ``auth.uid()`` on every row, or filters on a column with no index, is what slows a page down once a table grows.

The browser uses ``@supabase/supabase-js`` with the project URL and its anon key, both safe to ship. `list_assets` with ``type`` ``SUPABASE`` and ``active`` true reads them: the project URL is ``https://<reference>.supabase.co`` and the anon key is ``details.supabase.anon_key``. Ship nothing else: no secret key, no connection string, no platform credential of any kind.

**A read through the project's API stops at 1000 rows.** That is the PostgREST ``max_rows`` every provisioned project runs with, and nothing in the response says the result was cut, so a table holding 4000 rows renders as 1000 and every total the page adds up from it is wrong. Ask the database for numbers instead of counting rows in the browser: ``select("*", { count: "exact", head: true })`` for a count, and a Postgres view or a function for sums, averages and group bys, so the page fetches one row instead of thousands. When the app has to list everything, page with ``.range(from, to)`` in slices of 1000 until a page comes back short. Your own ``psql`` reads go straight to Postgres and never truncate, so the gap only shows up in the deployed app: check the numbers there, not in SQL.

## Files

The app's files (uploads, documents, videos) live in its database's storage: a private bucket per app (``insert into storage.buckets (id, name, public) values ('<app>', '<app>', false)``), policies on ``storage.objects`` by ``bucket_id`` and the person's role, uploads from the browser with ``supabase.storage.from(bucket).upload``, and reads through ``createSignedUrl``. A file over 50 MB needs the project's limit raised first: ``fileSizeLimit`` in bytes, with `call_asset_api` (``method`` ``PATCH``) on ``v1/projects/{project_ref}/config/storage``. A SITE asset's files are the app's own build, 25 MiB each at most, never a store for anything else.

## Calling the VibeTasking API from the app

For app features that start runs or message agents, the app's server code calls the VibeTasking API's ``/v1`` operations (``https://api.vibetasking.com/v1``, reference at ``/docs``, spec at ``/openapi.json``) with an API key. Mint one yourself:

1. `create_key` with the ``workspace_id`` from `get_me`, a ``name`` that says what it is for, and explicit ``scopes``, the narrowest set covering what the app calls (``resource:action`` strings like ``runs:read`` or ``runs:create``, since an unscoped key is refused). Omit ``expires_at`` so the key outlives the run. It still lives with the conversation that made it: canceling or deleting that conversation revokes it, so tell the user. The response carries ``token`` exactly once, and it can never be read again.
2. Put the token on the site as a secret at once, and nowhere else: `set_site_secrets` with ``{"VIBETASKING_API_KEY": "<the token>"}``. If the token is lost, mint a new key, set it the same way and delete the old one (`list_keys`, `delete_key`).
3. Call the API only from server code, passing the key as the ``api-key`` header from ``context.env``. Never embed it in client JavaScript and never expose it through a response.

```js
export async function onRequestPost(context) {
  const response = await fetch("https://api.vibetasking.com/v1/runs", {
    method: "POST",
    headers: { "api-key": context.env.VIBETASKING_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify(await context.request.json()),
  });
  return new Response(await response.text(), { status: response.status });
}
```

Validate and constrain what the server code forwards: it runs with the key's full authority, so a passthrough proxy hands that authority to every visitor.

## Selling on the site

When the user wants the site to charge their customers, pair it with the workspace's STRIPE asset. The site never holds a Stripe credential: payments flow through payment links or the VibeTasking API.

- Check ``stripe account_status`` first: until ``charges_enabled`` is true the account can sell nothing, so ask the user, in a message, to finish setup from the resource card.
- **Fixed prices** need no backend at all: create the product and price, mint a payment link (``stripe create_payment_link``), and put its URL on a buy button. Links keep working across deploys until deactivated.
- **Customer specific checkout** (a known email, a return page on the site) goes through server code calling the platform's headless toolkit endpoint with the STRIPE asset's id and the key from the previous section:

```js
export async function onRequestPost(context) {
  const response = await fetch("https://api.vibetasking.com/v1/toolkits/STRIPE/tools/stripe_create_checkout_session/call", {
    method: "POST",
    headers: { "api-key": context.env.VIBETASKING_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_id: context.env.STRIPE_ASSET_ID,
      args: {
        price_id: "price_...",  // pin server-side, never from the request body
        success_url: `${new URL(context.request.url).origin}/thanks?session={CHECKOUT_SESSION_ID}`,
        cancel_url: `${new URL(context.request.url).origin}/`,
      },
    }),
  });
  const outcome = await response.json();
  return Response.json({ url: outcome.result?.url });
}
```

- Pin the ``price_id`` (and any argument that shapes an amount) in server code. Server code that forwards tool names or arguments a visitor chose hands the key's authority to every visitor: expose exactly the calls the page needs, session creation and ``stripe_get_payment`` status reads.
- Before fulfilling anything, check the payment in server code: ``stripe_get_payment`` with the returned session id must report ``payment_status: "paid"``. The success page loading proves nothing.
- The platform's application fee is applied to every link and session on its own, so never add fee arguments of your own.