# Runs both in the ocean process (loaded via importlib by ocean.utilities.media.pdf_optimize) and
# in the Daytona sandbox, which cannot import ocean.*: keep it self-contained, stdlib + pymupdf only.
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# Above TARGET_BYTES we re-encode with ghostscript /ebook (150 DPI). Kept low so image-heavy-but-small
# PDFs still get downsampled. The cascade only keeps smaller results, so a low trigger never hurts.
TARGET_BYTES = 750 * 1024
SCREEN_BYTES = 5 * 1024 * 1024
HARD_CAP_BYTES = 20 * 1024 * 1024

# Injected before the agent's own <style> blocks so agent CSS takes precedence. In Chromium a CSS @page margin overrides
# page.pdf(margin=...) and a bare `size: A4` forces portrait under prefer_css_page_size, so @page carries both here.
_BASE_CSS_TEMPLATE = """\
<style data-pretty-docs-base>
  @page { size: __PAGE_SIZE__; margin: __PAGE_MARGIN__; }
  * { box-sizing: border-box; }
  body { margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  h1, h2, h3, h4, h5, h6 { page-break-after: avoid; }
  table, figure, blockquote, ul, ol, pre, tr, .card, .block { page-break-inside: avoid; }
  img { max-width: 100%; page-break-inside: avoid; }
  .page + .page { page-break-before: always; }
</style>"""

_FLOW_PAGE_MARGIN = "25mm 20mm"

