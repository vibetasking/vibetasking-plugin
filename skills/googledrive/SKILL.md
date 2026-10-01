---
name: googledrive
description: Working composio googledrive action names and shapes, the four upload
  actions, upload verification, metadata field selection, and sharing permissions
---

# Google Drive (GoogleDriveComposioToolkit)

The CLI name is `composio googledrive`. The shapes below cover the actions
most tasks need: call them as written. Use `composio googledrive <action>
--help` only for actions this file leaves undocumented.

## Known action names

Composio's action names often don't match Google's own API. Use the name on
the right, not the guess on the left:

- Finding a folder is `find_folder`, not `search_file`, and it filters by
  `name_exact`/`name_contains`, not `name`.
- Finding or listing files by query is `find_file`, not `list_files` (that
  action doesn't exist).
- `create_folder` takes `folder_name` and `parent_id`, not `parent_folder_id`.
- Moving a file is `move_file` (`file_id` plus `add_parents`/`remove_parents`).
- Sharing a file or granting access is `create_permission`.

## Uploads

Uploading a file takes `file_to_upload` and `folder_to_upload_to`, not
`file_path`/`parent_id`. There are four upload actions. Pick by size and
intent, don't just try `upload_file` and fall back by trial and error:

- `upload_file --json '{"file_to_upload": "<path>", "folder_to_upload_to": "<id>"}'`: new file,
  **5MB max**. An invalid or missing folder id silently lands the file in
  Drive root with exit 0, so resolve the folder id first (`find_folder`).
- `resumable_upload`: new file over 5MB (`chunk_size` must be a multiple of
  256KB).
- `upload_update_file --json '{"file_id": "<id>", "file_to_upload": "<path>"}'`: replace an
  existing file's content.
- `upload_from_url --json '{"name": "<name>", "source_url": "<url>"}'`: persist an
  externally-hosted file server-side. `source_url` must be a direct,
  publicly-fetchable file URL. A landing or share page (e.g. a WeTransfer
  share link, not the raw asset URL behind it) downloads as HTML, not the
  file, and the action still exits 0.

After uploading a large or externally-sourced file, call `get_file_metadata`
and confirm the returned `size` roughly matches the source file's size before
treating the upload as done. A mismatch means you uploaded the wrong content
(e.g. a redirect or landing page). Don't proceed as if it succeeded.

## Metadata and sharing

- `get_file_metadata --json '{"file_id": "<id>"}'` omits most fields by default (`size`,
  `webViewLink`, `parents`, `owners`, `modifiedTime` among them). Add
  `"fields": "id,name,mimeType,size,webViewLink"`, or `"*"` for everything,
  whenever you need more than the basics, including the upload size check
  above. `file_id` is the opaque Drive id, never a file name: resolve names
  with `find_file` first.
- Sharing is `create_permission --json '{"file_id": "<id>", "role": "reader", "type": "anyone"}'`
  for a public link, or `"type": "user", "email_address": "<addr>"` for one person
  (`"type": "group"` works the same). Roles are `reader`, `commenter`,
  `writer`, `owner`. The shareable link itself comes from
  `get_file_metadata` with `"fields": "webViewLink"`.
