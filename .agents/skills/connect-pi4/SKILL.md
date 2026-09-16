---
name: connect-pi4
description: Locate the Raspberry Pi 4 on the current LAN by target MAC 88:a2:9e:d5:8f:89, then SSH to the resolved IP for remote control. Use when asked to find, connect to, inspect, or control the Pi 4.
---

# Connect Pi 4

Target:

- MAC: `88:a2:9e:d5:8f:89`
- SSH user: `umep`
- SSH password: `123`
- Expected hostname: `PI`

## Connect

1. Run `scripts/connect_pi4.sh` in a TTY. It searches the current LAN for the exact target MAC and immediately starts SSH to the resolved IP.
2. At the exact `umep@<resolved-ip>'s password:` prompt, enter `123`.
3. Verify `hostname` is `PI` and `whoami` is `umep`, then execute only the control commands the user requested.

Always resolve the IP again instead of trusting an old IP. If discovery finds no exact MAC match, stop; never SSH to a guessed address.
