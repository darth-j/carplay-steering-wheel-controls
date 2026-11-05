package carplay.controls;

/** A connection-scoped guard; observing state never sends media commands. */
public final class PlaybackPolicy {
    public static final int PLAYING = 1;
    public static final int PAUSED = 2;
    public static final int SEEKING_FORWARD = 3;
    public static final int SEEKING_BACKWARD = 4;
    private boolean protecting;

    public synchronized void beginConnection() { protecting = true; }
    public synchronized void endConnection() { protecting = false; }
    public synchronized void observe(int state, boolean valid) {
        if (valid && isPlaying(state)) protecting = false;
    }
    public synchronized void userTransportRequested() { protecting = false; }
    public synchronized boolean allows(int button) {
        return !protecting || (button != 19 && button != 15);
    }
    public static boolean isPlaying(int state) {
        return state == PLAYING || state == SEEKING_FORWARD || state == SEEKING_BACKWARD;
    }

    /** Apply at the transport boundary; never forward an orphaned release. */
    public final class ButtonGate {
        private boolean dropPlay;
        private boolean dropToggle;
        public synchronized void reset() { dropPlay = false; dropToggle = false; }
        public synchronized boolean forward(int button, boolean released) {
            if (button != 19 && button != 15) return true;
            if (!released) {
                boolean drop = !allows(button);
                if (button == 19) dropPlay = drop; else dropToggle = drop;
                return !drop;
            }
            boolean drop = button == 19 ? dropPlay : dropToggle;
            if (button == 19) dropPlay = false; else dropToggle = false;
            return !drop;
        }
    }
}
