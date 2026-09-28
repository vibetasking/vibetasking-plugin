---
name: provenance
description: Stamp AI-provenance metadata into media and documents you produce before
  they leave the platform
---

# AI provenance marking

EU law requires machine-readable marking on AI-generated content. The platform stamps what it delivers for you: files produced by its generation tools (image, video, music, and speech generation) carry it from the start, and reply attachments, channel sends and email attachments are stamped on the way out when the format allows it (PDF, Office documents, PNG, MP4, MP3, WAV). Anything you build yourself that leaves by another path (an upload to a third-party service, a published page, a JPEG, a video you compose) must be stamped before it goes. Files that stay inside the platform need nothing.

The declaration is always the same two values: the IPTC digital source type `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia` and the credit `AI-generated`. Stamp after the file is final, since re-encoding or regenerating a file can strip metadata.

## Video and audio (mp4, mov, mp3, wav)

A lossless remux, no re-encode:

```bash
ffmpeg -i out.mp4 -c copy -metadata comment="AI-generated" \
  -metadata digital_source_type="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
  out.marked.mp4 && mv out.marked.mp4 out.mp4
```

## PDF

```bash
pip install --quiet pypdf
python - <<'EOF'
from pypdf import PdfWriter
path = "report.pdf"
w = PdfWriter(clone_from=path)
w.add_metadata({
    "/Subject": "AI-generated",
    "/DigitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
})
with open(path, "wb") as f:
    w.write(f)
EOF
```

## Office documents (docx, xlsx, pptx)

Standard library only:

```bash
python - <<'EOF'
import re, shutil, zipfile
path = "report.docx"
tmp = path + ".marked"
block = "<dc:subject>AI-generated http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia</dc:subject>"
with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
    for item in src.namelist():
        data = src.read(item)
        if item == "docProps/core.xml":
            text = data.decode("utf-8")
            if "<dc:subject>" in text:
                text = re.sub(r"<dc:subject>.*?</dc:subject>", block, text)
            else:
                text = text.replace("</cp:coreProperties>", block + "</cp:coreProperties>")
            data = text.encode("utf-8")
        dst.writestr(item, data)
shutil.move(tmp, path)
EOF
```

## Images (png, jpg)

Images from the platform's image generation are already marked. For an image you composed yourself:

```bash
python - <<'EOF'
from PIL import Image
from PIL.PngImagePlugin import PngInfo
path = "chart.png"
img = Image.open(path)
info = PngInfo()
info.add_text("comment", "AI-generated")
info.add_text("digital_source_type", "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia")
img.save(path, pnginfo=info)
EOF
```

For jpg, use ImageMagick instead: `magick in.jpg -set comment "AI-generated trainedAlgorithmicMedia" out.jpg && mv out.jpg in.jpg`.
