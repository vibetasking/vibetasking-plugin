# HTML → PDF reference

Shared reference for the `documents` and `presentations` skills. Covers
the rendering model, page sizing, the two layout modes, and the rules
that are code-enforced. Everything below applies to both PDFs and
slides — slides are just landscape A4 pages in page layout.

The renderer is Playwright (Chromium) printing to A4 paper. You design
in HTML and CSS; the toolkit injects a minimal print stylesheet (page
geometry, break hints, `box-sizing`, `print-color-adjust` — see
*Page-break hints* below) before your own CSS, so your CSS always wins.

## What is enforced [enforced]

These rules cannot be bypassed — the toolkit will raise an error or
return warnings:

- **`.page` overflow**: any `.page` div whose content exceeds its
  declared height fails the render. The error names the page and the
  first overflowing element. Fix by moving content to a new `.page`,
  switching the section to flow layout, or reducing density.
- **No fake pages**: a page-sized container (≈A4 width) that uses
  `min-height` and has content overflowing past that minimum is
  rejected. This is the "one `<div class='container'>` for a multi-
  page brochure" anti-pattern — Chromium paginates the long block,
  but absolute-positioned footers anchor to the container, background
  colors break at the page gutter, and section spacing doesn't align
  to page boundaries. Fix by using one `<div class="page">` per page
  (`height: 297mm`, never `min-height`), or by dropping the page-sized
  wrapper entirely and letting body content flow with
  `page-break-before` between sections.
- **File size cap**: PDFs above 20 MB after maximum compression are
  rejected with a list of the heaviest images. Below the cap the
  toolkit always optimizes automatically: oversized raster images are
  downscaled and recompressed at embed time, then the file runs through
  pymupdf clean → ghostscript /ebook → /screen (plus a transparency
  flatten when artifact-prone effects are present).
- **Bug-class warnings** (non-blocking, surfaced in the tool result):
  any `font-size` in `px`, inline-SVG/1×1-GIF placeholder images
  (silent image fetch failures), text rendered below 8pt,
  export-artifact-prone effects (see *Print-safe styling*),
  `[edge-margins]`/`[clipped-text]` when text lands within 6mm of or
  past the paper edge, `[page-size]` when `.page` divs don't match the
  paper dimensions, `[torn-block]` when a colored block is split
  across a flow page boundary, and `[trailing-page]` when a flow
  document ends on a blank or near-empty page. Fix them or ignore
  them deliberately — they name the page and the remedy.

Everything else is your call. Long decks, dense slides, text-only
pages, repeated layouts, custom themes — all fine.

## Page dimensions

| Orientation | Width  | Height |
|-------------|--------|--------|
| Portrait    | 210mm  | 297mm  |
| Landscape   | 297mm  | 210mm  |

In CSS pixels at 96 DPI: portrait 794×1122, landscape 1122×794.

## Two layout modes

### Flow layout — for content-heavy documents

No `.page` divs. Content flows naturally and Chromium paginates
automatically. The renderer applies 25mm top/bottom, 20mm side
margins via an injected `@page` rule — declare your own
`@page { margin: … }` to override them. Use this for reports,
articles, proposals, anything where content length is unpredictable —
there is **no overflow risk**.

Chromium decides the break points. The injected hints (below) keep
headings with their content and hold tables, lists, and `.card` /
`.block` elements together. A sentence continuing on the next page is
normal; a colored box torn in half is not — give any visually-unitary
colored section the class `card` or `block` (or your own
`page-break-inside: avoid`) and the break will happen around it
instead of through it. The render flags tears as `[torn-block]`.

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
  <h1>Title</h1>
  <p>Paragraphs flow across pages.</p>

  <div style="page-break-before: always;">
    <h2>New section starts on a fresh page.</h2>
  </div>
</body>
</html>
```

### Page layout — for designed pages or slides

Each `.page` div is one rendered page. Margin is zero so the page can
hold full-bleed designs. Use this for cover pages, certificates,
slide decks, dashboards, one-pagers. **The renderer will reject
overflow** — design content to fit.

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body { font-family: 'Inter', system-ui, sans-serif; }
  .page { width: 210mm; height: 297mm; padding: 25mm 20mm; overflow: hidden; }
</style>
</head>
<body>
  <div class="page">…page 1…</div>
  <div class="page">…page 2…</div>
</body>
</html>
```

`page-break-after: always` on `.page` is unnecessary — the renderer
handles it. Use `overflow: hidden` so visual bleeds don't leak; the
toolkit will still raise on real overflow.

**For multi-page designs, use one `.page` per page** — `height: 297mm`
exact, never `min-height`. A single page-sized container with
`min-height` is rejected `[enforced]`: Chromium paginates it but
footers, backgrounds, and section rhythm break at the page gutter.

**Margins are yours in page layout** — the paper margin is zero. Give
`.page` real padding (documents: `25mm 20mm`; slides: `12mm`–`18mm`)
and keep text at least 10mm from the paper edge unless the element is
intentionally full-bleed. The render warns when text lands within 6mm
of the edge (`[edge-margins]`) or past it (`[clipped-text]`).

