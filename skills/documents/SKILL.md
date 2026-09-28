---
name: documents
description: PDF generation and Word document styling
---

# Documents (PrettyDocsToolkit, WordOfficeToolkit)

## When to use this skill

- **PDFs** from HTML: reports, proposals, invoices, certificates,
  one-pagers, dashboards, articles. Use **flow layout** when content
  length is unpredictable. Use **page layout** for designed-per-page
  documents. See `reference/html-pdf.md`.
- **Word `.docx`** documents: when the user explicitly asks for a
  Word file. Otherwise prefer PDF.
- For **slide decks** (PDF or PowerPoint), use the `presentations`
  skill instead.

Most requests are custom: design what fits the task. The renderer is
flexible. The only hard rules are tagged `[enforced]` in
`reference/html-pdf.md`.

## Workflow

```bash
# 1. Write the HTML to document.html with your file writing tool so you can iterate.

# 2. (page layout only) Catch overflow before rendering.
python system/skills/documents/scripts/validate_html.py document.html

# 3. Render. Auto-compresses; returns "<path> — N pages, X MB" plus any warnings.
pretty_docs html_to_pdf --json '{"html_file_name": "document.html", "output_file_name": "document.pdf"}'

# 4. Sample pages for visual review (first, middle, last by default).
python system/skills/documents/scripts/preview_pdf.py document.pdf

# 5. Look at the renders: open each .preview/document/page-NN.jpg with your file reading tool, as an image.
```

Iterate steps 1, 3, 4, 5 with your file editing tool until the rendered pages
look right. Pass `"landscape": true` to `html_to_pdf` for wide content
(dashboards, comparison tables, anything 16:9).

Margins: flow layout gets 25mm/20mm automatically (override with your
own `@page { margin: … }`). In page layout `.page` starts marginless —
pad it yourself (documents `25mm 20mm`, slides `12–18mm`) and keep
text ≥10mm off the paper edge unless intentionally full-bleed. In flow
documents, give any colored box that must not split across pages the
class `card` or `block`. The render result warns on violations
(`[edge-margins]`, `[torn-block]`, …) — fix them or ignore them
deliberately, then always preview before delivering.

For short, simple documents (1–2 pages) you can pass HTML inline:

```bash
pretty_docs html_to_pdf --json '{"html": "<html>...</html>", "output_file_name": "output.pdf"}'
```

## Word documents

```bash
word --help                           # list all actions
word add_heading --help               # show parameters for an action
word add_heading --json '{"filename": "doc.docx", "text": "My Title", "level": 1}'
```

You can only apply styles, not read them. Don't include styling in
text arguments. Use the `style` argument or `word format_text` for
existing paragraphs. The `color` argument is a hex code without the
"#" prefix.

## Style decisions are yours

Long documents, dense tables, image-heavy designs, minimalist
single-column reports, infographic posters: all valid. The
validator catches structural breaks (overflow, broken page balance,
unreadable fonts), not stylistic choices. Pick the layout, palette,
and density that fits the user's request and the implicit context.

Useful primitives for enrichment:

- `banana generate_image` for custom illustrations and backgrounds.
- `image_search image_search` for stock photos.
- Google Fonts via `<link>` in `<head>`, with a system fallback.

## Reference

For dimensions, margins, page-break semantics, image embedding, and
the full list of what's enforced versus suggested, read
`system/skills/documents/reference/html-pdf.md`. Both this skill and
the `presentations` skill use the same renderer. The reference is the
source of truth.

## External PDFs

To shrink a PDF that came from somewhere else (an upload, a Word
export, a previous run):

```bash
python system/skills/documents/scripts/optimize_pdf.py path/to.pdf
```

Same cascade as `html_to_pdf` uses: pymupdf clean, then ghostscript at
progressively more aggressive presets, capped at 20 MB.

---

Companion files, each in this skill's folder beside this file:
- reference/html-pdf.md
- scripts/_pdf_lib.py
- scripts/optimize_pdf.py
- scripts/preview_pdf.py
- scripts/validate_html.py

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
