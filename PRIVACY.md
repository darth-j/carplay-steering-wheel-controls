<!-- SPDX-License-Identifier: GPL-3.0-only; Copyright (C) 2026 Skywalker (darth-j) -->

# Privacy and publication boundary

This project is a separately authored, portable logic library. It is deliberately published from an isolated directory rather than from the private development workspace or its history.

Included:

- Original logical state machines, adapter helpers, build/installer code and contracts.
- Small OEM context/removal fragments in source patches, with original ownership retained; no complete stock class or dependency JAR.
- Generic class/software fingerprints for reproducibility, not unit-specific startup data.
- Synthetic, in-memory tests with a virtual clock.
- A dependency-free local test command and a GPLv3 license.
- Explicitly requested generic model/platform/software-version compatibility information, without unique device identifiers.
- The public GitHub identity used for copyright/source attribution; no private email address is published.

Excluded:

- Device backups, firmware images, original libraries, complete decompiled manufacturer classes and proprietary SDK files.
- Vehicle identifiers, hardware serials, registration information, mileage and unit-specific configuration fingerprints.
- Credentials, keys, account identifiers, private email addresses, local usernames and absolute filesystem paths.
- Network addresses, hardware addresses, wireless network credentials and connection profiles.
- Phone numbers, caller names, contact lists, call identifiers, location information and navigation history.
- Real logs, screenshots, packet captures, crash dumps and private shared-conversation links.

The core has no network, filesystem, shell, telemetry or logging implementation. Only an adapter can connect its effects to a device. The clock and scheduler are supplied by the host; tests use no real endpoints.

Please contribute synthetic fixtures only. A successful secret scanner is not a guarantee: review every file and every commit before publishing. Git history and commit author metadata must also be reviewed; deleting a sensitive file in a later commit does not remove the earlier disclosure.
