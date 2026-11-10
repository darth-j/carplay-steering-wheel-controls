#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
# M.I.B Individual Script entry. Keep this file at SD root /mod/command.sh.
for sww_root in /net/mmx/fs/sda0 /net/mmx/fs/sdb0; do
    if [ -r "$sww_root/mod/steering-controls/manage.sh" ]; then
        on -f rcc /bin/sh "$sww_root/mod/steering-controls/manage.sh" "$sww_root"
        exit $?
    fi
done
echo "STOP: steering-controls package not found on SD1/SD2"
exit 1
