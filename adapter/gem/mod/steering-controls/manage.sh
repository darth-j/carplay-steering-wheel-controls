#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
export PATH=/proc/boot:/sbin:/bin:/usr/bin:/usr/sbin:/net/mmx/bin:/net/mmx/usr/bin:/net/mmx/usr/sbin:/net/mmx/sbin
export LD_LIBRARY_PATH=/net/mmx/mnt/app/root/lib-target:/net/mmx/mnt/eso/lib:/net/mmx/eso/lib:/net/mmx/mnt/app/usr/lib:/net/mmx/mnt/app/armle/lib:/net/mmx/mnt/app/armle/lib/dll:/net/mmx/mnt/app/armle/usr/lib
export IPL_CONFIG_DIR=/etc/eso/production
[ -x /usr/apps/mib2_ioc_flash ] || { echo "STOP: run on RCC"; exit 1; }
SD=$1
case "$SD" in /net/mmx/fs/sda0|/net/mmx/fs/sdb0) ;; *) echo "STOP: invalid SD root"; exit 1;; esac
DIR=$SD/mod/steering-controls
APP=/net/mmx/mnt/app
BASE=$APP/eso/hmi/lsd
LSD=$BASE/lsd.sh
ORIGINAL=$LSD.sww-original
ORIGINAL_SUM=$ORIGINAL.sha1
MANAGED_SUM=$LSD.sww-managed.sha1
JAR=$BASE/jars/SteeringWheelCarPlayControls.jar
JAR_SUM=$JAR.sww-managed.sha1
SOURCE=$DIR/SteeringWheelCarPlayControls.jar
PAYLOAD_SUM=$DIR/payload.sha1
DISABLED=$BASE/sww-controls.disabled
SED=$SD/apps/sbin/sed
PC=$SD/apps/sbin/pc
RAM=/net/rcc/dev/shmem/sww-controls-$$.prepared
NEXT=$LSD.sww-new-$$
NEXT_JAR=$JAR.sww-new-$$
PREVIOUS=$LSD.sww-previous
WRITABLE=0
sww_file_digest() {
    digest_line=$(/net/rcc/usr/bin/sha1sum "$1") || return 1
    set -- $digest_line
    [ "$#" -ge 1 ] && [ "${#1}" -eq 40 ] || return 1
    case "$1" in *[!a-fA-F0-9]*) return 1;; esac
    echo "$1"
}
sww_read_sum() {
    read sum_value < "$1" || return 1
    [ "${#sum_value}" -eq 40 ] || return 1
    case "$sum_value" in *[!a-fA-F0-9]*) return 1;; esac
    echo "$sum_value"
}
sww_write_sum() {
    echo "$2" > "$1.new" && mv -f "$1.new" "$1"
}
sww_cleanup() {
    rm -f "$RAM"
    if [ "$WRITABLE" -eq 1 ]; then
        rm -f "$NEXT" "$NEXT_JAR"
        mount -ur "$APP" >/dev/null 2>&1
    fi
}
trap sww_cleanup 0
sww_stop() { echo "STOP: $1"; exit 1; }
[ -x "$PC" ] && [ -x "$SED" ] || sww_stop "M.I.B pc/sed tools missing"
[ -r "$LSD" ] || sww_stop "startup file unavailable"
raw_train=$(on -f mmx "$PC" s:30:1966084) || sww_stop "train query failed"
raw_mu=$(on -f mmx "$PC" s:30:1966083) || sww_stop "MU query failed"
train=$(echo "$raw_train" | "$SED" 's/[^a-zA-Z0-9_-]//g') || exit 1
mu=$(echo "$raw_mu" | "$SED" 's/[^a-zA-Z0-9_-]//g') || exit 1
[ "$train" = MHI2_CN_AU57x_K1006_2 ] && [ "$mu" = 1005 ] || sww_stop "unsupported or unreadable firmware"
expected_rom=$(sww_read_sum "$DIR/rom.sha1") || sww_stop "local ROM checksum record missing"
actual_rom=$(sww_file_digest /net/mmx/ifs/lsd.jxe) || sww_stop "cannot verify running ROM"
[ "$actual_rom" = "$expected_rom" ] || sww_stop "running ROM differs from locally supplied backup"
echo "Detected supported reference firmware and matching local ROM"
read ACTION < "$DIR/action.txt" || sww_stop "action.txt missing"
case "$ACTION" in install-once|install-permanent|uninstall) ;; *) sww_stop "unknown action";; esac
CURRENT=$(sww_file_digest "$LSD") || sww_stop "cannot checksum startup"
HAVE_ORIGINAL=0
if [ -f "$ORIGINAL" ] || [ -f "$ORIGINAL_SUM" ]; then
    [ -f "$ORIGINAL" ] && [ -f "$ORIGINAL_SUM" ] || sww_stop "incomplete original backup"
    STOCK=$(sww_read_sum "$ORIGINAL_SUM") || sww_stop "invalid original checksum record"
    actual_original=$(sww_file_digest "$ORIGINAL") || exit 1
    [ "$actual_original" = "$STOCK" ] || sww_stop "original backup checksum mismatch"
    HAVE_ORIGINAL=1
    if [ "$CURRENT" != "$STOCK" ]; then
        managed=$(sww_read_sum "$MANAGED_SUM") || sww_stop "unknown current loader; do not overwrite"
        [ "$CURRENT" = "$managed" ] || sww_stop "startup changed outside this installer"
    fi
