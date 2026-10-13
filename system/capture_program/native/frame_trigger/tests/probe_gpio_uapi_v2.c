#include <linux/gpio.h>

#ifndef GPIO_V2_GET_LINE_IOCTL
#error "Linux GPIO character-device uAPI v2 is unavailable"
#endif

#ifndef GPIO_V2_LINE_SET_VALUES_IOCTL
#error "Linux GPIO character-device uAPI v2 output control is unavailable"
#endif

int main(void)
{
    struct gpio_v2_line_request request;
    struct gpio_v2_line_event event;
    struct gpio_v2_line_values values;

    request.config.flags = GPIO_V2_LINE_FLAG_OUTPUT;
    request.config.flags = GPIO_V2_LINE_FLAG_INPUT
                         | GPIO_V2_LINE_FLAG_EDGE_RISING;
    event.timestamp_ns = 1U;
    values.mask = 1U;
    values.bits = 0U;
    return (request.config.flags == 0U || event.timestamp_ns == 0U ||
            values.mask == 0U) ? 1 : 0;
}
