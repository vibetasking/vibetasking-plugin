---
name: presentations
description: Slide deck creation (PDF & PowerPoint), editing, and QA
---

# Presentations

Slides are landscape A4 pages rendered via `pretty_docs html_to_pdf`,
optionally converted to PPTX afterward. The rendering model is shared
with the `documents` skill. Read
`system/skills/documents/reference/html-pdf.md` for the dimensions,
margins, page-fitting rules, and what is `[enforced]` by code.

Most decks are custom. There is no "default template": design what
fits the topic. The validator catches structural breaks (overflow,
unreadable fonts, broken images). Style is your call based on
explicit / implicit user task context. Long decks, dense slides,
text-only pages, repeated layouts, poster-style or infographic-style
designs are all legitimate.

## Workflow

```bash
# 1. Write the deck HTML to slides.html with your file writing tool so you can iterate.

# 2. Preview-validate overflow (landscape).
python system/skills/documents/scripts/validate_html.py slides.html --landscape

# 3. Render to PDF (auto-compressed, returns size + warnings).
pretty_docs html_to_pdf --json '{"html_file_name": "slides.html", "output_file_name": "slides.pdf", "landscape": true}'

# 4. Sample pages for visual review (scales with deck length).
python system/skills/documents/scripts/preview_pdf.py slides.pdf

# 5. Open the sampled images: open each .preview/slides/page-NN.jpg with your file reading tool, as an image.

# 6. (Optional) Convert to PowerPoint.
python system/skills/presentations/scripts/html_to_pptx.py slides.html slides.pptx
```

Iterate steps 1, 3, 4, 5 with your file editing tool until the sampled pages
look right. `preview_pdf.py` samples first/middle/last by default
and scales up for longer decks (3 samples for ≤15 slides, 5 for
≤40, 8 for 40+). Pass `--all` or `--pages 1,7,12` when you need
specific frames.

Each slide is a `.page` div sized exactly to the paper —
`width: 297mm; height: 210mm` for landscape. The renderer puts every
`.page` on its own sheet and rejects overflow, so design content to
fit. Split across slides rather than cramming. Pad each `.page`
(12–18mm typical) so text keeps ≥10mm off the slide edge — full-bleed
backgrounds and images are fine, text touching the paper edge is not.
The render result warns on size mismatches (`[page-size]`) and text
at or past the edge (`[edge-margins]`, `[clipped-text]`). Beyond
that, the layout, density, and style are yours.

For concrete layout patterns to start from (title slides, two-column,
image splits, stats grids, quotes, comparisons, timelines, dark
themes, gradients), see `system/skills/presentations/slides.md`. The
patterns are starting points: adapt, combine, replace as the task
demands.

## Enriching slides with images

```bash
# Custom illustration or background
banana generate_image --json '{"prompt": "Abstract dark blue gradient, subtle geometric patterns", "path": "bg.jpg", "aspect_ratio": "16:9", "resolution": "2K"}'

# Stock photos
image_search image_search --json '{"query": "modern office teamwork", "count": 5}'

# Download a found image locally
curl -L -o "photo.jpg" "https://example.com/image.jpg"
```

Embed in your HTML:

```html
<img src="photo.jpg" style="width: 100%; object-fit: cover;" />
<!-- or as a background -->
<div class="page" style="background-image: url('bg.jpg'); background-size: cover;">
```

Both local paths and remote URLs work. Download remote images
locally if you need reliability across re-renders.

## Animations

HTML slides are rendered as static snapshots: CSS animations and
transitions do not appear in the PDF or PPTX. For animated
presentations, use the **Remotion skill** instead (full motion
graphics, entrance effects, data visualizations as video).

## PPTX conversion

`html_to_pptx.py` screenshots each slide at 2x resolution and embeds
the images in a `.pptx`. Slides become pixel-perfect images, which
means: the PPTX is not editable as text. Always QA the PDF first.
If text editability matters, ship the PDF, or build the deck natively
with PptxGenJS instead of the HTML pipeline.

## Native and edited PowerPoint files

Building a deck natively with PptxGenJS, editing an existing deck or
filling a template follows the guide at
`system/skills/presentations/rules/pptx.md`: its pptxgenjs gotchas, the
unzip, edit and zip workflow, the slide scripts and the validator. Inside
a run:

- Its `scripts/` paths are relative to `system/skills/presentations/rules/`,
  so a call reads
  `python system/skills/presentations/rules/scripts/thumbnail.py deck.pptx deck-thumbs`.
- `pptxgenjs`, `react-icons`, `react`, `react-dom` and `sharp` are not
  preinstalled here, whatever the guide says. Install them in the project
  folder, next to the script that requires them (`npm install pptxgenjs`).
  The sandbox's system directories are read only, so a global install fails.

The guide lives only inside a run, so a reader outside one does not have it.

## Dependencies (sandbox-provided)

- `pretty_docs` toolkit (Chromium + Playwright)
- `pymupdf`, `pillow`: Python image / PDF handling
- `python-pptx`, Playwright: HTML→PPTX conversion
- LibreOffice (`soffice`): PPTX→PDF when needed
- Poppler (`pdftoppm`), `markitdown`: extraction and fallback rendering
- `defusedxml`, `lxml`: the slide scripts and the validator

## Reference

For page dimensions, the two layout modes, image embedding, typography
units, and the full list of what is enforced vs suggested:
`system/skills/documents/reference/html-pdf.md`.

---

Companion files, each in this skill's folder beside this file:
- scripts/html_to_pptx.py
- slides.md

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