else
    STOCK=$CURRENT
    if grep -q -e 'Xbootclasspath/p:' -e 'MFW_CONTROLS_' -e 'SWW_CONTROLS_' -e 'carplay_hook' "$LSD"; then
        sww_stop "existing or foreign loader found; restore it using its own procedure first"
    fi
fi
if [ "$ACTION" = uninstall ]; then
    [ "$HAVE_ORIGINAL" -eq 1 ] || sww_stop "no verified original backup"
    if [ -f "$JAR" ]; then
        known_jar=$(sww_read_sum "$JAR_SUM") || sww_stop "unknown installed JAR"
        jar_now=$(sww_file_digest "$JAR") || exit 1
        [ "$jar_now" = "$known_jar" ] || sww_stop "installed JAR changed; refusing removal"
    fi
    cp -p "$ORIGINAL" "$RAM" && sh -n "$RAM" || sww_stop "cannot prepare recovery in RAM"
    mount -uw "$APP" || sww_stop "cannot mount app writable"
    WRITABLE=1
    cp -p "$RAM" "$NEXT" || sww_stop "cannot stage recovery"
    recovered=$(sww_file_digest "$NEXT") || exit 1
    [ "$recovered" = "$STOCK" ] || sww_stop "recovery staging mismatch"
    mv -f "$NEXT" "$LSD" || sww_stop "cannot publish recovery"
    restored=$(sww_file_digest "$LSD") || exit 1
    [ "$restored" = "$STOCK" ] || sww_stop "recovery verification failed; do not reboot"
    rm -f "$JAR" "$JAR_SUM" "$MANAGED_SUM" "$DISABLED"
    sync
    mount -ur "$APP" || sww_stop "original restored but read-only remount failed"
    WRITABLE=0
    echo "UNINSTALL VERIFIED. Original startup restored; backup retained. Restart only when safe."
    exit 0
fi
[ ! -f "$DISABLED" ] || sww_stop "bypass flag exists; inspect before re-enabling"
EXPECTED=$(sww_read_sum "$PAYLOAD_SUM") || sww_stop "payload checksum record missing"
source_hash=$(sww_file_digest "$SOURCE") || sww_stop "payload missing or checksum tool unavailable"
[ "$source_hash" = "$EXPECTED" ] || sww_stop "payload checksum mismatch"
JAR_PRESENT=0
if [ -f "$JAR" ]; then
    JAR_PRESENT=1
    old_payload=$(sww_read_sum "$JAR_SUM") || sww_stop "existing JAR not owned by this installer"
    jar_now=$(sww_file_digest "$JAR") || exit 1
    [ "$jar_now" = "$old_payload" ] && [ "$jar_now" = "$EXPECTED" ] || sww_stop "different payload installed; uninstall before upgrading"
