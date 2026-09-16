#!/usr/bin/env bash
set -euo pipefail

readonly TARGET_MAC="88:a2:9e:d5:8f:89"
readonly SSH_USER="umep"

script_dir="$(
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  pwd
)"
pi_ip="$("$script_dir/find_pi_ip.sh")"

printf 'Found Pi 4: %s (%s)\n' "$pi_ip" "$TARGET_MAC"
printf 'Connecting as %s...\n' "$SSH_USER"
exec /usr/bin/ssh -tt \
  -o ConnectTimeout=5 \
  -o StrictHostKeyChecking=accept-new \
  -o ServerAliveInterval=30 \
  "$SSH_USER@$pi_ip"
