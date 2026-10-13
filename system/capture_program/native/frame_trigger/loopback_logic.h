#ifndef FRAME_TRIGGER_LOOPBACK_LOGIC_H
#define FRAME_TRIGGER_LOOPBACK_LOGIC_H

#include <stdbool.h>
#include <stdint.h>

/*
 * Account for every kernel rising-edge event that was read.  Only the first
 * event inside the current pulse window is matched to that pulse; later events
 * remain visible in observed_count so the final count check fails closed.
 */
static inline void frame_trigger_record_loopback_edge(
    uint64_t timestamp_ns,
    uint64_t window_start_ns,
    uint64_t window_end_ns,
    bool *has_matched_timestamp,
    uint64_t *matched_timestamp_ns,
    uint64_t *observed_count,
    uint64_t *matched_count)
{
    *observed_count += 1;
    if (!*has_matched_timestamp &&
        timestamp_ns >= window_start_ns &&
        timestamp_ns <= window_end_ns) {
        *matched_timestamp_ns = timestamp_ns;
        *has_matched_timestamp = true;
        *matched_count += 1;
    }
}

#endif
