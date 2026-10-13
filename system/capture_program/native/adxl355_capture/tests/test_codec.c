#include "adxl355_regs.h"
#include "record_format.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint16_t read_le16(const uint8_t *bytes)
{
    return (uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8);
}

static uint32_t read_le32(const uint8_t *bytes)
{
    return (uint32_t)bytes[0]
         | ((uint32_t)bytes[1] << 8)
         | ((uint32_t)bytes[2] << 16)
         | ((uint32_t)bytes[3] << 24);
}

static uint64_t read_le64(const uint8_t *bytes)
{
    uint64_t value = 0;
    size_t index;

    for (index = 0; index < 8; ++index) {
        value |= (uint64_t)bytes[index] << (8u * index);
    }
    return value;
}

static void encode_axis20(uint8_t out[3], int32_t value)
{
    uint32_t raw = value < 0
        ? (uint32_t)(value + 1048576)
        : (uint32_t)value;

    out[0] = (uint8_t)((raw >> 12) & 0xffu);
    out[1] = (uint8_t)((raw >> 4) & 0xffu);
    out[2] = (uint8_t)((raw & 0x0fu) << 4);
}

static void encode_fifo_axis(uint8_t out[3], int32_t value, bool x_marker)
{
    encode_axis20(out, value);
    if (x_marker) {
        out[2] |= ADXL355_FIFO_X_MARKER_MASK;
    }
}

static void test_header_encoding(void)
{
    uint8_t bytes[ADXL355_HEADER_BYTES];
    struct adxl355_header_values values = {
        .flags = ADXL355_HEADER_FLAG_MOCK,
        .odr_millihz = 1000000u,
        .range_g = 2u,
        .start_realtime_ns = UINT64_C(0x0102030405060708),
        .start_monotonic_ns = UINT64_C(0x1112131415161718),
        .group_delay_ns = INT64_C(2122232425262728)
    };

    adxl355_encode_header(bytes, &values);
    assert(memcmp(bytes, ADXL355_FILE_MAGIC, 8) == 0);
    assert(read_le16(bytes + 8) == ADXL355_FORMAT_VERSION);
    assert(read_le16(bytes + 10) == ADXL355_HEADER_BYTES);
    assert(read_le16(bytes + 12) == ADXL355_RECORD_BYTES);
    assert(read_le16(bytes + 14) == ADXL355_HEADER_FLAG_MOCK);
    assert(read_le32(bytes + 16) == 1000000u);
    assert(read_le16(bytes + 20) == 2u);
    assert(bytes[22] == 0u && bytes[23] == 0u);
    assert(read_le64(bytes + 24) == values.start_realtime_ns);
    assert(read_le64(bytes + 32) == values.start_monotonic_ns);
    assert(read_le64(bytes + 40) == (uint64_t)values.group_delay_ns);
    assert(read_le64(bytes + 48) == 0u);
    assert(read_le64(bytes + 56) == 0u);
}

static void test_record_encoding(void)
{
    uint8_t bytes[ADXL355_RECORD_BYTES];
    struct adxl355_record_values values = {
        .sample_seq = UINT64_C(7),
        .line_seqno = UINT64_C(9),
        .drdy_monotonic_ns = UINT64_C(123456789),
        .spi_complete_monotonic_ns = UINT64_C(123456999),
        .x_raw = -1,
        .y_raw = -524288,
        .z_raw = 524287,
        .temp_raw = -123,
        .status = 0xa5u,
        .fifo_entries = 96u
    };

    adxl355_encode_record(bytes, &values);
    assert(read_le64(bytes + 0) == values.sample_seq);
    assert(read_le64(bytes + 8) == values.line_seqno);
    assert(read_le64(bytes + 16) == values.drdy_monotonic_ns);
    assert(read_le64(bytes + 24) == values.spi_complete_monotonic_ns);
    assert((int32_t)read_le32(bytes + 32) == values.x_raw);
    assert((int32_t)read_le32(bytes + 36) == values.y_raw);
    assert((int32_t)read_le32(bytes + 40) == values.z_raw);
    assert((int16_t)read_le16(bytes + 44) == values.temp_raw);
    assert(bytes[46] == values.status);
    assert(bytes[47] == values.fifo_entries);
}

static void test_fifo_decoding_and_pairing_policy(void)
{
    uint8_t bytes[ADXL355_FIFO_XYZ_BYTES] = {0};
    struct adxl355_fifo_xyz values;

    encode_fifo_axis(bytes + 0, 524287, true);
    encode_fifo_axis(bytes + 3, -524288, false);
    encode_fifo_axis(bytes + 6, -1, false);
    assert(adxl355_decode_fifo_xyz(bytes, &values) == ADXL355_FIFO_DECODE_OK);
    assert(values.x_raw == 524287);
    assert(values.y_raw == -524288);
    assert(values.z_raw == -1);

    bytes[5] |= ADXL355_FIFO_EMPTY_MASK;
    assert(adxl355_decode_fifo_xyz(bytes, &values) == ADXL355_FIFO_DECODE_EMPTY);
    bytes[5] &= (uint8_t)~ADXL355_FIFO_EMPTY_MASK;

    bytes[2] &= (uint8_t)~ADXL355_FIFO_X_MARKER_MASK;
    assert(adxl355_decode_fifo_xyz(bytes, &values) == ADXL355_FIFO_DECODE_MARKER);
    bytes[2] |= ADXL355_FIFO_X_MARKER_MASK;

    bytes[8] |= ADXL355_FIFO_X_MARKER_MASK;
    assert(adxl355_decode_fifo_xyz(bytes, &values) == ADXL355_FIFO_DECODE_MARKER);
    bytes[8] &= (uint8_t)~ADXL355_FIFO_X_MARKER_MASK;

    bytes[8] |= 0x04u;
    assert(adxl355_decode_fifo_xyz(bytes, &values)
           == ADXL355_FIFO_DECODE_VIRTUAL_BITS);

    assert(adxl355_validate_pairing_snapshot(1, 0, 3) == ADXL355_PAIRING_OK);
    assert(adxl355_validate_pairing_snapshot(2, 0, 6)
           == ADXL355_PAIRING_GPIO_BACKLOG);
    assert(adxl355_validate_pairing_snapshot(1, ADXL355_STATUS_FIFO_OVR, 3)
           == ADXL355_PAIRING_FIFO_OVERRUN);
    assert(adxl355_validate_pairing_snapshot(1, 0, 0)
           == ADXL355_PAIRING_FIFO_DEPTH);
    assert(adxl355_validate_pairing_snapshot(1, 0, 6)
           == ADXL355_PAIRING_FIFO_DEPTH);
}

int main(void)
{
    test_header_encoding();
    test_record_encoding();
    test_fifo_decoding_and_pairing_policy();
    (void)puts("test_codec: PASS");
    return 0;
}
