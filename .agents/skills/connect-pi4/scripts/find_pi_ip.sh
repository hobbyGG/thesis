#!/usr/bin/env bash
set -euo pipefail

readonly TARGET_MAC="88:a2:9e:d5:8f:89"

default_interface() {
  /sbin/route -n get default 2>/dev/null |
    /usr/bin/awk '/interface:/{print $2; exit}'
}

find_in_arp_cache() {
  /usr/sbin/arp -an 2>/dev/null |
    /usr/bin/awk -v mac="$TARGET_MAC" -v iface="$network_interface" '
      tolower($4) == mac && $6 == iface {
        gsub(/[()]/, "", $2)
        print $2
        exit
      }
    '
}

ssh_is_open() {
  /usr/bin/nc -z -w 1 "$1" 22 >/dev/null 2>&1
}

network_interface="$(default_interface)"
if [[ -z "$network_interface" ]]; then
  echo "No active default network interface found." >&2
  exit 1
fi

pi_ip="$(find_in_arp_cache)"
if [[ -n "$pi_ip" ]] && ssh_is_open "$pi_ip"; then
  printf '%s\n' "$pi_ip"
  exit 0
fi

local_ip="$(/usr/sbin/ipconfig getifaddr "$network_interface" 2>/dev/null || true)"
subnet_mask="$(/usr/sbin/ipconfig getoption "$network_interface" subnet_mask 2>/dev/null || true)"
if [[ -z "$local_ip" ]]; then
  echo "No IPv4 address found on $network_interface." >&2
  exit 1
fi
if [[ "$subnet_mask" != "255.255.255.0" ]]; then
  echo "Automatic discovery supports /24 LANs; $network_interface uses ${subnet_mask:-an unknown mask}." >&2
  exit 1
fi

subnet_prefix="${local_ip%.*}"
/usr/bin/jot 254 1 |
  /usr/bin/xargs -P 48 -n 1 /bin/sh -c \
    '/sbin/ping -c 1 -W 250 "$1.$2" >/dev/null 2>&1 || true' \
    _ "$subnet_prefix" || true

pi_ip="$(find_in_arp_cache)"
if [[ -z "$pi_ip" ]]; then
  echo "Raspberry Pi 4 with MAC $TARGET_MAC was not found on $network_interface." >&2
  exit 1
fi
if ! ssh_is_open "$pi_ip"; then
  echo "Found Raspberry Pi 4 at $pi_ip, but SSH port 22 is closed." >&2
  exit 1
fi

printf '%s\n' "$pi_ip"
