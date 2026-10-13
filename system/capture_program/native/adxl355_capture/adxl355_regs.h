#ifndef ADXL355_REGS_H
#define ADXL355_REGS_H

#include <stddef.h>
#include <stdint.h>

#define ADXL355_REG_DEVID_AD 0x00u
#define ADXL355_REG_DEVID_MST 0x01u
#define ADXL355_REG_PARTID 0x02u
#define ADXL355_REG_REVID 0x03u
#define ADXL355_REG_STATUS 0x04u
#define ADXL355_REG_FIFO_ENTRIES 0x05u
#define ADXL355_REG_TEMP2 0x06u
#define ADXL355_REG_TEMP1 0x07u
#define ADXL355_REG_FIFO_DATA 0x11u
#define ADXL355_REG_FILTER 0x28u
#define ADXL355_REG_SYNC 0x2bu
#define ADXL355_REG_RANGE 0x2cu
#define ADXL355_REG_POWER_CTL 0x2du
#define ADXL355_REG_RESET 0x2fu
#define ADXL355_REG_SHADOW_BASE 0x50u

#define ADXL355_DEVID_AD_VALUE 0xadu
#define ADXL355_DEVID_MST_VALUE 0x1du
#define ADXL355_PARTID_VALUE 0xedu
#define ADXL355_RESET_CODE 0x52u

#define ADXL355_STATUS_DATA_RDY 0x01u
#define ADXL355_STATUS_FIFO_FULL 0x02u
#define ADXL355_STATUS_FIFO_OVR 0x04u
#define ADXL355_STATUS_NVM_BUSY 0x10u
#define ADXL355_FIFO_ENTRIES_MASK 0x7fu
#define ADXL355_FIFO_X_MARKER_MASK 0x01u
#define ADXL355_FIFO_EMPTY_MASK 0x02u
#define ADXL355_FIFO_VIRTUAL_BITS_MASK 0x0cu
#define ADXL355_FIFO_XYZ_BYTES 9u
#define ADXL355_SHADOW_BYTES 5u

#define ADXL355_RANGE_INT_POL_HIGH 0x40u
#define ADXL355_POWER_CTL_STANDBY 0x01u
#define ADXL355_SYNC_INTERNAL 0x00u

enum adxl355_fifo_decode_result {
    ADXL355_FIFO_DECODE_OK = 0,
    ADXL355_FIFO_DECODE_EMPTY = 1,
    ADXL355_FIFO_DECODE_MARKER = 2,
    ADXL355_FIFO_DECODE_VIRTUAL_BITS = 3
};

struct adxl355_fifo_xyz {
    int32_t x_raw;
    int32_t y_raw;
    int32_t z_raw;
    uint8_t command_response;
    uint8_t raw_bytes[ADXL355_FIFO_XYZ_BYTES];
};

enum adxl355_pairing_result {
    ADXL355_PAIRING_OK = 0,
    ADXL355_PAIRING_GPIO_BACKLOG = 1,
    ADXL355_PAIRING_FIFO_OVERRUN = 2,
    ADXL355_PAIRING_FIFO_DEPTH = 3
};

static inline int32_t adxl355_decode_axis20(const uint8_t bytes[3])
{
    uint32_t raw = ((uint32_t)bytes[0] << 12)
                 | ((uint32_t)bytes[1] << 4)
                 | ((uint32_t)bytes[2] >> 4);

    if ((raw & 0x80000u) != 0u) {
        return (int32_t)raw - 1048576;
    }
    return (int32_t)raw;
}

static inline enum adxl355_fifo_decode_result adxl355_decode_fifo_xyz(
    const uint8_t data[ADXL355_FIFO_XYZ_BYTES],
    struct adxl355_fifo_xyz *values)
{
    size_t axis;

    for (axis = 0; axis < ADXL355_FIFO_XYZ_BYTES; ++axis) {
        values->raw_bytes[axis] = data[axis];
    }
    for (axis = 0; axis < 3; ++axis) {
        uint8_t low = data[axis * 3u + 2u];

        if ((low & ADXL355_FIFO_EMPTY_MASK) != 0u) {
            return ADXL355_FIFO_DECODE_EMPTY;
        }
        if ((low & ADXL355_FIFO_VIRTUAL_BITS_MASK) != 0u) {
            return ADXL355_FIFO_DECODE_VIRTUAL_BITS;
        }
        if (axis == 0u) {
            if ((low & ADXL355_FIFO_X_MARKER_MASK) == 0u) {
                return ADXL355_FIFO_DECODE_MARKER;
            }
        } else if ((low & ADXL355_FIFO_X_MARKER_MASK) != 0u) {
            return ADXL355_FIFO_DECODE_MARKER;
        }
    }
    values->x_raw = adxl355_decode_axis20(data + 0);
    values->y_raw = adxl355_decode_axis20(data + 3);
    values->z_raw = adxl355_decode_axis20(data + 6);
    return ADXL355_FIFO_DECODE_OK;
}

static inline enum adxl355_pairing_result adxl355_validate_pairing_snapshot(
    size_t gpio_event_count,
    uint8_t status,
    uint8_t fifo_entries)
{
    if (gpio_event_count != 1u) {
        return ADXL355_PAIRING_GPIO_BACKLOG;
    }
    if ((status & ADXL355_STATUS_FIFO_OVR) != 0u) {
        return ADXL355_PAIRING_FIFO_OVERRUN;
    }
    if ((fifo_entries & ADXL355_FIFO_ENTRIES_MASK) != 3u) {
        return ADXL355_PAIRING_FIFO_DEPTH;
    }
    return ADXL355_PAIRING_OK;
}

#endif
