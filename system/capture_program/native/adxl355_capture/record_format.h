#ifndef ADXL355_RECORD_FORMAT_H
#define ADXL355_RECORD_FORMAT_H

#include <stddef.h>
#include <stdint.h>

#define ADXL355_FILE_MAGIC "ADXLRW01"
#define ADXL355_FORMAT_VERSION 1u
#define ADXL355_HEADER_BYTES 64u
#define ADXL355_RECORD_BYTES 48u

#define ADXL355_HEADER_FLAG_MOCK 0x0001u

struct adxl355_header_values {
    uint16_t flags;
    uint32_t odr_millihz;
    uint16_t range_g;
    uint64_t start_realtime_ns;
    uint64_t start_monotonic_ns;
    int64_t group_delay_ns;
};

struct adxl355_record_values {
    uint64_t sample_seq;
    uint64_t line_seqno;
    uint64_t drdy_monotonic_ns;
    uint64_t spi_complete_monotonic_ns;
    int32_t x_raw;
    int32_t y_raw;
    int32_t z_raw;
    int16_t temp_raw;
    uint8_t status;
    uint8_t fifo_entries;
};

void adxl355_encode_header(
    uint8_t out[ADXL355_HEADER_BYTES],
    const struct adxl355_header_values *values);

void adxl355_encode_record(
    uint8_t out[ADXL355_RECORD_BYTES],
    const struct adxl355_record_values *values);

#endif
