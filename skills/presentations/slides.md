# HTML Slide Decks

Create slides as HTML/CSS. Output as PDF (default) or PowerPoint (.pptx).

## Output Commands

The full render workflow (write → validate → render → preview → optional PPTX) is in SKILL.md. To iterate after QA: edit `slides.html` with your file editing tool, then re-run the `html_to_pdf` command. Do not regenerate the entire HTML from scratch.

---

## Base Structure

Start from this skeleton. Each `<div class="page">` becomes one slide. It sets up the page geometry only; the design is yours.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
  @page {
    size: A4 landscape;
    margin: 0;
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .page {
    width: 297mm;
    height: 210mm;
    padding: 15mm 20mm;
    position: relative;
    overflow: hidden;
  }
</style>
</head>
<body>
  <div class="page">
    <!-- Slide 1 -->
  </div>
  <div class="page">
    <!-- Slide 2 -->
  </div>
</body>
</html>
```

---

## Slide Layout Patterns

### Title Slide

```html
<div class="page" style="
  background: linear-gradient(135deg, #1E2761, #408EC6);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: white;
">
  <h1 style="font-family: 'Playfair Display', Georgia, serif; font-size: 42pt; font-weight: 700; margin-bottom: 8mm;">Presentation Title</h1>
  <p style="font-size: 18pt; opacity: 0.85;">Subtitle or tagline goes here</p>
  <p style="font-size: 12pt; opacity: 0.6; margin-top: 15mm;">Author Name — March 2026</p>
</div>
```

### Content Slide (Two Columns)

```html
<div class="page" style="padding: 15mm 20mm;">
  <h2 style="font-size: 28pt; color: #1E2761; margin-bottom: 10mm;">Section Title</h2>
  <div style="display: flex; gap: 15mm;">
    <div style="flex: 1;">
      <h3 style="font-size: 16pt; color: #408EC6; margin-bottom: 4mm;">Left Column</h3>
      <p style="font-size: 13pt; line-height: 1.6; color: #333;">Content for the left side.</p>
    </div>
    <div style="flex: 1;">
      <h3 style="font-size: 16pt; color: #408EC6; margin-bottom: 4mm;">Right Column</h3>
      <p style="font-size: 13pt; line-height: 1.6; color: #333;">Content for the right side.</p>
    </div>
  </div>
</div>
```

### Image + Text Split

```html
<div class="page" style="display: flex; padding: 0;">
  <div style="flex: 1; padding: 20mm; display: flex; flex-direction: column; justify-content: center;">
    <h2 style="font-size: 28pt; color: #1E2761; margin-bottom: 8mm;">Key Insight</h2>
    <p style="font-size: 14pt; line-height: 1.7; color: #444;">
      Supporting text that explains the visual on the right.
    </p>
  </div>
  <div style="flex: 1; background-image: url('photo.jpg'); background-size: cover; background-position: center;"></div>
</div>
```

### Full-Bleed Image with Overlay

```html
<div class="page" style="
  background-image: url('hero.jpg');
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: flex-end;
  padding: 0;
">
  <div style="
    width: 100%;
    padding: 20mm;
    background: linear-gradient(transparent, rgba(0,0,0,0.8));
    color: white;
  ">
    <h2 style="font-size: 32pt; margin-bottom: 4mm;">Headline Over Image</h2>
    <p style="font-size: 14pt; opacity: 0.9;">Caption or supporting detail.</p>
  </div>
</div>
```

### Stats / Numbers

```html
<div class="page" style="padding: 20mm; background: #F8F9FA;">
  <h2 style="font-size: 24pt; color: #1E2761; margin-bottom: 15mm; text-align: center;">Key Metrics</h2>
  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10mm; text-align: center;">
    <div>
      <div style="font-size: 48pt; font-weight: 700; color: #408EC6;">92%</div>
      <div style="font-size: 12pt; color: #666; margin-top: 3mm;">Customer Satisfaction</div>
    </div>
    <div>
      <div style="font-size: 48pt; font-weight: 700; color: #408EC6;">3.2M</div>
      <div style="font-size: 12pt; color: #666; margin-top: 3mm;">Active Users</div>
    </div>
    <div>
      <div style="font-size: 48pt; font-weight: 700; color: #408EC6;">47%</div>
      <div style="font-size: 12pt; color: #666; margin-top: 3mm;">Year-over-Year Growth</div>
    </div>
  </div>
</div>
```

### Quote Slide

```html
<div class="page" style="
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30mm 40mm;
  color: white;
">
  <div style="font-size: 60pt; color: #408EC6; line-height: 1; margin-bottom: 5mm;">&ldquo;</div>
  <p style="font-size: 22pt; line-height: 1.6; font-style: italic; margin-bottom: 10mm;">
    The best way to predict the future is to invent it.
  </p>
  <p style="font-size: 13pt; opacity: 0.6;">— Alan Kay</p>
</div>
```

### Comparison / Before-After

```html
<div class="page" style="padding: 15mm 20mm;">
  <h2 style="font-size: 24pt; color: #1E2761; text-align: center; margin-bottom: 12mm;">Before vs. After</h2>
  <div style="display: flex; gap: 10mm; height: 70%;">
    <div style="flex: 1; background: #FFF3F3; border-radius: 4px; padding: 10mm;">
      <h3 style="font-size: 16pt; color: #C0392B; margin-bottom: 6mm;">Before</h3>
      <ul style="font-size: 13pt; line-height: 1.8; color: #555; padding-left: 5mm;">
        <li>Manual process</li>
        <li>3-day turnaround</li>
        <li>High error rate</li>
      </ul>
    </div>
    <div style="flex: 1; background: #F0FFF0; border-radius: 4px; padding: 10mm;">
      <h3 style="font-size: 16pt; color: #27AE60; margin-bottom: 6mm;">After</h3>
      <ul style="font-size: 13pt; line-height: 1.8; color: #555; padding-left: 5mm;">
        <li>Fully automated</li>
        <li>Real-time</li>
        <li>99.9% accuracy</li>
      </ul>
    </div>
  </div>
</div>
```

### Timeline / Process Flow

```html
<div class="page" style="padding: 15mm 20mm;">
  <h2 style="font-size: 24pt; color: #1E2761; margin-bottom: 15mm;">Roadmap</h2>
  <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 6mm;">
    <div style="flex: 1; text-align: center;">
      <div style="width: 40px; height: 40px; border-radius: 50%; background: #408EC6; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 5mm; font-weight: 700;">1</div>
      <h4 style="font-size: 13pt; color: #1E2761; margin-bottom: 3mm;">Research</h4>
      <p style="font-size: 11pt; color: #666;">Q1 2026</p>
    </div>
    <div style="flex: 1; text-align: center;">
      <div style="width: 40px; height: 40px; border-radius: 50%; background: #408EC6; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 5mm; font-weight: 700;">2</div>
      <h4 style="font-size: 13pt; color: #1E2761; margin-bottom: 3mm;">Prototype</h4>
      <p style="font-size: 11pt; color: #666;">Q2 2026</p>
    </div>
    <div style="flex: 1; text-align: center;">
      <div style="width: 40px; height: 40px; border-radius: 50%; background: #408EC6; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 5mm; font-weight: 700;">3</div>
      <h4 style="font-size: 13pt; color: #1E2761; margin-bottom: 3mm;">Beta</h4>
      <p style="font-size: 11pt; color: #666;">Q3 2026</p>
    </div>
    <div style="flex: 1; text-align: center;">
      <div style="width: 40px; height: 40px; border-radius: 50%; background: #27AE60; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 5mm; font-weight: 700;">4</div>
      <h4 style="font-size: 13pt; color: #1E2761; margin-bottom: 3mm;">Launch</h4>
      <p style="font-size: 11pt; color: #666;">Q4 2026</p>
    </div>
  </div>
</div>
```

---

## Styling Guide

### Dark Theme

```css
.page.dark {
  background: #1a1a2e;
  color: #F0F0F0;
}
.page.dark h2 { color: #CADCFC; }
.page.dark p { color: #CCCCCC; }
```

### Gradient Backgrounds

```css
/* Diagonal */
background: linear-gradient(135deg, #1E2761, #408EC6);

/* Radial spotlight */
background: radial-gradient(circle at 30% 40%, #408EC6 0%, #1E2761 70%);

/* Multi-stop */
background: linear-gradient(to right, #2C5F2D, #97BC62, #F5F5F5);
```

### Cards with Shadows

Keep shadows subtle. Heavy `box-shadow` blur — and any `box-shadow` on a
card that also clips a rounded image (`overflow: hidden` +
`border-radius`) — can rasterize as a gray rectangle in the exported PDF
(see *Common Pitfalls*). A hairline border is the safest alternative.

```css
.card {
  background: white;
  border-radius: 6px;
  padding: 8mm;
  border: 1px solid rgba(0, 0, 0, 0.08); /* print-safe definition */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* keep blur small; drop on image cards */
}
```

### CSS Grid Layouts

```css
/* 2x2 grid */
.grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 8mm;
  height: 100%;
}

/* 3-column feature row */
.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10mm;
}
```

---

## Adding Images

### Inline Images

```html
<!-- Local file (relative to the sandbox root) -->
<img src="chart.png" style="width: 100%; border-radius: 4px;" />

<!-- Remote URL (Playwright fetches during rendering) -->
<img src="https://example.com/photo.jpg" style="width: 50%; object-fit: cover;" />
```

### Background Images

```html
<div class="page" style="
  background-image: url('hero.jpg');
  background-size: cover;
  background-position: center;
">
```

### Image Grid

```html
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm;">
  <img src="img1.jpg" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px;" />
  <img src="img2.jpg" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px;" />
  <img src="img3.jpg" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px;" />
</div>
```

### Using Generated & Searched Images

Generate with `banana generate_image`, search with `image_search`, download with `curl` (commands in SKILL.md's "Enriching slides with images"). Then embed in your HTML:

```html
<div class="page" style="background-image: url('bg.jpg'); background-size: cover;">
  <!-- content over generated background -->
</div>

<img src="team.jpg" style="width: 100%; object-fit: cover; height: 140mm;" />
```

---

## Common Pitfalls

1. **Overflow fails the render** — if a slide's content exceeds the `.page` height, the renderer rejects the PDF and names the offending page. Use `height: 210mm` (exact), **never** `min-height`, plus `overflow: hidden` to bound content. When content genuinely won't fit, split across slides rather than shrinking type. Preview-validate with `python system/skills/documents/scripts/validate_html.py slides.html --landscape` before rendering.
2. **Font units** — always use `pt` for font sizes, never `px`. Pixel sizes render inconsistently across DPIs and the scorecard warns on any `font-size: \d+px`.
3. **Print-color-adjust** — the toolkit injects `print-color-adjust: exact` on `body` so backgrounds render. Don't override it.
4. **Image loading** — remote URLs must be reachable; the toolkit HEADs each one first. Download images locally for reliability across re-renders.
5. **Fonts** — Google Fonts work well (Playwright fetches them during rendering). Add a `<link>` tag in `<head>` and reference the font in CSS. Good pairings: Inter + Playfair Display, Montserrat + Lora, Raleway + Merriweather, Poppins + Source Serif 4. Always include a system font fallback (e.g. `font-family: 'Inter', 'Segoe UI', sans-serif`).
6. **PDF first, PPTX second** — always generate and inspect the PDF first. The PPTX conversion screenshots exactly what Playwright renders, so fix issues in PDF before converting.
7. **Export artifacts (gray boxes)** — `box-shadow`, `backdrop-filter`, `filter: blur()/drop-shadow()`, blend modes, and large semi-transparent overlays become transparency groups that some PDF viewers (macOS Preview) render as gray rectangles, even though they look fine in the browser. The renderer auto-flattens to mitigate, but prefer print-safe styling: hairline borders over shadows on image cards, gradients/solid fills over `rgba()` blobs. See *Print-safe styling* in `html-pdf.md`.
