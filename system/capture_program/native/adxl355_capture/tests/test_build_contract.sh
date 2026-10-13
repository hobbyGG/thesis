#!/bin/sh
set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/adxl355-build-contract.XXXXXX")
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

if make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=0 \
    GPIO_UAPI_V2_AVAILABLE=0 \
    BUILD_DIR="$test_dir/fail" \
    all >"$test_dir/fail.stdout" 2>"$test_dir/fail.stderr"; then
    echo "Linux build without GPIO uAPI v2 headers unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'requires GPIO character-device uAPI v2 headers' "$test_dir/fail.stderr"
grep -q 'no kernel line sequence number' "$test_dir/fail.stderr"

make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=0 \
    GPIO_UAPI_V2_AVAILABLE=0 \
    BUILD_DIR="$test_dir/clean" \
    clean >/dev/null

make -C "$source_dir" \
    UNAME_S=Linux \
    GPIO_UAPI_V2_AVAILABLE=0 \
    MOCK_ONLY=1 \
    BUILD_DIR="$test_dir/mock" \
    all >/dev/null
"$test_dir/mock/adxl355_capture" --capabilities \
    | grep -q '"hardware_support":false'

make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=0 \
    GPIO_UAPI_V2_AVAILABLE=1 \
    EXTRA_CPPFLAGS="-Itests/linux_stubs" \
    BUILD_DIR="$test_dir/uapi-v2" \
    all >/dev/null
capabilities=$("$test_dir/uapi-v2/adxl355_capture" --capabilities)
printf '%s\n' "$capabilities" | grep -q '"hardware_support":true'
printf '%s\n' "$capabilities" | grep -q '"gpio_backend":"linux-gpio-uapi-v2"'
printf '%s\n' "$capabilities" | grep -q '"line_sequence_source":"kernel_line_seqno"'
printf '%s\n' "$capabilities" | grep -q '"line_sequence_certified":true'

echo "test_build_contract: PASS"