fi
BASE_SOURCE=$LSD
[ "$HAVE_ORIGINAL" -eq 0 ] || BASE_SOURCE=$ORIGINAL
PATTERN='^on -p 12 \/ifs\/jre\/bin\/j9 [$]VMOPTIONS -Xbootclasspath:[$]BOOTCLASSPATH -jxe:[$]LSD_DIR\/lsd[.]jxe &$'
line=$($SED -n "/$PATTERN/=" "$BASE_SOURCE") || exit 1
case "$line" in ''|*[!0-9]*) sww_stop "expected exactly one reference Java launch line";; esac
BLOCK=$DIR/once.block
[ "$ACTION" != install-permanent ] || BLOCK=$DIR/permanent.block
[ -r "$BLOCK" ] || sww_stop "loader block missing"
$SED -e "${line}r $BLOCK" -e "${line}d" "$BASE_SOURCE" > "$RAM" || sww_stop "cannot prepare startup in RCC RAM"
sh -n "$RAM" || sww_stop "prepared startup syntax invalid"
grep -q SWW_CONTROLS_BEGIN "$RAM" && grep -q SWW_CONTROLS_END "$RAM" || sww_stop "prepared loader markers missing"
TARGET_SUM=$(sww_file_digest "$RAM") || exit 1
[ "$CURRENT" != "$TARGET_SUM" ] || { echo "ALREADY INSTALLED: no changes"; exit 0; }
mount -uw "$APP" || sww_stop "cannot mount app writable"
WRITABLE=1
latest=$(sww_file_digest "$LSD") || exit 1
[ "$latest" = "$CURRENT" ] || sww_stop "startup changed during preparation"
if [ "$HAVE_ORIGINAL" -eq 0 ]; then
    cp -p "$LSD" "$ORIGINAL.new" || sww_stop "cannot back up startup"
    saved=$(sww_file_digest "$ORIGINAL.new") || exit 1
    [ "$saved" = "$STOCK" ] || sww_stop "original backup copy mismatch"
    mv -f "$ORIGINAL.new" "$ORIGINAL" && sww_write_sum "$ORIGINAL_SUM" "$STOCK" || sww_stop "cannot save backup checksum"
fi
cp -p "$LSD" "$PREVIOUS" || sww_stop "cannot save current startup for rollback"
previous_sum=$(sww_file_digest "$PREVIOUS") || exit 1
[ "$previous_sum" = "$CURRENT" ] || sww_stop "rollback snapshot mismatch"
sww_rollback_install() {
    echo "VERIFY FAILED: attempting previous startup restore"
    recovered=bad
    if cp -p "$PREVIOUS" "$NEXT"; then
        recovered=$(sww_file_digest "$NEXT")
        if [ "$recovered" = "$CURRENT" ]; then mv -f "$NEXT" "$LSD"; fi
    fi
    restored=$(sww_file_digest "$LSD")
    if [ "$restored" = "$CURRENT" ]; then
        if [ "$JAR_PRESENT" -eq 0 ]; then
            jar_now=$(sww_file_digest "$JAR")
            if [ "$jar_now" = "$EXPECTED" ]; then rm -f "$JAR" "$JAR_SUM"; fi
        fi
        echo "RESTORE VERIFIED. Startup returned to previous state."
    else
        echo "RECOVERY FAILED: do not reboot; retain SD and use independent recovery"
    fi
    sync
    exit 1
}
cp -p "$SOURCE" "$NEXT_JAR" && chmod 644 "$NEXT_JAR" || sww_stop "cannot stage JAR; startup unchanged"
staged_jar=$(sww_file_digest "$NEXT_JAR") || exit 1
[ "$staged_jar" = "$EXPECTED" ] || sww_stop "staged JAR checksum mismatch; startup unchanged"
cp -p "$RAM" "$NEXT" && chmod 755 "$NEXT" || sww_stop "cannot stage startup; startup unchanged"
staged_startup=$(sww_file_digest "$NEXT") || exit 1
[ "$staged_startup" = "$TARGET_SUM" ] || sww_stop "staged startup checksum mismatch"
mv -f "$NEXT_JAR" "$JAR" || sww_stop "cannot publish JAR; startup unchanged"
mv -f "$NEXT" "$LSD" || sww_rollback_install
written=$(sww_file_digest "$LSD") || sww_rollback_install
[ "$written" = "$TARGET_SUM" ] || sww_rollback_install
sww_write_sum "$JAR_SUM" "$EXPECTED" && sww_write_sum "$MANAGED_SUM" "$TARGET_SUM" || sww_rollback_install
sync
mount -ur "$APP" || sww_stop "files verified but read-only remount failed; inspect before reboot"
WRITABLE=0
echo "INSTALL VERIFIED: $ACTION. No automatic restart requested."
echo "Original backup and checksum remain on this head unit; never publish them."
exit 0
