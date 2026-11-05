#!/bin/sh
set -eu
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT HUP INT TERM
javac --release 8 -encoding UTF-8 -d "$OUT" PlaybackPolicy.java SteeringWheelControls.java ControlsTest.java
java -ea -cp "$OUT" carplay.controls.ControlsTest
