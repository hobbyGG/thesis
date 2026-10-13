#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "../loopback_logic.h"

int main(void)
{
    bool has_matched_timestamp = false;
    uint64_t matched_timestamp_ns = 0;
    uint64_t observed_count = 0;
    uint64_t matched_count = 0;

    frame_trigger_record_loopback_edge(
        110, 100, 200,
        &has_matched_timestamp,
        &matched_timestamp_ns,
        &observed_count,
        &matched_count);
    assert(has_matched_timestamp);
    assert(matched_timestamp_ns == 110);
    assert(observed_count == 1);
    assert(matched_count == 1);

    /* A second rising edge in the same pulse is counted but cannot replace it. */
    frame_trigger_record_loopback_edge(
        150, 100, 200,
        &has_matched_timestamp,
        &matched_timestamp_ns,
        &observed_count,
        &matched_count);
    assert(has_matched_timestamp);
    assert(matched_timestamp_ns == 110);
    assert(observed_count == 2);
    assert(matched_count == 1);

    /* A queued stale edge is also counted and cannot be matched to this pulse. */
    frame_trigger_record_loopback_edge(
        90, 100, 200,
        &has_matched_timestamp,
        &matched_timestamp_ns,
        &observed_count,
        &matched_count);
    assert(matched_timestamp_ns == 110);
    assert(observed_count == 3);
    assert(matched_count == 1);

    return 0;
}
