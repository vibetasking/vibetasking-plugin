#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  frame.sh <video-file> [--time HH:MM:SS] [--index N] [--interval SECONDS] --out /path/to/frame.jpg

Examples:
  frame.sh video.mp4 --out /tmp/frame.jpg
  frame.sh video.mp4 --time 00:00:10 --out /tmp/frame-10s.jpg
  frame.sh video.mp4 --index 0 --out /tmp/frame0.png
  frame.sh video.mp4 --interval 5 --out /tmp/frames/frame.jpg
EOF
  exit 2
}

if [[ "${1:-}" == "" || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
fi

in="${1:-}"
shift || true

time=""
index=""
interval=""
out=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --time)
      time="${2:-}"
      shift 2
      ;;
    --index)
      index="${2:-}"
      shift 2
      ;;
    --interval)
      interval="${2:-}"
      shift 2
      ;;
    --out)
      out="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      ;;
  esac
done

if [[ ! -f "$in" ]]; then
  echo "File not found: $in" >&2
  exit 1
fi

if [[ "$out" == "" ]]; then
  echo "Missing --out" >&2
  usage
fi

mkdir -p "$(dirname "$out")"

if [[ "$interval" != "" ]]; then
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$in")
  if ! awk -v d="$duration" 'BEGIN { exit !(d + 0 > 0) }'; then
    echo "No duration for $in (ffprobe gave '$duration')" >&2
    exit 1
  fi
  base="${out%.*}"
  ext="${out##*.}"
  t=0
  # Compared against the fractional duration, so 5s into a 5.5s clip is still sampled
  while awk -v t="$t" -v d="$duration" 'BEGIN { exit !(t < d) }'; do
    ts=$(printf "%05d" "$t")
    ffmpeg -hide_banner -loglevel error -y \
      -ss "$t" \
      -i "$in" \
      -frames:v 1 \
      "${base}-${ts}.${ext}"
    echo "${base}-${ts}.${ext}"
    t=$((t + interval))
  done
  exit 0
elif [[ "$index" != "" ]]; then
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -vf "select=eq(n\\,${index})" \
    -vframes 1 \
    "$out"
elif [[ "$time" != "" ]]; then
  ffmpeg -hide_banner -loglevel error -y \
    -ss "$time" \
    -i "$in" \
    -frames:v 1 \
    "$out"
else
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -vf "select=eq(n\\,0)" \
    -vframes 1 \
    "$out"
fi

echo "$out"
