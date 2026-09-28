# Editing Presentations

## Template-Based Workflow

When using an existing presentation as a template:

1. **Analyze existing slides**:
   ```bash
   python system/skills/presentations/scripts/thumbnail.py template.pptx
   python -m markitdown template.pptx
   ```
   Review `thumbnails.jpg` to see layouts, and markitdown output to see placeholder text.

2. **Plan slide mapping**: For each content section, choose a template slide.

   **USE VARIED LAYOUTS** -- don't default to basic title + bullet slides. Actively seek out:
   - Multi-column layouts (2-column, 3-column)
   - Image + text combinations
   - Full-bleed images with text overlay
   - Quote or callout slides
   - Section dividers, stat/number callouts, icon grids

3. **Unpack**: `python system/skills/presentations/scripts/office/unpack.py template.pptx unpacked/`

4. **Build presentation**:
   - Delete unwanted slides (remove from `<p:sldIdLst>`)
   - Duplicate slides to reuse (`add_slide.py`)
   - Reorder slides in `<p:sldIdLst>`
   - **Complete all structural changes before step 5**

5. **Edit content**: Update text in each `slide{N}.xml`. Use your file editing tool, not sed or Python scripts.

6. **Clean**: `python system/skills/presentations/scripts/clean.py unpacked/`

7. **Pack**: `python system/skills/presentations/scripts/office/pack.py unpacked/ output.pptx --original template.pptx`

---

## Scripts

| Script | Purpose |
|--------|---------|
| `unpack.py` | Extract and pretty-print PPTX |
| `add_slide.py` | Duplicate slide or create from layout |
| `clean.py` | Remove orphaned files |
| `pack.py` | Repack with validation |
| `thumbnail.py` | Create visual grid of slides |

### unpack.py

```bash
python system/skills/presentations/scripts/office/unpack.py input.pptx unpacked/
```

Extracts PPTX, pretty-prints XML, escapes smart quotes.

### add_slide.py

```bash
python system/skills/presentations/scripts/add_slide.py unpacked/ slide2.xml      # Duplicate slide
python system/skills/presentations/scripts/add_slide.py unpacked/ slideLayout2.xml # From layout
```

Prints the `<p:sldId>` to add to `<p:sldIdLst>` at desired position, spelled with the prefixes the deck's `presentation.xml` uses.

### clean.py

```bash
python system/skills/presentations/scripts/clean.py unpacked/
```

Removes slides not in `<p:sldIdLst>`, unreferenced media, orphaned rels. Slides and relationship targets are matched by namespace and resolved part, so any prefix or target spelling works. If the list names a slide no relationship resolves, it stops and removes nothing: fix the list first.

### pack.py

```bash
python system/skills/presentations/scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

Validates against the OOXML schemas, repairs, condenses XML, re-encodes smart quotes. With `--original`, schema errors the original already carried are tolerated and only new ones fail the pack. Without it, every schema error fails the pack, so pass the template a deck came from whenever there is one.

### thumbnail.py

```bash
python system/skills/presentations/scripts/thumbnail.py input.pptx [output_prefix] [--cols N]
```

Creates `thumbnails.jpg` with slide filenames as labels. Default 3 columns, max 12 per grid.

**Use for template analysis only** (choosing layouts). For visual QA, convert with `soffice --headless --convert-to pdf output.pptx`, then sample pages with `python system/skills/documents/scripts/preview_pdf.py output.pdf` and open the renders with your file reading tool.

---

## Editing Content

For each slide:
1. Read the slide's XML
2. Identify ALL placeholder content -- text, images, charts, icons, captions
3. Replace each placeholder with final content

### Formatting Rules

- **Bold all headers, subheadings, and inline labels**: Use `b="1"` on `<a:rPr>`
- **Never use unicode bullets**: Use proper list formatting with `<a:buChar>` or `<a:buAutoNum>`
- **Bullet consistency**: Let bullets inherit from the layout

### Common Pitfalls

**Template adaptation:**
- When source has fewer items than template: **Remove excess elements entirely** (images, shapes, text boxes), don't just clear text
- When replacing text with different length: longer content may overflow or wrap unexpectedly

**Multi-Item Content:** Create separate `<a:p>` elements for each item -- never concatenate into one string.

**Smart Quotes:** When adding new text with quotes, use XML entities:

| Character | XML Entity |
|-----------|------------|
| Left double quote | `&#x201C;` |
| Right double quote | `&#x201D;` |
| Left single quote | `&#x2018;` |
| Right single quote / apostrophe | `&#x2019;` |
