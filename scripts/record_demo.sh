#!/usr/bin/env bash
#
# Regenerate the SemShift terminal demo (assets/demo.cast and an optional GIF).
#
# The committed assets/demo.svg is a hand-authored, static "screenshot" that
# renders reliably on GitHub (GitHub's image proxy may strip SVG animation).
# Use this script when you want a *real* recorded GIF for social posts, the
# landing page, or a Product Hunt gallery.
#
# Requirements (install what you need):
#   - asciinema   : record the cast            -> https://asciinema.org
#   - agg         : cast -> gif (recommended)  -> https://github.com/asciinema/agg
#     (or svg-term-cli for cast -> animated SVG -> https://github.com/marionebl/svg-term-cli)
#   - semshift    : pip install -e ".[dev]"
#
# Usage:
#   ./scripts/record_demo.sh           # records assets/demo.cast then builds assets/demo.gif
#   ./scripts/record_demo.sh --cast    # only re-record the cast
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAST="$ROOT/assets/demo.cast"
GIF="$ROOT/assets/demo.gif"

CMD='semshift compare examples/old_policy.md examples/new_policy.md --mode policy'

record_cast() {
  command -v asciinema >/dev/null 2>&1 || { echo "asciinema not found; see header for install"; exit 1; }
  echo "Recording: $CMD"
  # -c runs the command non-interactively and captures its output into the cast.
  asciinema rec --overwrite -c "$CMD" "$CAST"
  echo "Wrote $CAST"
}

build_gif() {
  if command -v agg >/dev/null 2>&1; then
    agg --theme monokai --font-size 22 "$CAST" "$GIF"
    echo "Wrote $GIF"
  else
    echo "agg not found; skipping GIF. Install agg, or use:"
    echo "  svg-term --in '$CAST' --out assets/demo.svg --window"
  fi
}

case "${1:-all}" in
  --cast) record_cast ;;
  all)    record_cast; build_gif ;;
  *)      echo "usage: $0 [--cast]"; exit 2 ;;
esac
