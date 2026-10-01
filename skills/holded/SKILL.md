---
name: holded
description: Holded ERP document and contact operations via the `holded` CLI, and
  app.holded.com browser operation for what the API doesn't cover.
---

# Holded (HoldedOpenApiToolkit)

Holded is an ERP/invoicing platform. API domains: invoicing (contacts, invoices, estimates, credit notes, products, services), accounting, CRM (leads, funnels), projects, and team management.

The action names below are the v2 API's, loaded by a key starting `pat_`. A legacy key loads the v1 API, whose actions are named and paged differently: run `holded --help` for the names this run has.

## Commands

```bash
holded --help                         # list all actions
holded list_contacts --help           # show parameters for an action
holded list_contacts --json '{"limit": 100}'
holded create_an_invoice --json '{"contact_id": "abc123", "items": [...]}'
```

## Notes

- **Discover before calling.** Documents are typed, with separate actions per kind (invoices, estimates, credit notes, purchases). Run `holded --help` to find the right action and `holded <action> --help` for its parameters.
- **Pagination.** List actions are cursor-based. Pass `limit`, then repeat with the `cursor` from the previous page until none comes back.
- **Dates.** Use full ISO 8601 with the user's timezone offset, e.g. "2026-03-15T00:00:00+01:00".
- **Document downloads.** Actions like `holded get_invoice_pdf` save the file to the sandbox and return `{"file_path": "...", "size_bytes": ...}`.
- **Write ordering.** POST/PUT/PATCH/DELETE operations run sequentially to preserve consistency.
- **Ids are internal ids.** Every `*_id` parameter (and the line `account`) takes Holded's own internal id from a prior read or create response, never a human code or a placeholder. Capture the `id` a create action returns and pass it to follow-up calls. Values like `LAST_INSERT_ID` or an accounting code such as `62900003` raise `Error parsing ObjectId`.

## Document line items (invoices, estimates, …)

- **Taxes are keys, not percentages.** A line's `taxes` takes Holded tax keys like `["s_iva_21"]`, not the number `21`. Read the available keys with `holded list_all_taxes`, or copy them from the linked product or service. When `taxes` is omitted the line inherits the contact's default sales tax, and a contact with no default produces a line with no tax, so the totals come out without VAT.
- **`account` is an internal id, not the chart code.** A line's `account` takes Holded's internal account id, not the accounting code such as `70500001`. Resolve the code to its id with `holded list_chart_of_accounts`, or set the default account on the product or service so the line inherits it.
- **Updating a document replaces it.** `holded update_a_purchase`, `holded update_an_invoice` and the other document updates are full replacements: every field left out of the call goes back to its default. Read the document first, change what you need, and send the whole thing back including `items`.
- **On a foreign-currency document, check the total after each write.** Holded renders amounts already rounded to two decimals and rounds again when it converts to the account currency, so sending a price straight back can move the total by a cent. Read the document again after writing, compare the total against what it was, and stop at the first difference rather than continuing through the rest.
- **New documents are drafts.** A created estimate or invoice is saved once the action returns an `id`, but it stays a draft until finalized. Finalize only when explicitly asked, with the document's own action such as `holded accept_an_estimate` or `holded approve_an_invoice`.

## API key permissions

A `403` means the connected API key lacks permission for that operation. Holded words it two ways: `Insufficient permissions: <scope> required` (naming a scope like `accounting:taxes.read`, `accounting:chart-of-accounts.read`, or `inventory:products.read`) or a bare `Access denied.` (common on reads such as contacts, products, and invoices). Either way, retrying the same call will not help. Tell the user to enable the missing permission on the Holded API key and stop.


# Holded in the browser (app.holded.com)

For what the API doesn't cover, operate app.holded.com logged in; most of its data
is served by internal APIs that scripts can call directly with the page's
authenticated session, so once you're logged in you rarely need to click through
the UI. If a request bounces to a login page, the session has expired — log in
again. Purchase documents live under **Compras → Escáner** (the inbox/scanner).

## Bulk-download inbox documents

`download_inbox_invoices.js` lists every document in the purchase inbox within a
date range and downloads them all, plus a `download_summary_<timestamp>.txt`
listing what succeeded and what failed.
```
js(path="system/skills/holded/download_inbox_invoices.js", args={"startDate": "02/02/2026", "endDate": "08/02/2026"})
```
- `startDate`, `endDate` (required): inclusive range, `dd/mm/yyyy` or `dd-mm-yyyy`.

It returns a JSON object — check `downloadedCount`, `attemptedCount`,
`failedCount`, and `failures[]` before reporting done. Files and the summary land
in the sandbox Downloads folder. Runs synchronously; slow with many documents.

A document counts as downloaded only when its bytes open as the file its name says
(PDF, PNG, JPEG, ZIP); an HTML or JSON answer lands in `failures[]` with the reason.
A file request that bounces to the login page stops the batch: `success` is false,
`sessionExpired` is true, and `attemptedCount` is below `listedCount`. Log in again
and rerun for the dates still missing.

---

Companion files, each in this skill's folder beside this file:
- download_inbox_invoices.js

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
