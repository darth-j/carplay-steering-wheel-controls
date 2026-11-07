#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
# Part of CarPlay Steering-Wheel Controls; see LICENSE and NOTICE.md.
set -eu
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT HUP INT TERM
javac --release 8 -encoding UTF-8 -d "$OUT" PlaybackPolicy.java SteeringWheelControls.java
mkdir -p dist "$OUT/META-INF"
cp LICENSE "$OUT/META-INF/LICENSE"
cp NOTICE.md "$OUT/META-INF/NOTICE.md"
jar cf dist/carplay-steering-wheel-controls.jar -C "$OUT" .
echo "Built dist/carplay-steering-wheel-controls.jar"
echo "LIBRARY ONLY: requires a target adapter and compatible runtime; not a firmware installer."