**Size `.page` to the paper exactly** — `210mm × 297mm` portrait,
`297mm × 210mm` landscape (matching the `landscape` argument). The
renderer puts every `.page` on its own sheet, so a wrong size shows
up as dead bands or drift rather than bleed, and the render warns
(`[page-size]`).

## Typography

- **Always use `pt` for font sizes**, never `px`. The scorecard warns
  on any `font-size: \d+px` because pixel sizes render inconsistently
  between screen preview and the rasterized PDF.
- **Minimum readable size is 8pt.** Smaller is flagged.
- **Use Google Fonts freely** via a `<link>` in `<head>`. Always
  include a system fallback so the document doesn't blank out if the
  network blip happens during render.

## Images

- **Local files**: `<img src="hero.jpg">` — paths are relative to the sandbox root.
- **Remote URLs**: `<img src="https://...">` — the toolkit HEADs the
  URL first; unreachable images fail the render.
- **CSS backgrounds** are also resolved: `background-image: url(...)`.
- **Optimization is automatic.** At embed time the toolkit downscales
  oversized raster images (long edge capped ~2000px) and JPEG-encodes
  opaque ones; after render it runs the ghostscript cascade. Don't
  hand-optimize.
- **Crop to what you show.** `object-fit: cover` crops only *visually* —
  the full source is still embedded (then downsampled from). If you need
  just a region of a large screenshot, crop the file to that region
  first (e.g. with Pillow) so you embed the part you actually display.

If your PDF still exceeds the 20 MB cap, the error message lists the
heaviest images. Replace them or call out to the agent's image
generator with smaller resolutions.

## Links & interactivity

`<a href>` becomes a clickable link in the PDF — web (`https://…`), email
(`mailto:…`), phone (`tel:…`), and in-document anchors (`href="#section"`)
all work. Use them freely for CTAs and contact details. Links and the
document outline (bookmarks) are preserved automatically through
compression and the transparency flatten, so a "Book a call" button stays
clickable in the exported file. (Fillable form fields are *not* preserved
through compression — don't rely on them.)

## Print-safe styling (avoid export artifacts)

Chrome's print-to-PDF turns `box-shadow`, `backdrop-filter`, CSS
`filter: blur()/drop-shadow()`, blend modes, and large semi-transparent
overlays into transparency groups. They look perfect in the browser
preview, but some PDF viewers (notably macOS Preview) render them as gray
rectangles in the exported file. The renderer auto-flattens the PDF when
it detects these effects — which removes the artifact — but for the
cleanest, lightest result, prefer print-safe styling:

- **Cards over images**: don't put `box-shadow` on a card that also clips
  a rounded image (`overflow: hidden` + `border-radius`) — the worst
  offender. Use a hairline `border` for definition, or keep the shadow
  tiny (a few pt of blur, no spread).
- **Don't** stack a shadowed, absolutely-positioned element (a number
  badge, a sticker) directly over an image.
- **Overlays/glows**: build them with solid fills or `linear-`/`radial-`
  gradients, not big `opacity`/`rgba()` blobs or `backdrop-filter`.
- Backgrounds, gradients, and colors all render reliably — use them
  freely. The scorecard flags artifact-prone effects in the tool result.

## Page-break hints (the toolkit already adds these)

The toolkit injects:

- `@page { size: A4 [landscape]; margin: … }` matching the layout
  mode (zero for page layout, 25mm/20mm for flow) and the
  `landscape` argument
- `body { margin: 0; print-color-adjust: exact; }`
- `page-break-after: avoid` on `h1`–`h6`
- `page-break-inside: avoid` on `table`, `figure`, `blockquote`,
  `ul`, `ol`, `pre`, `tr`, `.card`, `.block`
- `img { max-width: 100%; page-break-inside: avoid; }`
- `.page + .page { page-break-before: always; }` — every `.page`
  starts on a fresh sheet

You don't need to repeat these. Your own CSS takes precedence, so
override only when you have a specific reason.

## Workflow

For any non-trivial document or deck:

```bash
# 1. Write the HTML to doc.html with your file writing tool so you can iterate with your file editing tool.

# 2. (Page layout only) Preview-validate overflow before rendering.
python system/skills/documents/scripts/validate_html.py doc.html
#   exits non-zero on overflow with the offending page named

# 3. Render. Auto-compresses; returns size + warnings.
pretty_docs html_to_pdf --json '{"html_file_name": "doc.html", "output_file_name": "doc.pdf"}'

# 4. Sample pages for visual review.
python system/skills/documents/scripts/preview_pdf.py doc.pdf

# 5. Look at the sampled images: open each .preview/doc/page-NN.jpg with your file reading tool, as an image.
```

Iterate on `doc.html` with your file editing tool between steps; only the
parts you change need to be regenerated.

For external PDFs (uploads, files you wrote, Word→PDF) that need to be
shrunk:

```bash
python system/skills/documents/scripts/optimize_pdf.py path/to.pdf
```
