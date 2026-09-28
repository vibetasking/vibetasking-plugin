---
name: whatsapp
description: Complete --json argument shapes for every WhatsApp Business Cloud API
  send (text, template, media, interactive), the 24-hour window rules, and WhatsApp
  Web browser tactics
---

# WhatsApp (WhatsappToolkit)

The CLI name is `whatsapp` (no trailing dash, see `system/toolkits.json`).
The commands below carry each action's complete argument shape: call them
as written, no `--help` round trip needed. Reserve `--help` for the
management actions documented by name only.

## Commands

### Send a free-form text message

```bash
whatsapp send_message --json '{"text": "Your order has shipped!"}'
```

Only delivers inside the 24-hour customer service window (since the
contact's last inbound message). Omit `to` — sends default to the run's
bound contact (see Notes for when an explicit recipient is allowed).

### Send an approved template message (works outside the 24h window)

```bash
whatsapp list_templates
whatsapp send_template_message --json '{"name": "order_confirmed", "language": "en_US", "body_variables": ["Alice", "#1234"]}'
```

`list_templates` returns each approved template's `variables.body` /
`header` / `buttons` counts — pass exactly that many strings, in order, as
`body_variables` / `header_variables` / `button_url_variables`.

### Send media

```bash
whatsapp send_media --json '{"media_type": "image", "file_path": "chart.png", "caption": "Q3 results"}'
```

Provide exactly one source: `link` (public URL, Meta fetches it),
`media_id` (from a prior `upload_media`), or `file_path` (sandbox-relative,
uploaded for you). `media_type` is one of `image`, `video`, `audio`,
`document`, `sticker`. Only delivers inside the 24-hour window.

```bash
whatsapp upload_media --json '{"file_path": "brochure.pdf"}'
```

The returned `media_id` is valid 30 days — reuse it across sends instead
of re-uploading the same asset.

### Location, contact cards, interactive messages

```bash
whatsapp send_location --json '{"latitude": 41.3874, "longitude": 2.1686, "name": "Office"}'
whatsapp send_contacts --json '{"contacts": [{"name": {"formatted_name": "Alice Smith"}, "phones": [{"phone": "+34600123456"}]}]}'
whatsapp send_interactive_buttons --json '{"body_text": "Confirm your appointment?", "buttons": [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]}'
whatsapp send_interactive_list --json '{"body_text": "Pick a slot", "button_label": "Choose", "rows": [{"id": "am", "title": "Morning"}, {"id": "pm", "title": "Afternoon"}]}'
```

`send_interactive_buttons` takes up to 3 buttons; `send_interactive_list`
takes up to 10 rows. Both are free-form sends, so the 24-hour window rule
applies. The tapped button/row `id` comes back as the contact's next
inbound message.

### Management

```bash
whatsapp get_business_profile
whatsapp get_phone_number
whatsapp list_phone_numbers
whatsapp get_template_status --json '{"name": "order_confirmed"}'
```

`create_template` / `delete_template` submit or remove templates for Meta
approval — see `whatsapp create_template --help` for the component shape.

## Notes

- Omit `to`: every send defaults to the run's bound contact (the person
  this conversation is with). On contact-bound runs, an explicit `to`
  addressing anyone else is rejected unless external recipients are
  enabled in the channel's settings — don't assume it's allowed. Runs
  with no bound contact must pass `to` explicitly, in E.164 format
  (e.g. `+34600123456`).
- Meta's 24-hour customer service window gates free-form sends
  (`send_message`, `send_media`, `send_location`, `send_contacts`,
  interactive buttons/lists). Outside it, use `send_template_message`
  to re-open the conversation.

## WhatsApp Web through the browser

For tasks that operate `web.whatsapp.com` with the browser toolkit rather
than this CLI:

- Open a chat with the deep link `https://web.whatsapp.com/send?phone=<number>`
  (E.164 digits without the `+`). The deep link checks the number against
  WhatsApp's global directory. The in-page search box only searches chats
  and contacts the account already knows, so an empty search result is not
  evidence the number lacks WhatsApp. Mark a number as not on WhatsApp only
  when the deep link makes WhatsApp show its own invalid-number notice.
- The chat re-renders after text entry, detaching elements snapshotted
  earlier, and a click on a stale element index fails with "Element ... is
  gone or detached". Re-snapshot right before clicking Send, or click by
  coordinates.
- A chat can hold an unsent draft from an earlier attempt. Clear the
  compose box before typing so the leftover text does not ride along or
  duplicate the send.
