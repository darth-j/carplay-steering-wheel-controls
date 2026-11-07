/*
 * SPDX-License-Identifier: GPL-3.0-only
 * Copyright (C) 2026 Skywalker (darth-j)
 *
 * This file is part of CarPlay Steering-Wheel Controls.
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 * This program is distributed WITHOUT ANY WARRANTY; without even the
 * implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE and NOTICE.md for licensing and source attribution.
 */
package carplay.controls;

/** Portable reference logic. Hardware adapters must supply logical events. */
public final class SteeringWheelControls {
    public static final int STAR = 1, ROLLER = 2, VOICE = 3, NAVIGATION_VOICE = 4;
    public static final int PRESS = 1, RELEASE = 0, LONG_PRESS = 3, DOUBLE_PRESS = 2;
    public static final int NEXT = 9, PREVIOUS = 10, ANSWER = 13, PAUSE = 18, PLAY = 19;
    public static final int IDLE = 0, INCOMING = 1, IN_CALL = 2;

    public interface Port {
        void mediaButton(int button);
        boolean hasMediaFocus();
        void requestMediaFocus();
        void showCarPlay();
        void openDevicePicker();
        void siriPressed();
        void siriLongDetected();
        void siriReleasedAfterLongPress();
        void endCallKey(boolean released);
    }
    /** Use a monotonic clock in production. */
    public interface Clock { long nowMillis(); }
    /** Must schedule without blocking the input/event thread. */
    public interface Scheduler { void after(long delayMillis, Runnable job); }

    private static final class Capture {
        boolean active, suppressShort, phoneEnd, reject;
        void clear() { active = suppressShort = phoneEnd = reject = false; }
    }
    private final Port port;
    private final Clock clock;
    private final Scheduler scheduler;
    private final long rejectHoldMillis;
    private final PlaybackPolicy policy = new PlaybackPolicy();
    private final Capture[] captures = {new Capture(), new Capture(), new Capture(), new Capture()};
    private boolean connected, carPlayPage, inputAllowed = true;
    private int playbackState, callPhase;
    private boolean endKeyDown, releasePending;
    private long endPressedAt;
    private int endGeneration;

    public SteeringWheelControls(Port port, Clock clock, Scheduler scheduler) {
        this(port, clock, scheduler, 1500L);
    }
    public SteeringWheelControls(Port port, Clock clock, Scheduler scheduler, long rejectHoldMillis) {
        if (port == null || clock == null || scheduler == null || rejectHoldMillis < 0)
            throw new IllegalArgumentException("Invalid controls configuration");
        this.port = port; this.clock = clock; this.scheduler = scheduler;
        this.rejectHoldMillis = rejectHoldMillis;
    }
    public PlaybackPolicy playbackPolicy() { return policy; }
    public synchronized int callPhase() { return callPhase; }

    public synchronized void updateConnection(boolean isConnected, boolean isCarPlayPage) {
        if (isConnected && !connected) { playbackState = 0; policy.beginConnection(); }
        if (!isConnected) {
            policy.endConnection(); playbackState = 0; callPhase = IDLE;
            cancelCaptures();
        }
        connected = isConnected; carPlayPage = isConnected && isCarPlayPage;
    }
    public synchronized void setInputAllowed(boolean allowed) {
        inputAllowed = allowed;
        if (!allowed) cancelCaptures();
    }
    public synchronized void updatePlayback(int state, boolean valid) {
        if (valid && connected) { playbackState = state; policy.observe(state, true); }
    }
    /** Pass status/direction only. Numbers, names and identifiers are unnecessary. */
    public synchronized void updateCalls(int[] statuses, int[] directions, boolean valid) {
        if (!valid) return;
        if (statuses == null || directions == null || statuses.length != directions.length)
            throw new IllegalArgumentException("Call arrays must have equal lengths");
        int phase = IDLE;
        if (connected) for (int i = 0; i < statuses.length; i++) {
            if (statuses[i] == 3 && directions[i] == 0) { phase = INCOMING; break; }
            if (statuses[i] == 1 || statuses[i] == 2 || statuses[i] == 3) phase = IN_CALL;
        }
        callPhase = phase;
    }

    /** @return true only when this library consumed the steering-wheel event. */
    public synchronized boolean onKey(int key, int event, boolean steeringWheelSource) {
        if (!steeringWheelSource || !inputAllowed || key < STAR || key > NAVIGATION_VOICE) return false;
        Capture c = captures[key - 1];
        if (event == PRESS) {
            if (c.active) return true;
            if (key != VOICE && !(connected && (carPlayPage || callPhase != IDLE))) return false;
            c.active = true;
            if (key == NAVIGATION_VOICE && callPhase != IDLE) {
                c.phoneEnd = true; c.reject = callPhase == INCOMING; pressEndKey();
            }
            return true;
        }
        if (!c.active) return false;
        if (event == LONG_PRESS || event == DOUBLE_PRESS) { c.suppressShort = true; return true; }
        if (event != RELEASE) return false;
        try {
            if (c.phoneEnd) releaseEndKey(c.reject);
            else if (!c.suppressShort) shortAction(key);
        } finally { c.clear(); }
        return true;
    }

    private void shortAction(int key) {
        if (!connected) { if (key == VOICE) port.openDevicePicker(); return; }
        if (callPhase != IDLE) {
            if (key == VOICE) port.showCarPlay();
            else if (key == STAR && callPhase == INCOMING) port.mediaButton(ANSWER);
            else if (key == NAVIGATION_VOICE) { pressEndKey(); releaseEndKey(callPhase == INCOMING); }
            return;
        }
        if (key == VOICE) {
            if (!carPlayPage) { port.showCarPlay(); return; }
            port.siriPressed();
            try { port.siriLongDetected(); }
            finally { port.siriReleasedAfterLongPress(); }
            return;
        }
        if (!carPlayPage) return;
        policy.userTransportRequested();
        if (key == ROLLER) {
            if (PlaybackPolicy.isPlaying(playbackState)) port.mediaButton(PAUSE);
            else { requestFocusIfNeeded(); port.mediaButton(PLAY); }
        } else {
            requestFocusIfNeeded();
            if (key == STAR) port.mediaButton(NEXT);
            else if (key == NAVIGATION_VOICE) port.mediaButton(PREVIOUS);
        }
    }
    private void requestFocusIfNeeded() { if (!port.hasMediaFocus()) port.requestMediaFocus(); }
    private void pressEndKey() {
        if (endKeyDown) return;
        port.endCallKey(false); endKeyDown = true;
        endPressedAt = clock.nowMillis(); endGeneration++;
    }
    private void releaseEndKey(boolean reject) {
        if (!endKeyDown || releasePending) return;
        long elapsed = Math.max(0L, clock.nowMillis() - endPressedAt);
        long delay = reject ? Math.max(0L, rejectHoldMillis - elapsed) : 0L;
        if (delay == 0) { finishEndKey(); return; }
        final int generation = endGeneration;
        releasePending = true;
        try {
            scheduler.after(delay, new Runnable() {
                public void run() {
                    synchronized (SteeringWheelControls.this) {
                        if (endGeneration == generation && endKeyDown) finishEndKey();
                    }
                }
            });
        } catch (RuntimeException failure) { finishEndKey(); throw failure; }
    }
    private void finishEndKey() {
        try { if (endKeyDown) port.endCallKey(true); }
        finally { endKeyDown = false; releasePending = false; }
    }
    private void cancelCaptures() {
        try { if (endKeyDown) finishEndKey(); }
        finally {
            endGeneration++; releasePending = false;
            for (int i = 0; i < captures.length; i++) captures[i].clear();
        }
    }
}
