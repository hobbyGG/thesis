#ifndef TEST_LINUX_GPIO_H
#define TEST_LINUX_GPIO_H

#include <stdint.h>
#include <sys/ioctl.h>

#define GPIO_MAX_NAME_SIZE 32
#define GPIO_V2_LINES_MAX 64
#define GPIO_V2_LINE_NUM_ATTRS_MAX 10

#define GPIO_V2_LINE_FLAG_INPUT (UINT64_C(1) << 2)
#define GPIO_V2_LINE_FLAG_OUTPUT (UINT64_C(1) << 3)
#define GPIO_V2_LINE_FLAG_EDGE_RISING (UINT64_C(1) << 4)

#define GPIO_V2_LINE_EVENT_RISING_EDGE 1U

struct gpio_v2_line_attribute {
    uint32_t id;
    uint32_t padding;
    uint64_t value;
};

struct gpio_v2_line_config_attribute {
    struct gpio_v2_line_attribute attr;
    uint64_t mask;
};

struct gpio_v2_line_config {
    uint64_t flags;
    uint32_t num_attrs;
    uint32_t padding[5];
    struct gpio_v2_line_config_attribute attrs[GPIO_V2_LINE_NUM_ATTRS_MAX];
};

struct gpio_v2_line_request {
    uint32_t offsets[GPIO_V2_LINES_MAX];
    char consumer[GPIO_MAX_NAME_SIZE];
    struct gpio_v2_line_config config;
    uint32_t num_lines;
    uint32_t event_buffer_size;
    uint32_t padding[5];
    int32_t fd;
};

struct gpio_v2_line_event {
    uint64_t timestamp_ns;
    uint32_t id;
    uint32_t offset;
    uint32_t seqno;
    uint32_t line_seqno;
    uint32_t padding[6];
};

struct gpio_v2_line_values {
    uint64_t bits;
    uint64_t mask;
};

#define GPIO_V2_GET_LINE_IOCTL _IOWR(0xb4, 0x07, struct gpio_v2_line_request)
#define GPIO_V2_LINE_SET_VALUES_IOCTL _IOWR(0xb4, 0x0f, struct gpio_v2_line_values)

#endif
