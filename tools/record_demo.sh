#!/usr/bin/env bash
# Record the skirmish demo for a portfolio GIF / asciinema cast.
#
# Requires:
#   - pygame        (pip install pygame)        for the live window
#   - asciinema     (pip install asciinema)      for a terminal cast
#
# Headless note: with no display, `run_skirmish.py` auto-falls back to a
# text-only headless run (no window); asciinema still captures that as a cast.
#
# Usage:
#   bash tools/record_demo.sh            # records fsm vs utility, 1500 ticks
#   asciinema play demo.cast             # play it back
#   # convert to gif via `asciinema rec` + agg (https://github.com/asciinema/agg)
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHONPATH=src python examples/run_skirmish.py \
    tests/fixtures/maps/skirmish.json fsm utility 1500
