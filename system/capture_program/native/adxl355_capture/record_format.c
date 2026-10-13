#include "record_format.h"

#include <string.h>

static void put_le16(uint8_t *out, uint16_t value)
{
    out[0] = (uint8_t)(value & 0xffu);
    out[1] = (uint8_t)((value >> 8) & 0xffu);
}

static void put_le32(uint8_t *out, uint32_t value)
{
    out[0] = (uint8_t)(value & 0xffu);
    out[1] = (uint8_t)((value >> 8) & 0xffu);
    out[2] = (uint8_t)((value >> 16) & 0xffu);
    out[3] = (uint8_t)((value >> 24) & 0xffu);
}

static void put_le64(uint8_t *out, uint64_t value)
{
    size_t index;

    for (index = 0; index < 8; ++index) {
        out[index] = (uint8_t)((value >> (8u * index)) & 0xffu);
    }
}

void adxl355_encode_header(
    uint8_t out[ADXL355_HEADER_BYTES],
    const struct adxl355_header_values *values)
{
    memset(out, 0, ADXL355_HEADER_BYTES);
    memcpy(out, ADXL355_FILE_MAGIC, 8);
    put_le16(out + 8, ADXL355_FORMAT_VERSION);
    put_le16(out + 10, ADXL355_HEADER_BYTES);
    put_le16(out + 12, ADXL355_RECORD_BYTES);
    put_le16(out + 14, values->flags);
    put_le32(out + 16, values->odr_millihz);
    put_le16(out + 20, values->range_g);
    put_le64(out + 24, values->start_realtime_ns);
    put_le64(out + 32, values->start_monotonic_ns);
    put_le64(out + 40, (uint64_t)values->group_delay_ns);
}

void adxl355_encode_record(
    uint8_t out[ADXL355_RECORD_BYTES],
    const struct adxl355_record_values *values)
{
    memset(out, 0, ADXL355_RECORD_BYTES);
    put_le64(out + 0, values->sample_seq);
    put_le64(out + 8, values->line_seqno);
    put_le64(out + 16, values->drdy_monotonic_ns);
    put_le64(out + 24, values->spi_complete_monotonic_ns);
    put_le32(out + 32, (uint32_t)values->x_raw);
    put_le32(out + 36, (uint32_t)values->y_raw);
    put_le32(out + 40, (uint32_t)values->z_raw);
    put_le16(out + 44, (uint16_t)values->temp_raw);
    out[46] = values->status;
    out[47] = values->fifo_entries;
}
