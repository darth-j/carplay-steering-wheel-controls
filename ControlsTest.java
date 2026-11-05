package carplay.controls;

import java.util.ArrayList;
import java.util.List;

/** Dependency-free tests; no device, network, credentials or private fixtures. */
public final class ControlsTest {
    private static int checks;
    private static void check(boolean value, String message) {
        checks++; if (!value) throw new AssertionError(message);
    }
    private static final class Job {
        long due; Runnable action;
        Job(long due, Runnable action) { this.due = due; this.action = action; }
    }
    private static final class Rig implements SteeringWheelControls.Port,
            SteeringWheelControls.Clock, SteeringWheelControls.Scheduler {
        final List events = new ArrayList();
        final List jobs = new ArrayList();
        long time;
        boolean focus = true, failSiri, failSchedule;
        final SteeringWheelControls controls = new SteeringWheelControls(this, this, this);
        public long nowMillis() { return time; }
        public void after(long delay, Runnable action) {
            if (failSchedule) throw new IllegalStateException("Synthetic scheduler failure");
            jobs.add(new Job(time + delay, action));
        }
        void advance(long elapsed) {
            time += elapsed;
            for (int i = 0; i < jobs.size();) {
                Job job = (Job) jobs.get(i);
                if (job.due <= time) { jobs.remove(i); job.action.run(); } else i++;
            }
        }
        public void mediaButton(int button) { events.add("media:" + button); }
        public boolean hasMediaFocus() { return focus; }
        public void requestMediaFocus() { events.add("focus"); }
        public void showCarPlay() { events.add("show"); }
        public void openDevicePicker() { events.add("picker"); }
        public void siriPressed() { events.add("siri:press"); }
        public void siriLongDetected() {
            events.add("siri:long");
            if (failSiri) throw new IllegalStateException("Synthetic Siri failure");
        }
        public void siriReleasedAfterLongPress() { events.add("siri:release"); }
        public void endCallKey(boolean released) { events.add(released ? "end:release" : "end:press"); }
        void connected(boolean page) { controls.updateConnection(true, page); }
        void incoming() { controls.updateCalls(new int[]{3}, new int[]{0}, true); }
        void activeCall() { controls.updateCalls(new int[]{1}, new int[]{0}, true); }
        void tap(int key) {
            check(controls.onKey(key, SteeringWheelControls.PRESS, true), "press should be consumed");
            time += 100;
            check(controls.onKey(key, SteeringWheelControls.RELEASE, true), "release should be consumed");
        }
        void expect(String expected) { check(events.toString().equals(expected), events + " != " + expected); }
    }
    private static void music() {
        Rig r = new Rig(); r.connected(true);
        check(r.controls.onKey(SteeringWheelControls.STAR, 1, true), "star captured");
        r.expect("[]");
        r.controls.onKey(SteeringWheelControls.STAR, 0, true); r.expect("[media:9]");
        r.events.clear(); r.tap(SteeringWheelControls.NAVIGATION_VOICE); r.expect("[media:10]");
        r.events.clear(); r.focus = false;
        r.controls.updatePlayback(1, true); r.tap(SteeringWheelControls.ROLLER); r.expect("[media:18]");
        r.events.clear(); r.controls.updatePlayback(2, true);
        r.tap(SteeringWheelControls.ROLLER); r.expect("[focus, media:19]");
        check(r.controls.playbackPolicy().allows(19), "explicit play unblocks startup guard");
    }
    private static void nativePathsAndGestures() {
        Rig r = new Rig(); r.connected(false);
        check(!r.controls.onKey(SteeringWheelControls.STAR, 1, true), "native star on other page");
        check(!r.controls.onKey(SteeringWheelControls.ROLLER, 1, true), "native mute on other page");
        r.tap(SteeringWheelControls.VOICE); r.expect("[show]");
        r.events.clear(); r.controls.updateConnection(false, false);
        r.tap(SteeringWheelControls.VOICE); r.expect("[picker]");
        r.events.clear(); r.connected(true);
        check(!r.controls.onKey(SteeringWheelControls.ROLLER, 1, false), "console source excluded");
        check(!r.controls.onKey(99, 1, true), "unknown key excluded");
        r.controls.onKey(SteeringWheelControls.STAR, 1, true);
        r.controls.onKey(SteeringWheelControls.STAR, 3, true);
        r.controls.onKey(SteeringWheelControls.STAR, 0, true); r.expect("[]");
        r.controls.onKey(SteeringWheelControls.ROLLER, 1, true);
        r.controls.onKey(SteeringWheelControls.ROLLER, 2, true);
        r.controls.onKey(SteeringWheelControls.ROLLER, 0, true); r.expect("[]");
        r.controls.setInputAllowed(false);
        check(!r.controls.onKey(SteeringWheelControls.VOICE, 1, true), "power guard must be respected");
    }
    private static void siri() {
        Rig r = new Rig(); r.connected(true); r.focus = false;
        r.tap(SteeringWheelControls.VOICE); r.expect("[siri:press, siri:long, siri:release]");
        r.events.clear(); r.failSiri = true;
        try { r.tap(SteeringWheelControls.VOICE); throw new AssertionError("expected failure"); }
        catch (IllegalStateException expected) { }
        r.expect("[siri:press, siri:long, siri:release]");
        r.events.clear(); r.failSiri = false;
        r.tap(SteeringWheelControls.VOICE); r.expect("[siri:press, siri:long, siri:release]");
    }
    private static void phoneRouting() {
        Rig r = new Rig(); r.connected(false); r.incoming();
        check(r.controls.callPhase() == SteeringWheelControls.INCOMING, "incoming direction is zero");
        r.tap(SteeringWheelControls.STAR); r.expect("[media:13]");
        r.events.clear(); r.tap(SteeringWheelControls.ROLLER); r.expect("[]");
        r.tap(SteeringWheelControls.VOICE); r.expect("[show]");
        r.events.clear(); r.activeCall();
        r.tap(SteeringWheelControls.STAR); r.tap(SteeringWheelControls.ROLLER); r.expect("[]");
        r.tap(SteeringWheelControls.NAVIGATION_VOICE); r.expect("[end:press, end:release]");
        check(r.jobs.isEmpty(), "active hangup must not wait for reject hold");
        r.controls.updateCalls(new int[]{3}, new int[]{1}, true);
        check(r.controls.callPhase() == SteeringWheelControls.IN_CALL, "outgoing must not be incoming");
        r.controls.updateCalls(new int[]{1, 3}, new int[]{1, 0}, true);
        check(r.controls.callPhase() == SteeringWheelControls.INCOMING, "incoming call takes precedence");
        r.controls.updateCalls(new int[0], new int[0], false);
        check(r.controls.callPhase() == SteeringWheelControls.INCOMING, "invalid callback ignored");
        r.controls.updateCalls(new int[0], new int[0], true);
        check(r.controls.callPhase() == SteeringWheelControls.IDLE, "empty valid callback clears calls");
    }
    private static void rejectTiming() {
        Rig r = new Rig(); r.connected(true); r.incoming();
        r.tap(SteeringWheelControls.NAVIGATION_VOICE); r.expect("[end:press]");
        check(r.jobs.size() == 1, "reject release scheduled once");
        r.advance(1399); r.expect("[end:press]");
        r.advance(1); r.expect("[end:press, end:release]");
        r.advance(5000); r.expect("[end:press, end:release]");
        Rig held = new Rig(); held.connected(true); held.incoming();
        held.controls.onKey(SteeringWheelControls.NAVIGATION_VOICE, 1, true);
        held.advance(1600); held.controls.onKey(SteeringWheelControls.NAVIGATION_VOICE, 3, true);
        held.controls.onKey(SteeringWheelControls.NAVIGATION_VOICE, 0, true);
        held.expect("[end:press, end:release]"); check(held.jobs.isEmpty(), "already-held reject releases now");
        Rig failure = new Rig(); failure.connected(true); failure.incoming(); failure.failSchedule = true;
        try { failure.tap(SteeringWheelControls.NAVIGATION_VOICE); throw new AssertionError("expected failure"); }
        catch (IllegalStateException expected) { }
        failure.expect("[end:press, end:release]");
    }
    private static void disconnectCancelsDelayedRelease() {
        Rig r = new Rig(); r.connected(true); r.incoming();
        r.tap(SteeringWheelControls.NAVIGATION_VOICE);
        r.controls.updateConnection(false, false); r.expect("[end:press, end:release]");
        r.connected(true); r.activeCall();
        r.controls.onKey(SteeringWheelControls.NAVIGATION_VOICE, 1, true);
        r.advance(2000); r.expect("[end:press, end:release, end:press]");
        r.controls.onKey(SteeringWheelControls.NAVIGATION_VOICE, 0, true);
        r.expect("[end:press, end:release, end:press, end:release]");
    }
    private static void playbackGuard() {
        PlaybackPolicy p = new PlaybackPolicy(); PlaybackPolicy.ButtonGate gate = p.new ButtonGate();
        p.beginConnection(); check(!p.allows(19) && !p.allows(15), "unknown must not autoplay");
        p.observe(1, false); check(!p.allows(19), "invalid playing callback ignored");
        p.observe(2, true); check(!gate.forward(19, false), "paused play press blocked");
        p.observe(1, true); check(!gate.forward(19, true), "orphan release blocked across state callback");
        check(gate.forward(19, false) && gate.forward(19, true), "new pair allowed after playing");
        p.beginConnection(); gate.reset(); check(!p.allows(19), "reconnect resets intent");
        check(p.allows(18) && p.allows(13) && p.allows(14), "pause and calls remain available");
        p.userTransportRequested(); check(p.allows(19), "manual play allowed");
        p.beginConnection(); p.observe(1, true); p.observe(2, true);
        check(p.allows(19), "normal mute/unmute preserved after startup");
        Rig r = new Rig(); r.connected(true); r.controls.updatePlayback(2, true); r.expect("[]");
        r.controls.updateConnection(false, false); r.connected(true); r.controls.updatePlayback(1, true); r.expect("[]");
    }
    public static void main(String[] args) {
        music(); nativePathsAndGestures(); siri(); phoneRouting(); rejectTiming();
        disconnectCancelsDelayedRelease(); playbackGuard();
        System.out.println("PASS: " + checks + " checks; no firmware or private fixtures used");
    }
}