_WRAPPER = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{base_css}
</head>
<body>
{content}
</body>
</html>"""

_PT_TO_MM = 25.4 / 72
# Slack at the content edges, since font ascent shifts text bbox tops a few points
_TEAR_TOLERANCE_PT = 6.0

# Browser-side measurement for `html_to_pdf` and validate_html.py. `fakePages` are A4-wide non-`.page` containers overflowing
# their `min-height`, the brochure anti-pattern that leaves Chromium to paginate and breaks footers and backgrounds
MEASURE_PAGES_JS = r"""
() => {
  const PX_TO_MM = 25.4 / 96;
  const PX_TO_PT = 0.75;
  const PORTRAIT_W_PX = 794;   // 210mm @ 96 DPI
  const LANDSCAPE_W_PX = 1123; // 297mm @ 96 DPI
  const WIDTH_TOL_PX = 12;
  const PAGE_LIKE_MIN_PX = 700; // anything ≥ this looks like the agent meant a page

  const describe = (el) => {
    const cls = (typeof el.className === 'string' && el.className)
      ? '.' + el.className.split(/\s+/).filter(Boolean).join('.')
      : '';
    return el.tagName.toLowerCase() + cls;
  };

  const pages = Array.from(document.querySelectorAll('.page')).map((el, index) => {
    const rect = el.getBoundingClientRect();
    const overflow_px = Math.max(0, el.scrollHeight - el.clientHeight);

    let first_offender = null;
    if (overflow_px > 2) {
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT);
      let n;
      while ((n = walker.nextNode())) {
        const r = n.getBoundingClientRect();
        if (r.height > 0 && r.bottom > rect.bottom + 2) {
          first_offender = {
            selector: describe(n),
            text: (n.textContent || '').trim().slice(0, 80),
          };
          break;
        }
      }
    }

    let smallest_pt = null;
    const textWalker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let t;
    while ((t = textWalker.nextNode())) {
      if (!t.parentElement) continue;
      if (!(t.textContent || '').trim()) continue;
      const cs = getComputedStyle(t.parentElement);
      const fs_px = parseFloat(cs.fontSize);
      if (!fs_px) continue;
      const fs_pt = fs_px * PX_TO_PT;
      if (smallest_pt === null || fs_pt < smallest_pt) smallest_pt = fs_pt;
    }

    return {
      index,
      overflow_mm: overflow_px * PX_TO_MM,
      width_mm: rect.width * PX_TO_MM,
      height_mm: rect.height * PX_TO_MM,
      smallest_font_pt: smallest_pt,
      first_offender,
    };
  });

  const fakePages = [];
  document.querySelectorAll('body div, body section, body main, body article').forEach((el) => {
    if (el.classList.contains('page')) return;
    const cs = getComputedStyle(el);
    const width_px = parseFloat(cs.width);
    if (!width_px) return;
    const isPageWidth =
      Math.abs(width_px - PORTRAIT_W_PX) < WIDTH_TOL_PX ||
      Math.abs(width_px - LANDSCAPE_W_PX) < WIDTH_TOL_PX;
    if (!isPageWidth) return;

    const minH_px = (cs.minHeight && cs.minHeight !== 'auto') ? parseFloat(cs.minHeight) : 0;
    if (minH_px < PAGE_LIKE_MIN_PX) return;
    if (el.scrollHeight <= minH_px + 5) return; // fits — would be fine as a page

    fakePages.push({
      selector: describe(el),
      overflow_mm: Math.round((el.scrollHeight - minH_px) * PX_TO_MM),
    });
  });

  return { pages, fakePages };
}
"""


def uses_fixed_layout(html: str) -> bool:
    """True when any class attribute carries the exact `page` token (mirrors the `.page` selector the measurement JS queries)."""

    return any("page" in m.group(2).split() for m in re.finditer(r'class\s*=\s*(["\'])([^"\']*)\1', html))


def build_base_css(*, fixed_layout: bool, landscape: bool = False) -> str:
    """The injected print stylesheet for the given layout mode and orientation."""

    return _BASE_CSS_TEMPLATE.replace("__PAGE_SIZE__", "A4 landscape" if landscape else "A4").replace(
        "__PAGE_MARGIN__",
        "0" if fixed_layout else _FLOW_PAGE_MARGIN,
    )


def ensure_document_structure(html: str, *, fixed_layout: bool, landscape: bool = False) -> str:
    """Wrap bare HTML fragments and inject the base print CSS, shared by the renderer and validate_html.py so both see the same document."""

    base_css = build_base_css(fixed_layout=fixed_layout, landscape=landscape)
    html = html.strip()

    if not re.match(r"(?i)<!DOCTYPE|<html", html):
        return _WRAPPER.format(base_css=base_css, content=html)

    if "<head" in html.lower():
        return re.sub(r"(<head[^>]*>)", rf"\1\n{base_css}", html, count=1, flags=re.IGNORECASE)

    return re.sub(r"(<html[^>]*>)", rf"\1\n<head>\n{base_css}\n</head>", html, count=1, flags=re.IGNORECASE)


@dataclass
class OptimizeResult:
    original_bytes: int
    final_bytes: int
    page_count: int | None = None
    steps: list[str] = field(default_factory=list)
    exceeded_cap: bool = False
    heaviest_images: list[dict] = field(default_factory=list)

    @property
    def reduction_pct(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return 100.0 * (1.0 - self.final_bytes / self.original_bytes)


def format_bytes(n: int) -> str:
    """Human-readable size: 412 KB, 3.2 MB, 18.4 MB."""

    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


async def launch_chromium(playwright, **launch_kwargs):
    """Launch Chromium for rendering, falling back to the system Chrome in the base image."""

    # The bundled Playwright browser may be absent, see docs/sandbox.md
    args = list(launch_kwargs.pop("args", []) or [])
    flags = ["--disable-dev-shm-usage"]
    # Chrome's own renderer sandbox refuses to run as root (the container's user), so disable it only
    # there. Elsewhere (local dev) it stays on for process isolation.
    if getattr(os, "geteuid", lambda: 1)() == 0:
        flags.append("--no-sandbox")
    for flag in flags:
        if flag not in args:
            args.append(flag)
    launch_kwargs["args"] = args

    # The macOS app bundles are not on PATH, so local dev names them explicitly
    attempts = [dict(launch_kwargs), {**launch_kwargs, "channel": "chrome"}]
    for candidate in (
        "google-chrome",
        "chromium",
        "chromium-browser",
        "chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ):
        binary = shutil.which(candidate)
        if binary:
            attempts.append({**launch_kwargs, "executable_path": binary})

    last_error: Exception | None = None
    for kwargs in attempts:
        try:
            return await playwright.chromium.launch(**kwargs)
        except Exception as e:  # noqa: BLE001  # try the next strategy
            last_error = e

    raise RuntimeError(
        "Could not launch Chromium/Chrome for PDF rendering: bundled Playwright browser missing "
        f"and no system Chrome found. Last error: {last_error}",
    )


async def load_print_layout(page, html: str, *, wait_until: str, timeout: int) -> None:
    """Load `html` under print media, the styling page.pdf renders with, so a measurement reads the printed layout."""

    await page.emulate_media(media="print")
    await page.set_content(html, wait_until=wait_until, timeout=timeout)
    # A late webfont reflows the text, so the measurement waits for the fonts the layout ends up using
    await page.evaluate("document.fonts.ready.then(() => true)")


def optimize_pdf(
    path: str | Path,
    *,
    target_bytes: int = TARGET_BYTES,
    screen_bytes: int = SCREEN_BYTES,
    hard_cap_bytes: int = HARD_CAP_BYTES,
    flatten: bool = False,
) -> OptimizeResult:
    """Compress a PDF in place (pymupdf clean, optional transparency flatten, ghostscript downsample cascade), restoring links + outline. Returns size, page count, and steps applied."""

    path = Path(path)
    original_bytes = path.stat().st_size
    result = OptimizeResult(original_bytes=original_bytes, final_bytes=original_bytes)

    _pymupdf_clean(path, result)

    # Only a ghostscript re-distill drops links/outline (pymupdf clean keeps them),
    # so capture them just before one runs, and only when one will (see _restore_nav).
    nav = _capture_nav(path) if (flatten or result.final_bytes > target_bytes) else None

    if flatten:
        _flatten_transparency(path, result)
    if result.final_bytes > target_bytes:
        _ghostscript(path, result, preset="/ebook")
    if result.final_bytes > screen_bytes:
        _ghostscript(path, result, preset="/screen")
    if nav and any(step.startswith("ghostscript") for step in result.steps):
        _restore_nav(path, nav, result)
    if result.final_bytes > hard_cap_bytes:
        result.exceeded_cap = True
        result.heaviest_images = list_heaviest_images(path)

    return result


def _run_pdfwrite(path: Path, *, compat: str, preset: str) -> Path | None:
    """Re-distill via ghostscript into a temp file, returning its path, or None on failure or without gs."""

    if not shutil.which("gs"):
        return None

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        subprocess.run(
            [
                "gs",
                "-sDEVICE=pdfwrite",
                f"-dCompatibilityLevel={compat}",
                f"-dPDFSETTINGS={preset}",
                "-dNOPAUSE",
                "-dBATCH",
                "-dQUIET",
                f"-sOutputFile={tmp_path}",
                str(path),
            ],
            check=True,
            timeout=120,
            capture_output=True,
        )

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        tmp_path.unlink(missing_ok=True)
        return None

    if tmp_path.stat().st_size == 0:
        tmp_path.unlink(missing_ok=True)
        return None

    return tmp_path


def _commit(tmp_path: Path, path: Path, result: OptimizeResult, step: str) -> None:
    """Replace path with tmp_path and record the step + new size."""

    shutil.move(str(tmp_path), str(path))
    result.steps.append(step)
    result.final_bytes = path.stat().st_size


def _valid_same_pages(path: Path, expected: int | None) -> bool:
    """True if path opens and has the expected page count (None means accept any)."""

    if expected is None:
        return True
    try:
        with pymupdf.open(path) as doc:
            return doc.page_count == expected

    except Exception:  # noqa: BLE001  # an unreadable re-distill is simply not kept
        return False


def _flatten_transparency(path: Path, result: OptimizeResult) -> None:
    """Flatten transparency via a PDF-1.3 re-distill (removes Chrome box-shadow/overlay gray boxes on export). No-op without gs."""

    # Why 1.3: see ../reference/html-pdf.md
    tmp_path = _run_pdfwrite(path, compat="1.3", preset="/printer")
    if tmp_path is None:
        return

    # Keep regardless of size (it fixes artifacts, may not shrink), but only if valid.
    if _valid_same_pages(tmp_path, result.page_count):
        _commit(tmp_path, path, result, "ghostscript_flatten")
    else:
        tmp_path.unlink(missing_ok=True)


def _pymupdf_clean(path: Path, result: OptimizeResult) -> None:
    """Always-safe structural cleanup (dedup objects, deflate streams), also recording the page count."""

    try:
        with pymupdf.open(path) as doc:
            result.page_count = doc.page_count
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            doc.save(
                tmp_path,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
            )
        if tmp_path.stat().st_size < result.final_bytes:
            _commit(tmp_path, path, result, "pymupdf_clean")
        else:
            tmp_path.unlink(missing_ok=True)

    except Exception:  # noqa: BLE001, S110
        # pymupdf occasionally chokes on Chromium PDFs with exotic font subsets. The original file stays valid
        pass


def _ghostscript(path: Path, result: OptimizeResult, *, preset: str) -> None:
    """Re-encode via ghostscript at the given PDFSETTINGS preset, keeping the result only when smaller."""

    tmp_path = _run_pdfwrite(path, compat="1.5", preset=preset)
    if tmp_path is None:
        return

    if tmp_path.stat().st_size < result.final_bytes:
        _commit(tmp_path, path, result, f"ghostscript_{preset.lstrip('/')}")
    else:
        tmp_path.unlink(missing_ok=True)


def _capture_nav(path: Path) -> dict | None:
    """Snapshot links + outline before a ghostscript pass (pdfwrite drops them). None if unreadable."""

    try:
        with pymupdf.open(path) as doc:
            return {
                "links": [page.get_links() for page in doc],
                "toc": doc.get_toc(),
                "page_count": doc.page_count,
            }

    except Exception:  # noqa: BLE001  # an unreadable PDF has no nav to keep
        return None


def _restore_nav(path: Path, nav: dict | None, result: OptimizeResult) -> None:
    """Re-insert the links + outline a ghostscript pass stripped. No-op if the page count changed."""

    # Page geometry survives pdfwrite, so captured rects map 1:1. A page-count change means the layout
    # shifted and rects would land wrong, so bail.
    if not nav:
        return

    tmp_path: Path | None = None
    try:
        with pymupdf.open(path) as doc:
            if doc.page_count != nav["page_count"]:
                return
            restored = 0
            for page, page_links in zip(doc, nav["links"], strict=False):
                for link in page_links:
                    try:
                        page.insert_link(link)
                        restored += 1

                    except Exception:  # noqa: BLE001, S112  # one link pymupdf refuses leaves the rest restored
                        continue
            if nav["toc"]:
                try:
                    doc.set_toc(nav["toc"])
                except Exception:  # noqa: BLE001, S110  # the links still restore without the outline
                    pass
            if not (restored or nav["toc"]):
                return
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            doc.save(tmp_path, garbage=3, deflate=True)
        _commit(tmp_path, path, result, "restored_nav")

    except Exception:  # noqa: BLE001  # the compressed file stays valid without its nav
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def measure_pdf_pages(path: str | Path, max_pages: int = 200) -> list[dict]:
    """Per-page text geometry of a rendered PDF: word/image counts plus the min text distance to each paper edge in mm. Empty list when unreadable."""

    pages: list[dict] = []
    try:
        with pymupdf.open(path) as doc:
            for index, page in enumerate(doc):
                if index >= max_pages:
                    break
                words = page.get_text("words")
                entry: dict = {
                    "page": index + 1,
                    "words": len(words),
                    "images": len(page.get_images(full=True)),
                    "edges_mm": None,
                }
                if words:
                    rect = page.rect
                    entry["edges_mm"] = {
                        "left": (min(w[0] for w in words) - rect.x0) * _PT_TO_MM,
                        "top": (min(w[1] for w in words) - rect.y0) * _PT_TO_MM,
                        "right": (rect.x1 - max(w[2] for w in words)) * _PT_TO_MM,
                        "bottom": (rect.y1 - max(w[3] for w in words)) * _PT_TO_MM,
                    }
                pages.append(entry)

    except Exception:  # noqa: BLE001  # an unreadable PDF measures as no pages
        return []

    return pages


def detect_torn_fills(path: str | Path, max_pages: int = 200) -> list[dict]:
    """Same-color solid fills ending at one page's content bottom and resuming at the next page's top, as [{"pages": (n, n + 1)}]."""

    tears: list[dict] = []
    try:
        with pymupdf.open(path) as doc:
            pages: list[dict] = []
            for index, page in enumerate(doc):
                if index >= max_pages:
                    break
                edges = [(w[1], w[3]) for w in page.get_text("words")]
                fills: list[tuple] = []
                page_area = page.rect.width * page.rect.height
                for drawing in page.get_drawings():
                    fill, rect = drawing.get("fill"), drawing.get("rect")
                    if fill is None or rect is None or "f" not in (drawing.get("type") or ""):
                        continue
                    if rect.width < 40 or rect.height < 4:  # hairlines and bullets aren't blocks
                        continue
                    if rect.width * rect.height > 0.85 * page_area:  # page background, continuous by design
                        continue
                    fills.append((fill, rect))
                    edges.append((rect.y0, rect.y1))
                pages.append(
                    {
                        "fills": fills,
                        "top": min((e[0] for e in edges), default=None),
                        "bottom": max((e[1] for e in edges), default=None),
                    },
                )

            # Anchor on the document-wide content extremes (the margin lines where Chromium fragments), not
            # per-page ones: the first element on a page trivially abuts its own page's content top without being a tear.
            doc_top = min((p["top"] for p in pages if p["top"] is not None), default=None)
            doc_bottom = max((p["bottom"] for p in pages if p["bottom"] is not None), default=None)
            if doc_top is None or doc_bottom is None:
                return []

            colored_tears: list[tuple[tuple[int, int], tuple]] = []
            for i in range(len(pages) - 1):
                above, below = pages[i], pages[i + 1]
                tails = [(f, r) for f, r in above["fills"] if r.y1 >= doc_bottom - _TEAR_TOLERANCE_PT]
                heads = [(f, r) for f, r in below["fills"] if r.y0 <= doc_top + _TEAR_TOLERANCE_PT]
                for tail_fill, tail in tails:
                    if any(
                        tail_fill == head_fill
                        and min(tail.x1, head.x1) - max(tail.x0, head.x0) >= 0.7 * min(tail.width, head.width)
                        for head_fill, head in heads
                    ):
                        colored_tears.append(((i + 1, i + 2), tail_fill))

            # A color torn at most boundaries is a body/section background flowing by design (Chromium clips it to the
            # content box, dodging the page-area filter), so only repeated-tear colors drop and a single split still surfaces.
            boundaries = max(1, len(pages) - 1)
            by_color: dict = {}
            for pair, fill in colored_tears:
                by_color.setdefault(fill, []).append(pair)
            torn_pairs = {
                pair
                for fill, pairs in by_color.items()
                if not (len(pairs) >= 3 and len(pairs) / boundaries >= 0.6)
                for pair in pairs
            }
            tears.extend({"pages": pair} for pair in sorted(torn_pairs))

    except Exception:  # noqa: BLE001  # an unreadable PDF reports no tears
        return []

    return tears


def list_heaviest_images(path: Path, limit: int = 5) -> list[dict]:
    """Return the largest embedded images so the caller can surface them."""

    images: list[dict] = []
    try:
        with pymupdf.open(path) as doc:
            seen: set[int] = set()
            for page_index, page in enumerate(doc):
                for img in page.get_images(full=True):
                    xref = img[0]
                    if xref in seen:
                        continue
                    seen.add(xref)
                    try:
                        data = doc.extract_image(xref)
                    except Exception:  # noqa: BLE001, S112  # an unextractable image is left out of the ranking
                        continue
                    images.append(
                        {
                            "page": page_index + 1,
                            "bytes": len(data.get("image", b"")),
                            "width": data.get("width"),
                            "height": data.get("height"),
                            "ext": data.get("ext"),
                        },
                    )

    except Exception:  # noqa: BLE001  # an unreadable PDF lists no images
        return []

    images.sort(key=lambda item: item["bytes"], reverse=True)
    return images[:limit]
