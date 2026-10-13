#!/bin/sh
set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/frame-trigger-build-contract.XXXXXX")
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

mkdir -p "$test_dir/fail" "$test_dir/mock" "$test_dir/uapi-v2"

if make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=0 \
    GPIO_UAPI_V2_AVAILABLE=0 \
    TARGET="$test_dir/fail/frame_trigger" \
    all >"$test_dir/fail.stdout" 2>"$test_dir/fail.stderr"; then
    echo "Linux build without GPIO uAPI v2 headers unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'requires GPIO character-device uAPI v2 headers' "$test_dir/fail.stderr"
grep -q 'userspace timestamps are never substituted' "$test_dir/fail.stderr"

make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=1 \
    GPIO_UAPI_V2_AVAILABLE=0 \
    TARGET="$test_dir/mock/frame_trigger" \
    all >/dev/null
if "$test_dir/mock/frame_trigger" \
    --events "$test_dir/mock/events.csv" \
    --summary "$test_dir/mock/summary.json" \
    --gpiochip /dev/gpiochip0 \
    --output-line 18 \
    --loopback-line 24 \
    --frequency-hz 50 \
    --count 1 \
    --pulse-width-us 100 \
    --initial-delay-ms 1 \
    >"$test_dir/mock.stdout" 2>"$test_dir/mock.stderr"; then
    echo "mock-only binary unexpectedly accepted hardware mode" >&2
    exit 1
fi
grep -q 'GPIO character-device uAPI v2 is required' "$test_dir/mock.stderr"

make -C "$source_dir" \
    UNAME_S=Linux \
    MOCK_ONLY=0 \
    GPIO_UAPI_V2_AVAILABLE=1 \
    EXTRA_CPPFLAGS="-Itests/linux_stubs" \
    TARGET="$test_dir/uapi-v2/frame_trigger" \
    all >/dev/null

grep -q 'lacks character-device uAPI v2' "$source_dir/frame_trigger.c"
grep -q 'refusing userspace timestamp fallback' "$source_dir/frame_trigger.c"
if test "$(uname -s)" = "Linux"; then
    touch "$test_dir/uapi-v2/not-a-gpiochip"
    if "$test_dir/uapi-v2/frame_trigger" \
        --events "$test_dir/uapi-v2/events.csv" \
        --summary "$test_dir/uapi-v2/summary.json" \
        --gpiochip "$test_dir/uapi-v2/not-a-gpiochip" \
        --output-line 18 \
        --loopback-line 24 \
        --frequency-hz 50 \
        --count 1 \
        --pulse-width-us 100 \
        --initial-delay-ms 1 \
        >"$test_dir/uapi-v2.stdout" 2>"$test_dir/uapi-v2.stderr"; then
        echo "GPIO uAPI v2 binary unexpectedly accepted a non-GPIO device" >&2
        exit 1
    fi
    grep -q 'lacks character-device uAPI v2' "$test_dir/uapi-v2.stderr"
    grep -q 'refusing userspace timestamp fallback' "$test_dir/uapi-v2.stderr"
    grep -q '"status": "error"' "$test_dir/uapi-v2/summary.json"
fi

if grep -R -n -E '(^|[^[:alnum:]_])gpiod_|#include[[:space:]]*<gpiod[.]h>' \
    "$source_dir/frame_trigger.c" >"$test_dir/gpiod-symbols"; then
    cat "$test_dir/gpiod-symbols" >&2
    echo "frame trigger still references libgpiod" >&2
    exit 1
fi

echo "test_build_contract: PASS"
