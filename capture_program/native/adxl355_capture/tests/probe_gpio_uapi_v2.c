#include <linux/gpio.h>

#ifndef GPIO_V2_GET_LINE_IOCTL
#error "Linux GPIO character-device uAPI v2 is unavailable"
#endif

int main(void)
{
    struct gpio_v2_line_request request;
    struct gpio_v2_line_event event;

    request.config.flags = GPIO_V2_LINE_FLAG_INPUT
                         | GPIO_V2_LINE_FLAG_EDGE_RISING;
    event.line_seqno = 1u;
    return (request.config.flags == 0u || event.line_seqno == 0u) ? 1 : 0;
}
