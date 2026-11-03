#!/bin/sh
# KairoX86's own checks, after the shared ones (shared/tools/check-app.sh).
set -e
python3 tools/make_font_rom.py . --check
