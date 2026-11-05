# Security and responsible reporting

Do not attach firmware dumps, credentials, private configuration, packet captures or identifiable device logs to public issues.

For ordinary logic defects, submit a minimal synthetic event sequence, the expected action and the observed action. Use logical keys and state enums; no caller, vehicle or account identity is needed.

This library does not expose a remote-control service and must not be used to justify enabling unrestricted remote access. Firmware flashing, wireless protocol changes and head-unit recovery are not provided.

If a report would expose sensitive data or demonstrate security-sensitive access, use a private channel supported by the hosting platform. Do not publish the sensitive material first.
