import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pdf_lib import format_bytes, optimize_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description="Compress a PDF")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--target-mb", type=float, default=2.0, help="Above this size, run ghostscript /ebook (default 2 MB)")
    parser.add_argument("--screen-mb", type=float, default=5.0, help="Above this size, run ghostscript /screen (default 5 MB)")
    parser.add_argument("--cap-mb", type=float, default=20.0, help="Hard cap; exit non-zero if exceeded (default 20 MB)")
    args = parser.parse_args()

    path = Path(args.pdf)
    if not path.is_file():
        print(f"Error: {path} does not exist or is not a file", file=sys.stderr)
        return 2

    result = optimize_pdf(
        path,
        target_bytes=int(args.target_mb * 1024 * 1024),
        screen_bytes=int(args.screen_mb * 1024 * 1024),
        hard_cap_bytes=int(args.cap_mb * 1024 * 1024),
    )

    print(
        f"{path.name}: {format_bytes(result.original_bytes)} → "
        f"{format_bytes(result.final_bytes)} ({result.reduction_pct:.0f}% smaller)",
    )
    print(f"steps: {', '.join(result.steps) if result.steps else '(none, already optimal)'}")

    if result.exceeded_cap:
        print(f"\nERROR: PDF still exceeds the {args.cap_mb:.0f} MB cap after maximum compression.")
        if result.heaviest_images:
            print("heaviest images:")
            for h in result.heaviest_images:
                print(f"  page {h['page']}: {format_bytes(h['bytes'])} ({h['width']}×{h['height']})")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
