import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import pymupdf  # type: ignore
except ImportError:
    pymupdf = None  # type: ignore


def _default_sample_count(page_count: int) -> int:
    """Scale sampling with deck length."""

    if page_count <= 5:
        return min(page_count, 3)
    if page_count <= 15:
        return 3
    if page_count <= 40:
        return 5
    return 8


def _evenly_spaced(page_count: int, n: int) -> list[int]:
    """Return n distinct page indices (0-based) evenly spread across the deck."""

    if page_count <= 0:
        return []
    if n >= page_count:
        return list(range(page_count))
    if n == 1:
        return [0]
    step = (page_count - 1) / (n - 1)
    seen: list[int] = []
    for i in range(n):
        idx = round(i * step)
        if not seen or idx != seen[-1]:
            seen.append(idx)
    return seen


def _parse_pages(spec: str, page_count: int) -> list[int]:
    """Parse `--pages 1,3,7` into a sorted list of 0-based indices."""

    indices: list[int] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            n = int(token)
        except ValueError:
            print(f"Error: '--pages' contains a non-integer token: {token!r}", file=sys.stderr)
            sys.exit(2)
        if n < 1 or n > page_count:
            print(f"Error: '--pages' contains out-of-range page: {n} (deck has {page_count})", file=sys.stderr)
            sys.exit(2)
        indices.append(n - 1)
    return sorted(set(indices))


def _render_with_pymupdf(pdf: Path, indices: list[int], out_dir: Path, dpi: int) -> list[Path]:
    written: list[Path] = []
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    with pymupdf.open(pdf) as doc:
        for idx in indices:
            page = doc.load_page(idx)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out_path = out_dir / f"page-{idx + 1:02d}.jpg"
            pix.save(out_path)
            written.append(out_path)
    return written


def _render_with_pdftoppm(pdf: Path, indices: list[int], out_dir: Path, dpi: int) -> list[Path]:
    if not shutil.which("pdftoppm"):
        print("Error: neither pymupdf nor pdftoppm is available to render the PDF.", file=sys.stderr)
        sys.exit(2)

    written: list[Path] = []
    for idx in indices:
        page_no = idx + 1
        prefix = out_dir / f"page-{page_no:02d}"
        try:
            subprocess.run(
                ["pdftoppm", "-jpeg", "-r", str(dpi), "-f", str(page_no), "-l", str(page_no), str(pdf), str(prefix)],
                check=True,
                capture_output=True,
                timeout=60,
            )

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"Error: pdftoppm failed on page {page_no}: {exc}", file=sys.stderr)
            sys.exit(2)
        # pdftoppm appends `-N.jpg` even when rendering a single page.
        for candidate in sorted(out_dir.glob(f"page-{page_no:02d}*.jpg")):
            shutil.move(str(candidate), str(out_dir / f"page-{page_no:02d}.jpg"))
            written.append(out_dir / f"page-{page_no:02d}.jpg")
            break
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Render sampled PDF pages as JPEGs")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--sample", type=int, help="Render N evenly-spaced pages")
    parser.add_argument("--all", action="store_true", help="Render every page (overrides --sample)")
    parser.add_argument("--pages", help="Explicit page list, 1-indexed, comma-separated (e.g. '1,5,12')")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI (default 150)")
    parser.add_argument("--out", default=".preview", help="Output base directory (default .preview)")
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.is_file():
        print(f"Error: {pdf} does not exist or is not a file", file=sys.stderr)
        return 2

    if pymupdf is not None:
        with pymupdf.open(pdf) as doc:
            page_count = doc.page_count
    else:
        try:
            result = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True, timeout=30)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            print("Error: cannot determine page count (pymupdf and pdfinfo both unavailable).", file=sys.stderr)
            return 2
        page_count = 0
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                page_count = int(line.split(":", 1)[1].strip())
                break

    if page_count <= 0:
        print(f"Error: {pdf} has no pages.", file=sys.stderr)
        return 2

    if args.pages:
        indices = _parse_pages(args.pages, page_count)
    elif args.all:
        indices = list(range(page_count))
    else:
        n = args.sample or _default_sample_count(page_count)
        indices = _evenly_spaced(page_count, n)

    out_dir = Path(args.out) / pdf.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    if pymupdf is not None:
        written = _render_with_pymupdf(pdf, indices, out_dir, args.dpi)
    else:
        written = _render_with_pdftoppm(pdf, indices, out_dir, args.dpi)

    print(f"Rendered {len(written)} of {page_count} pages from {pdf} at {args.dpi} DPI:")
    for p in written:
        print(f"  {p}")
    print("\nOpen the previews with your file reading tool, as images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
