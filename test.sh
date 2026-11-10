#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
# Part of CarPlay Steering-Wheel Controls; see LICENSE and NOTICE.md.
set -eu
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT HUP INT TERM
javac --release 8 -encoding UTF-8 -d "$OUT" PlaybackPolicy.java SteeringWheelControls.java ControlsTest.java
java -ea -cp "$OUT" carplay.controls.ControlsTest
