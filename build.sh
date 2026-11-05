#!/bin/sh
set -eu
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT HUP INT TERM
javac --release 8 -encoding UTF-8 -d "$OUT" PlaybackPolicy.java SteeringWheelControls.java
mkdir -p dist
jar cf dist/carplay-steering-wheel-controls.jar -C "$OUT" .
echo "Built dist/carplay-steering-wheel-controls.jar"
echo "LIBRARY ONLY: requires a target adapter and compatible runtime; not a firmware installer."
