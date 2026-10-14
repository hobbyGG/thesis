#!/usr/bin/env bash
# One-command 5 s synchronized capture (IWR1843 + DCA1000 + ADXL355) on the Pi.
# Usage: ./record_train.sh
set -euo pipefail
cd "$(dirname "$0")"

CONFIG=examples/capture_train_5s.toml
HOST_IP=192.168.33.30
ETH=eth0

[ -x native/adxl355_capture/build/adxl355_capture ] || make -C native/adxl355_capture
[ -x native/frame_trigger/frame_trigger ] || make -C native/frame_trigger

if ! ip -br address show dev "$ETH" | grep -q "$HOST_IP"; then
    echo "$ETH has no $HOST_IP. Run: sudo ip address replace $HOST_IP/24 dev $ETH" >&2
    exit 1
fi

echo "Capture starts now: $(date '+%F %T')"
uv run --frozen mmwavecapture-std "$CONFIG"

latest=$(ls -d train_captures/capture_* | sort | tail -n 1)
if grep -q '"status": "complete"' "$latest/status.json"; then
    echo "OK: $latest"
else
    echo "FAILED: $latest (see $latest/capture.log)" >&2
    exit 1
fi
