import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pdf_lib import MEASURE_PAGES_JS, ensure_document_structure, launch_chromium, load_print_layout, uses_fixed_layout


async def measure(html: str, *, landscape: bool) -> dict:
    # Measure with the same injected base CSS the renderer uses (box-sizing,
    # break rules), so a validate pass can't diverge from the render verdict.
    html = ensure_document_structure(html, fixed_layout=uses_fixed_layout(html), landscape=landscape)
    viewport = {"width": 1122, "height": 794} if landscape else {"width": 794, "height": 1122}
    async with async_playwright() as p:
        browser = await launch_chromium(p, headless=True, timeout=30000)
        page = await browser.new_page(viewport=viewport)
        try:
            # The renderer's load, so a validate pass measures the layout html_to_pdf would print
            await load_print_layout(page, html, wait_until="networkidle", timeout=60000)
            return await page.evaluate(MEASURE_PAGES_JS) or {}

        finally:
            await browser.close()


def report(result: dict, *, tolerance_mm: float) -> int:
    pages = result.get("pages") or []
    fake_pages = result.get("fakePages") or []
    overflowing = [m for m in pages if (m.get("overflow_mm") or 0) > tolerance_mm]

    exit_code = 0

    if fake_pages:
        exit_code = 1
        print(f"FAKE PAGE: {len(fake_pages)} page-sized container(s) overflow their min-height.")
        for fp in fake_pages:
            print(f"  {fp.get('selector', '<unknown>')}: +{fp.get('overflow_mm', 0):.0f}mm")
        print(
            'Fix: use one `<div class="page">` per page (height: 297mm, never min-height), '
            "or drop the wrapper entirely and use flow layout with page-break-before.",
        )

    if overflowing:
        exit_code = 1
        if fake_pages:
            print("")
        print(f"OVERFLOW: {len(overflowing)} of {len(pages)} .page div(s) exceed their height.")
        for m in overflowing:
            offender = m.get("first_offender") or {}
            sel = offender.get("selector") or "<unknown>"
            txt = offender.get("text") or ""
            txt_part = f" ('{txt}')" if txt else ""
            print(f"  Page {m['index'] + 1}: +{m['overflow_mm']:.0f}mm; first offender: {sel}{txt_part}")
        print("\nFix by moving content to a new .page, dropping the .page wrapper to use flow layout, or reducing density.")

    if exit_code == 0:
        if not pages:
            print(
                "OK: no .page divs and no fake-page containers detected: flow-layout HTML. "
                "Render via pretty_docs html_to_pdf for full checks.",
            )
        else:
            print(f"OK: {len(pages)} page(s) fit within their declared height.")

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview-validate HTML for .page overflow")
    parser.add_argument("html_file", help="Path to HTML file to check")
    parser.add_argument("--landscape", action="store_true", help="Use landscape viewport")
    parser.add_argument("--tolerance-mm", type=float, default=2.0, help="Overflow tolerance in mm (default 2.0)")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of human report")
    args = parser.parse_args()

    path = Path(args.html_file)
    if not path.is_file():
        print(f"Error: {path} does not exist or is not a file", file=sys.stderr)
        return 2

    html = path.read_text(encoding="utf-8")

    try:
        result = asyncio.run(measure(html, landscape=args.landscape))
    except Exception as exc:  # noqa: BLE001  # any render failure is reported as exit 2
        print(f"Error: failed to render HTML in Chromium: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
        overflowing = [m for m in (result.get("pages") or []) if (m.get("overflow_mm") or 0) > args.tolerance_mm]
        fake_pages = result.get("fakePages") or []
        return 1 if (overflowing or fake_pages) else 0

    return report(result, tolerance_mm=args.tolerance_mm)


if __name__ == "__main__":
    sys.exit(main())
