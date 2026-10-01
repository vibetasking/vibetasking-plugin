---
name: provenance
description: Stamp AI-provenance metadata into media and documents you build yourself
  when they leave the platform by a path it does not stamp for you, such as an upload
  to a third-party service or a published page
---

# AI provenance marking

EU law requires machine-readable marking on AI-generated content. The platform stamps what it delivers for you: files produced by its generation tools (image, video, music, and speech generation) carry it from the start, and reply attachments, channel sends and email attachments are stamped on the way out when the format allows it (PDF, Office documents, PNG, JPEG, WebP, MP4, MOV, MP3, WAV, FLAC, Opus). Images, video and audio other than Opus also carry signed Content Credentials, which any later edit of the file breaks, so upload a generated file as it came out when you can. Anything you build yourself that leaves by another path (an upload to a third-party service, a published page, a video you compose) must be stamped before it goes. Files that stay inside the platform need nothing.

The declaration is always the same two values: the IPTC digital source type `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia` and the credit `AI-generated`. Stamp after the file is final, since re-encoding or regenerating a file can strip metadata.

## Video and audio (mp4, mov, mp3, wav)

Write the tags in place with mutagen, the library the platform marks its own output with. It touches no frame or sample, and an ffmpeg remux would keep only the comment in MP4, MOV and WAV.

```bash
python - <<'EOF'
import os
from mutagen.id3 import TXXX
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4FreeForm
from mutagen.wave import WAVE
path = "out.mp4"
source_type = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
ext = os.path.splitext(path)[1].lower()
if ext in (".mp4", ".mov"):
    media = MP4(path)
    if media.tags is None:
        media.add_tags()
    media.tags["----:org.iptc.newscodes:DigitalSourceType"] = [MP4FreeForm(source_type.encode())]
    media.tags["\xa9cmt"] = ["AI-generated"]
else:
    media = MP3(path) if ext == ".mp3" else WAVE(path)
    if media.tags is None:
        media.add_tags()
    media.tags.add(TXXX(encoding=3, desc="DigitalSourceType", text=[source_type]))
media.save()
EOF
```

## PDF

```bash
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
credit = "AI-generated http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
    for item in src.namelist():
        data = src.read(item)
        if item == "docProps/core.xml":
            text = data.decode("utf-8")
            text, found = re.subn(
                r"<dc:description(\s[^>]*)?/>|<dc:description(\s[^>]*)?>(.*?)</dc:description>",
                lambda m: "<dc:description" + (m.group(1) or m.group(2) or "").rstrip() + ">"
                + ((m.group(3) or "") + " " + credit).strip() + "</dc:description>",
                text,
                count=1,
                flags=re.S,
            )
            if not found:
                text = text.replace(
                    "</cp:coreProperties>",
                    '<dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">' + credit + "</dc:description></cp:coreProperties>",
                )
            data = text.encode("utf-8")
        dst.writestr(item, data)
shutil.move(tmp, path)
EOF
```

## Images (png, jpg)

Images from the platform's image generation are already marked. For an image you composed yourself (png, jpg, webp), write the XMP fields in place with exiftool, which leaves the pixels, the frames and the author's own metadata untouched:

```bash
exiftool -overwrite_original \
  -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
  -XMP-photoshop:Credit="AI-generated" chart.png
```
