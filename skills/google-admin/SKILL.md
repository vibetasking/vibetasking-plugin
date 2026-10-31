---
name: google-admin
description: Google Workspace administration through the composio CLI. Which actions
  are Composio's and which run on Google's API directly, my_customer for the account's
  own id, the audit and login activity of every application, users' OAuth tokens and
  sign outs, updating a user with a body, organizational units and devices, and what
  a refusal for missing privileges means
---

# Google Admin (GoogleAdminComposioToolkit)

The CLI name is `composio google_admin`. Every action works on the Google
Workspace account of the administrator who connected the integration.

## Two families of actions

- Composio's own actions are named verb first: `list_users`, `get_user`,
  `create_user`, `delete_user`, `suspend_user`, `add_user_alias`,
  `remove_user_alias`, `list_groups`, `get_group`, `create_group`,
  `update_group_settings`, `list_group_members`, `add_user_to_group` and
  `remove_user_from_group`.
- Every other Admin SDK method is named resource first, as Google names it:
  `users_patch`, `users_sign_out`, `tokens_list`, `orgunits_list`,
  `activities_list`, `mobiledevices_action` and the rest. `composio google_admin --search <words>` finds one, and
  `composio google_admin <action> --help` shows its arguments.

A resource first action takes the method's path and query parameters in
snake_case and, when the method changes a resource, a `body` holding that
resource's fields, also in snake_case. Its answer is Google's own JSON, in
Google's camelCase names.

## The account's own id

An argument named `customer_id` or `customer` takes `my_customer` for the
connected account.

```bash
composio google_admin orgunits_list --json '{"customer_id": "my_customer", "type": "all"}'
```

## Who did what: the activity reports

`activities_list` returns the audit events of one application. `user_key` is
a user's email or `all`, and `application_name` picks the application:
`login` for sign ins, `admin` for changes made in the Admin console, `token`
for third party app grants, `drive`, `gmail`, `groups`, `mobile`, `saml` and
the rest its `--help` lists.

```bash
jq -n '{user_key: "all", application_name: "login", event_name: "login_failure", start_time: "2026-10-01T00:00:00Z", max_results: 1000}' > failures.json
composio google_admin activities_list --json-file failures.json
```

- `start_time` and `end_time` are RFC 3339 times. `max_results` defaults to
  1000, and the answer's `nextPageToken` goes back as `page_token` for the
  next page.
- `filters` narrows by an event's own parameters, `actor_ip_address` by the
  address the event came from.
- `user_usage_report_get` and `customer_usage_reports_get` answer the usage of
  one `date` (`yyyy-mm-dd`, Pacific time).

## Security alerts

The Alert Center's alerts are out of reach of this integration: Google opens
that API only to a service account with domain-wide delegation. Suspicious
sign ins are in the `login` activity, as the events `suspicious_login`,
`suspicious_login_less_secure_app` and `suspicious_programmatic_login`.

## A user's access

- `tokens_list` (`user_key`) lists the third party apps a user granted access
  to, and `tokens_delete` (`user_key`, `client_id`) revokes one.
- `users_sign_out` ends every session of a user, on every device.
- `asps_list`, `verification_codes_list` and `verification_codes_generate`
  cover app passwords and backup codes. `two_step_verification_turn_off`
  turns 2-step verification off for a user.

## Updating a user

`users_patch` changes only the fields its `body` names:

```bash
jq -n '{user_key: "ana@acme.com", body: {org_unit_path: "/Sales/EU", name: {given_name: "Ana"}}}' > patch.json
composio google_admin users_patch --json-file patch.json
```

## Devices

`mobiledevices_list` and `chromeosdevices_list` take `customer_id`
`my_customer`. `mobiledevices_action` takes the device's `resource_id` and a
`body` with its `action`: `approve`, `block`, `admin_account_wipe`,
`admin_remote_wipe`, `cancel_remote_wipe_then_activate` or
`cancel_remote_wipe_then_block`. Read the device first and confirm with the
person before a wipe.

## A refusal

An answer of 403 with "Not Authorized to access this resource/api" means the
administrator who connected the integration lacks the privilege for that area,
or that the account's Admin console does not trust this app. Tell the person
which action was refused.
