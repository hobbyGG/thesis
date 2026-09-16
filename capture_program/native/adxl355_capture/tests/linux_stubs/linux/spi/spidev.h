#ifndef TEST_LINUX_SPI_SPIDEV_H
#define TEST_LINUX_SPI_SPIDEV_H

#include <stdint.h>

#define SPI_MODE_0 0u
#define SPI_IOC_WR_MODE 0ul
#define SPI_IOC_WR_BITS_PER_WORD 0ul
#define SPI_IOC_WR_MAX_SPEED_HZ 0ul
#define SPI_IOC_MESSAGE(count) (0ul + (unsigned long)(count))

struct spi_ioc_transfer {
    uint64_t tx_buf;
    uint64_t rx_buf;
    uint32_t len;
    uint32_t speed_hz;
    uint16_t delay_usecs;
    uint8_t bits_per_word;
    uint8_t cs_change;
    uint8_t tx_nbits;
    uint8_t rx_nbits;
    uint8_t word_delay_usecs;
    uint8_t pad;
};

#endif
