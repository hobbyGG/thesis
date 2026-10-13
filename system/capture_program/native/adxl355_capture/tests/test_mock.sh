#!/bin/sh
set -eu

program=${1:?usage: test_mock.sh /path/to/adxl355_capture}
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/adxl355-capture-test.XXXXXX")
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

capabilities=$("$program" --capabilities)
printf '%s\n' "$capabilities" | grep -q '"schema_version":1'
printf '%s\n' "$capabilities" | grep -Eq '"hardware_support":(true|false)'
printf '%s\n' "$capabilities" | grep -q '"mock_support":true'
printf '%s\n' "$capabilities" | grep -Eq '"gpio_backend":"(linux-gpio-uapi-v2|unavailable)"'

output="$test_dir/samples.raw"
summary="$test_dir/summary.json"
ready="$test_dir/ready.json"

"$program" \
    --output "$output" \
    --summary "$summary" \
    --ready-file "$ready" \
    --spi-device /mock/spidev \
    --gpiochip /mock/gpiochip \
    --drdy-line 25 \
    --odr-hz 1000 \
    --range-g 2 \
    --spi-hz 5000000 \
    --mock \
    --max-samples 5

test "$(wc -c < "$output" | tr -d ' ')" = "304"
test "$(od -An -tx1 -N8 "$output" | tr -d ' \n')" = "4144584c52573031"
grep -q '"status":"ready"' "$ready"
grep -q '"timestamp_semantics":"drdy_edge"' "$summary"
grep -q '"status":"complete"' "$summary"
grep -q '"samples":5' "$summary"
grep -q '"samples_written":5' "$summary"
grep -q '"mock":true' "$summary"
grep -q '"gpio_backend":"synthetic_mock"' "$summary"
grep -q '"line_sequence_source":"synthetic_mock"' "$summary"
grep -q '"line_sequence_certified":false' "$summary"
grep -q '"group_delay_ns":0' "$summary"
grep -q '"group_delay_calibrated":false' "$summary"
grep -q '"group_delay_calibration_source":null' "$summary"
grep -q '"group_delay_ns":0' "$ready"
grep -q '"group_delay_calibrated":false' "$ready"
grep -q '"gpio_backlog_events":0' "$summary"
grep -q '"fifo_protocol_errors":0' "$summary"
grep -q '"fifo_xyz_mismatches":0' "$summary"
grep -q '"sample_source":"mock"' "$summary"
if find "$test_dir" -name '*.tmp.*' -print | grep -q .; then
    echo "atomic metadata temporary file was not cleaned up" >&2
    exit 1
fi

calibrated_output="$test_dir/calibrated.raw"
calibrated_summary="$test_dir/calibrated-summary.json"
calibrated_ready="$test_dir/calibrated-ready.json"
"$program" \
    --output "$calibrated_output" \
    --summary "$calibrated_summary" \
    --ready-file "$calibrated_ready" \
    --mock \
    --max-samples 1 \
    --group-delay-ns 1780000 \
    --group-delay-calibrated \
    --group-delay-source bench-scope-v1
test "$(od -An -tu8 -j40 -N8 "$calibrated_output" | tr -d ' ')" = "1780000"
grep -q '"group_delay_ns":1780000' "$calibrated_summary"
grep -q '"group_delay_calibrated":true' "$calibrated_summary"
grep -q '"group_delay_calibration_source":"bench-scope-v1"' "$calibrated_summary"
grep -q '"group_delay_ns":1780000' "$calibrated_ready"
grep -q '"group_delay_calibrated":true' "$calibrated_ready"
grep -q '"group_delay_calibration_source":"bench-scope-v1"' "$calibrated_ready"

invalid_summary="$test_dir/invalid-calibration-summary.json"
if "$program" \
    --output "$test_dir/invalid-calibration.raw" \
    --summary "$invalid_summary" \
    --ready-file "$test_dir/invalid-calibration-ready.json" \
    --mock \
    --group-delay-ns 1780000 >"$test_dir/invalid.stdout" 2>"$test_dir/invalid.stderr"; then
    echo "positive uncalibrated group delay unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'requires --group-delay-calibrated' "$test_dir/invalid.stderr"
grep -q '"status":"failed"' "$invalid_summary"

missing_source_summary="$test_dir/missing-source-summary.json"
if "$program" \
    --output "$test_dir/missing-source.raw" \
    --summary "$missing_source_summary" \
    --ready-file "$test_dir/missing-source-ready.json" \
    --mock \
    --group-delay-ns 1780000 \
    --group-delay-calibrated >"$test_dir/missing-source.stdout" 2>"$test_dir/missing-source.stderr"; then
    echo "calibrated group delay without source unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'requires a nonempty --group-delay-source' "$test_dir/missing-source.stderr"
grep -q '"status":"failed"' "$missing_source_summary"

interrupted_output="$test_dir/interrupted.raw"
interrupted_summary="$test_dir/interrupted-summary.json"
interrupted_ready="$test_dir/interrupted-ready.json"

"$program" \
    --output "$interrupted_output" \
    --summary "$interrupted_summary" \
    --ready-file "$interrupted_ready" \
    --mock \
    --max-samples 100000 >"$test_dir/interrupted.stdout" 2>"$test_dir/interrupted.stderr" &
capture_pid=$!

tries=0
while test ! -f "$interrupted_ready"; do
    if ! kill -0 "$capture_pid" 2>/dev/null; then
        echo "mock capture exited before becoming ready" >&2
        wait "$capture_pid" || true
        exit 1
    fi
    tries=$((tries + 1))
    if test "$tries" -gt 200; then
        echo "timed out waiting for ready file" >&2
        kill -TERM "$capture_pid" 2>/dev/null || true
        wait "$capture_pid" || true
        exit 1
    fi
    sleep 0.01
done

kill -TERM "$capture_pid"
if wait "$capture_pid"; then
    echo "interrupted finite capture unexpectedly succeeded" >&2
    exit 1
fi
grep -q '"status":"failed"' "$interrupted_summary"
grep -q '"stop_reason":"signal_before_target"' "$interrupted_summary"
grep -q 'terminated before --max-samples was reached' "$interrupted_summary"
test ! -e "$interrupted_ready"

missing_output="$test_dir/missing-hardware.raw"
missing_summary="$test_dir/missing-hardware-summary.json"
missing_ready="$test_dir/missing-hardware-ready.json"
if "$program" \
    --output "$missing_output" \
    --summary "$missing_summary" \
    --ready-file "$missing_ready" \
    --spi-device "$test_dir/does-not-exist-spidev" \
    --gpiochip "$test_dir/does-not-exist-gpiochip" \
    --max-samples 1 >"$test_dir/missing.stdout" 2>"$test_dir/missing.stderr"; then
    echo "capture with missing hardware unexpectedly succeeded" >&2
    exit 1
fi
grep -q '"status":"failed"' "$missing_summary"
grep -q '"samples":0' "$missing_summary"
test ! -e "$missing_ready"

echo "test_mock: PASS"
