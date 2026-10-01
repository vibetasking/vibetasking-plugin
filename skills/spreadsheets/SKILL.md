---
name: spreadsheets
description: Excel/Google Sheets best practices, data verification, batch workflows
---

# Spreadsheets (ExcelOfficeToolkit, GoogleSheetsComposioToolkit)

## Commands

### Excel

```bash
excel --help                                # list all actions
excel create_excel_workbook --help          # show parameters for an action
excel create_excel_workbook --json '{"filepath": "report.xlsx"}'
excel write_data_to_excel --json '{"filepath": "report.xlsx", "sheet_name": "Sheet1", "data": [...], "start_cell": "A1"}'
```

- `excel create_excel_workbook` also creates Sheet1. Never call `excel create_excel_worksheet` unless you need an additional one.
- Always set `include_ranges=True` when calling `excel get_workbook_metadata`.
- Always provide `start_cell` when calling `excel write_data_to_excel`.
- Always call `excel validate_all_formulas` after writing data. It checks formula syntax and references only — it does not compute values or catch runtime errors like `#DIV/0!`. See "Formula recalculation" below.
- `excel read_data_from_excel` returns formula cells as formula strings, not computed values.
- `excel` writes save in place on the target file, and every call loads and re-saves the whole workbook. Copy the user's original before editing it unless the task explicitly asks for an in-place edit, and batch bulk changes into one Python script rather than many CLI calls on a large file.
- Use English function names, commas as separators, periods for decimals, regardless of language.
- Prefer formulas that also work in Google Sheets. Keep formulas simple.

### Google Sheets

```bash
composio googlesheets get_sheet_names --json '{"spreadsheet_id": "abc123"}'
composio googlesheets values_get --json '{"spreadsheet_id": "abc123", "range": "Sales!A1:D10"}'
composio googlesheets values_update --json '{"spreadsheet_id": "abc123", "range": "Sales!A2:D2", "values": [["Alice", 3, true, "a@y.com"]], "value_input_option": "RAW"}'
composio googlesheets spreadsheets_values_append --json '{"spreadsheet_id": "abc123", "range": "Sales", "values": [["Bob", 5, false, "b@y.com"]], "value_input_option": "RAW"}'
```

These shapes are complete: call them as written. For any other action,
`composio googlesheets <action> --help` shows its parameters.

- Creating a spreadsheet is `create_google_sheet1` with `title`, not `create_spreadsheet` with `spreadsheet_name` (that action doesn't exist).
- `spreadsheets_values_append` appends after the last row of the table it detects in `range`. Give it a sheet-qualified range or the exact sheet name alone, never a bare `A:F`, and read `updates.updatedRange` in the response to see where the rows actually landed. For strict placement use `values_update`.
- `update_values_batch` writes several ranges in one call: `data` is an array of `{"range": ..., "values": [[...]]}` objects, plus top-level `spreadsheet_id` and `value_input_option`.
- `googlesheets_values_get` returns a dict keyed by A1 notation (e.g., `{"A32": "Hello World"}`). Does NOT return empty cells. Don't assume fewer rows/columns than actually exist.
- Writing a range is `values_update`, not `update_spreadsheet_values`. `googlesheets_values_update` takes a 2D array (matrix). First element maps to the first cell in the range. Watch for off-by-one errors.
- Always pass `value_input_option: RAW` on `spreadsheets_values_append` and `values_update`, unless a formula genuinely needs USER_ENTERED evaluation. USER_ENTERED tells Sheets to reparse the string as if a human typed it, which silently strips a leading `+` from phone numbers and rewrites date-shaped text into a raw date serial number. Treat any phone-like or date-like text field as RAW-only.
- Never assume the first sheet is "Sheet1". Always retrieve actual sheet names first.
- Avoid `googlesheets_get_spreadsheet_info` with `include_grid_data=true` on large spreadsheets (HTTP 413).

## Python scripts (openpyxl, pandas)

For bulk work on `.xlsx` files, a Python script in your shell beats many CLI calls. Known traps:

- With `load_workbook(..., read_only=True)`, never call `ws.cell(row, col)` in a loop. Each call re-parses the sheet from the top, so a full scan turns quadratic — minutes on a few thousand rows. Stream with `ws.iter_rows(values_only=True)` instead; the same scan takes seconds.
- When a script times out, the script is usually the problem. Find and fix the slow part before rerunning with a longer `timeout`.
- Never save a workbook loaded with `data_only=True`. Saving replaces every formula with its cached value, permanently. Load with `data_only=True` only to read.
- A pandas round-trip (`read_excel` → `to_excel`) silently drops formulas, formatting, merged cells, and all other sheets. Use pandas when the deliverable is plain data. Edit existing workbooks with openpyxl.
- Write results to a new file and keep the user's original intact, unless the task explicitly says to modify it in place.

## Formula recalculation

Neither `excel` actions nor openpyxl compute formula values. They store formula strings, so many viewers show 0 or blank, and reads return the formula text. After writing formulas, recalculate headlessly and deliver the recalculated copy:

```bash
libreoffice --headless --convert-to xlsx --outdir recalculated file.xlsx
```

- Verify computed values by reading the recalculated copy with openpyxl `data_only=True`. Remember `excel read_data_from_excel` returns formula strings, so it cannot do this.
- Scan the recalculated values for `#DIV/0!`, `#REF!`, `#VALUE!`, `#N/A`, and `#NAME?`. Deliver with zero formula errors.

## Messy data

Real-world data is messy. It's often ill-structured, with errors, or just plain wrong.

- Common issues include shifted dates, slightly mistyped identifiers, and flipped signs in numeric values.
- Watch out for suspicious high-level patterns that conflict with the user's task or perceived expectations.
- When you detect an issue, first try to work around it or correct it yourself. If that's not possible, clearly explain the problem to the user.

## Layout, formatting, and comparisons

When the user has not specified formatting rules, proactively make outputs easy to understand and review.

- In sheets where the columns have not been specified by the user, include extra columns with formulas to help validate the data.
- Use formatting to tell things apart, in tools that support it.

When comparing documents or sheets, be especially mindful of messy data.

- It's likely an item in one document maps to multiple items in the other.

When each row needs its own written reasoning or justification, write those texts yourself with your file writing tool, `excel_write_data_to_excel` or `googlesheets_values_update`. Text a script assembles from formulas or templates repeats itself and misses what is particular to each row. Use the shell for the number crunching, and write long runs of text in batches.

## Data verification

- It's easy to make mistakes when writing data. Before doing so, make sure you're certain about what data you're writing, and where.
- After every write, read the range back and check it against its row and column context, since a value in the wrong cell reads as correct in isolation. Confirm you wrote to the intended cell ranges.
- When the read shows a mistake, roll back what was written by accident, then apply what is missing.
- When a mistake cannot be repaired, stop and tell the user what happened.
