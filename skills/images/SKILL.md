---
name: images
description: Image generation and editing
---

# Images (BananaToolkit)

## Commands

### Generate image

```bash
banana generate_image --json '{"prompt": "A serene mountain landscape at golden hour, wide-angle shot", "path": "landscape.jpg", "aspect_ratio": "16:9", "resolution": "2K"}'
```

Parameters:
- `prompt` (str, required): describe the image. Be hyper-specific for more control.
- `files` (list[str], optional): source file paths to edit or use as context. Accepts images, PDFs, CSV and text files.
- `path` (str): output path, default "image.jpg"
- `aspect_ratio` (str): "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9". Default "16:9"
- `resolution` (str): "512px", "1K", "2K", "4K". Default "1K"
- `thinking` (str): "minimal" (default) or "high". Use "high" for dense infographics, many labels or complex layouts, where planning before drawing pays off

Source photos in `files` may be HEIC even when named `.jpg` (iPhones do this). `generate_image` reads HEIC directly, so you can pass them as-is. If a different tool rejects such a file because of its extension, convert it first:

```bash
file photo.jpg                       # e.g. "ISO Media, HEIF Image (HEVC)" -> it is HEIC, not JPEG
convert photo.jpg photo_fixed.jpg    # ImageMagick reads by content and re-encodes a real JPEG
```

`convert` detects the true format from the file content, so the wrong extension does not matter.

Image generation prompting tips:
- Always provide context (the "why" or "for whom").
- For specific text in the image, include it in double quotes in the prompt.
- Describe positively ("an empty street") not negatively ("no cars, no people").
- For complex scenes, break into steps: "First, draw a street, then add a car."
- Use photographic language (wide-angle shot, macro, low-angle, etc.).
- When editing people: "Keep the person's facial features exactly the same."
- When editing images, or using them as inspiration, send them in the `files` parameter.
- Iterate on an image this tool made by passing it back in `files` and describing only the change ("make the title Spanish, change nothing else"). The model continues from where that image left off, so small steps keep everything else intact. Regenerating from scratch loses it.
- Capable of infographics, charts, text rendering, real-time data, and translating text in images.
- Use images to enrich presentations and documents (see the presentations and documents skills).
- The output has no transparent background. For a cutout asset, generate the subject on a plain white background, then key it out: `convert in.png -fuzz 10% -transparent white out.png`.

To find existing images on the web rather than generate them, `image_search` is covered in the research skill.
