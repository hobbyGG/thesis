#define _POSIX_C_SOURCE 200809L

#include "adxl355_regs.h"
#include "record_format.h"

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <inttypes.h>
#include <limits.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#ifndef ADXL355_ENABLE_LINUX_HW
#define ADXL355_ENABLE_LINUX_HW 0
#endif

#if ADXL355_ENABLE_LINUX_HW
#include <linux/gpio.h>
#include <linux/spi/spidev.h>
#include <poll.h>
#include <sys/ioctl.h>
#endif

#define DEFAULT_SPI_DEVICE "/dev/spidev0.0"
#define DEFAULT_GPIOCHIP "/dev/gpiochip0"
#define DEFAULT_DRDY_LINE 25u
#define DEFAULT_ODR_HZ 1000u
#define DEFAULT_RANGE_G 2u
#define DEFAULT_SPI_HZ 5000000u
#define MAX_SPI_HZ 10000000u
#define GPIO_EVENT_BATCH_SIZE 64u

#if ADXL355_ENABLE_LINUX_HW
#define GPIO_BACKEND_NAME "linux-gpio-uapi-v2"
#define GPIO_LINE_SEQUENCE_SOURCE "kernel_line_seqno"
#else
#define GPIO_BACKEND_NAME "unavailable"
#define GPIO_LINE_SEQUENCE_SOURCE "unavailable"
#endif

struct capture_config {
    const char *output_path;
    const char *summary_path;
    const char *ready_path;
    const char *spi_device;
    const char *gpiochip;
    uint32_t drdy_line;
    uint32_t odr_hz;
    uint32_t range_g;
    uint32_t spi_hz;
    uint64_t max_samples;
    int64_t group_delay_ns;
    const char *group_delay_calibration_source;
    bool group_delay_calibrated;
    bool mock;
    bool capabilities;
};

struct capture_stats {
    uint64_t samples_written;
    uint64_t first_drdy_ns;
    uint64_t last_drdy_ns;
    uint64_t line_seq_gaps;
    uint64_t fifo_overruns;
    uint64_t gpio_backlog_events;
    uint64_t fifo_protocol_errors;
    uint64_t fifo_xyz_mismatches;
    uint64_t fifo_xyz_sets_drained;
    uint8_t max_fifo_entries;
    uint64_t start_realtime_ns;
    uint64_t start_monotonic_ns;
    int64_t group_delay_ns;
    char stop_reason[64];
    char error_message[256];
};

static volatile sig_atomic_t stop_requested = 0;

static void handle_signal(int signal_number)
{
    (void)signal_number;
    stop_requested = 1;
}

static void set_error(struct capture_stats *stats, const char *message)
{
    if (stats->error_message[0] == '\0') {
        (void)snprintf(stats->error_message, sizeof(stats->error_message), "%s", message);
    }
}

static void set_errno_error(
    struct capture_stats *stats,
    const char *operation,
    int error_number)
{
    if (stats->error_message[0] == '\0') {
        (void)snprintf(
            stats->error_message,
            sizeof(stats->error_message),
            "%s: %s",
            operation,
            strerror(error_number));
    }
}

static bool clock_now_ns(clockid_t clock_id, uint64_t *result)
{
    struct timespec now;

    if (clock_gettime(clock_id, &now) != 0) {
        return false;
    }
    *result = (uint64_t)now.tv_sec * UINT64_C(1000000000)
            + (uint64_t)now.tv_nsec;
    return true;
}

static bool parse_u64(const char *text, uint64_t minimum, uint64_t maximum, uint64_t *out)
{
    char *end = NULL;
    unsigned long long value;

    if (text == NULL || text[0] == '\0' || text[0] == '-') {
        return false;
    }
    errno = 0;
    value = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        return false;
    }
    if ((uint64_t)value < minimum || (uint64_t)value > maximum) {
        return false;
    }
    *out = (uint64_t)value;
    return true;
}

static int odr_filter_code(uint32_t odr_hz)
{
    switch (odr_hz) {
    case 4000u:
        return 0;
    case 2000u:
        return 1;
    case 1000u:
        return 2;
    case 500u:
        return 3;
    case 250u:
        return 4;
    case 125u:
        return 5;
    default:
        return -1;
    }
}

static int range_code(uint32_t range_g)
{
    switch (range_g) {
    case 2u:
        return 1;
    case 4u:
        return 2;
    case 8u:
        return 3;
    default:
        return -1;
    }
}

static void print_usage(FILE *stream, const char *program)
{
    (void)fprintf(
        stream,
        "Usage: %s --output PATH --summary PATH --ready-file PATH [options]\n"
        "\n"
        "Options:\n"
        "  --spi-device PATH   SPI device (default: %s)\n"
        "  --gpiochip PATH     GPIO chip (default: %s)\n"
        "  --drdy-line N       GPIO line offset (default: %u)\n"
        "  --odr-hz N          125, 250, 500, 1000, 2000, or 4000\n"
        "  --range-g N         2, 4, or 8 (default: %u)\n"
        "  --spi-hz N          SPI clock, 1..10000000 (default: %u)\n"
        "  --mock              Run without GPIO/SPI hardware\n"
        "  --max-samples N     Stop successfully after exactly N samples\n"
        "  --group-delay-ns N  Calibrated digital-filter delay in ns (default: 0)\n"
        "  --group-delay-calibrated\n"
        "                       Certify --group-delay-ns as calibrated\n"
        "  --group-delay-source TEXT\n"
        "                       Nonempty provenance required with calibration\n"
        "  --capabilities      Print build capabilities as JSON and exit\n"
        "  --help              Show this help\n",
        program,
        DEFAULT_SPI_DEVICE,
        DEFAULT_GPIOCHIP,
        DEFAULT_DRDY_LINE,
        DEFAULT_RANGE_G,
        DEFAULT_SPI_HZ);
}

enum parse_result {
    PARSE_OK = 0,
    PARSE_HELP = 1,
    PARSE_ERROR = 2,
    PARSE_CAPABILITIES = 3
};

static enum parse_result parse_arguments(
    int argc,
    char **argv,
    struct capture_config *config,
    struct capture_stats *stats)
{
    enum {
        OPT_OUTPUT = 1000,
        OPT_SUMMARY,
        OPT_READY_FILE,
        OPT_SPI_DEVICE,
        OPT_GPIOCHIP,
        OPT_DRDY_LINE,
        OPT_ODR_HZ,
        OPT_RANGE_G,
        OPT_SPI_HZ,
        OPT_MOCK,
        OPT_MAX_SAMPLES,
        OPT_GROUP_DELAY_NS,
        OPT_GROUP_DELAY_CALIBRATED,
        OPT_GROUP_DELAY_SOURCE,
        OPT_CAPABILITIES
    };
    static const struct option options[] = {
        {"output", required_argument, NULL, OPT_OUTPUT},
        {"summary", required_argument, NULL, OPT_SUMMARY},
        {"ready-file", required_argument, NULL, OPT_READY_FILE},
        {"spi-device", required_argument, NULL, OPT_SPI_DEVICE},
        {"gpiochip", required_argument, NULL, OPT_GPIOCHIP},
        {"drdy-line", required_argument, NULL, OPT_DRDY_LINE},
        {"odr-hz", required_argument, NULL, OPT_ODR_HZ},
        {"range-g", required_argument, NULL, OPT_RANGE_G},
        {"spi-hz", required_argument, NULL, OPT_SPI_HZ},
        {"mock", no_argument, NULL, OPT_MOCK},
        {"max-samples", required_argument, NULL, OPT_MAX_SAMPLES},
        {"group-delay-ns", required_argument, NULL, OPT_GROUP_DELAY_NS},
        {"group-delay-calibrated", no_argument, NULL, OPT_GROUP_DELAY_CALIBRATED},
        {"group-delay-source", required_argument, NULL, OPT_GROUP_DELAY_SOURCE},
        {"capabilities", no_argument, NULL, OPT_CAPABILITIES},
        {"help", no_argument, NULL, 'h'},
        {NULL, 0, NULL, 0}
    };
    int option;
    uint64_t value;

    memset(config, 0, sizeof(*config));
    config->spi_device = DEFAULT_SPI_DEVICE;
    config->gpiochip = DEFAULT_GPIOCHIP;
    config->drdy_line = DEFAULT_DRDY_LINE;
    config->odr_hz = DEFAULT_ODR_HZ;
    config->range_g = DEFAULT_RANGE_G;
    config->spi_hz = DEFAULT_SPI_HZ;

    opterr = 0;
    while ((option = getopt_long(argc, argv, "h", options, NULL)) != -1) {
        switch (option) {
        case OPT_OUTPUT:
            config->output_path = optarg;
            break;
        case OPT_SUMMARY:
            config->summary_path = optarg;
            break;
        case OPT_READY_FILE:
            config->ready_path = optarg;
            break;
        case OPT_SPI_DEVICE:
            config->spi_device = optarg;
            break;
        case OPT_GPIOCHIP:
            config->gpiochip = optarg;
            break;
        case OPT_DRDY_LINE:
            if (!parse_u64(optarg, 0, UINT32_MAX, &value)) {
                set_error(stats, "invalid --drdy-line value");
                return PARSE_ERROR;
            }
            config->drdy_line = (uint32_t)value;
            break;
        case OPT_ODR_HZ:
            if (!parse_u64(optarg, 1, UINT32_MAX, &value)) {
                set_error(stats, "invalid --odr-hz value");
                return PARSE_ERROR;
            }
            config->odr_hz = (uint32_t)value;
            break;
        case OPT_RANGE_G:
            if (!parse_u64(optarg, 1, UINT32_MAX, &value)) {
                set_error(stats, "invalid --range-g value");
                return PARSE_ERROR;
            }
            config->range_g = (uint32_t)value;
            break;
        case OPT_SPI_HZ:
            if (!parse_u64(optarg, 1, MAX_SPI_HZ, &value)) {
                set_error(stats, "invalid --spi-hz value");
                return PARSE_ERROR;
            }
            config->spi_hz = (uint32_t)value;
            break;
        case OPT_MOCK:
            config->mock = true;
            break;
        case OPT_MAX_SAMPLES:
            if (!parse_u64(optarg, 1, UINT64_MAX, &value)) {
                set_error(stats, "invalid --max-samples value");
                return PARSE_ERROR;
            }
            config->max_samples = value;
            break;
        case OPT_GROUP_DELAY_NS:
            if (!parse_u64(optarg, 0, INT64_MAX, &value)) {
                set_error(stats, "invalid --group-delay-ns value");
                return PARSE_ERROR;
            }
            config->group_delay_ns = (int64_t)value;
            break;
        case OPT_GROUP_DELAY_CALIBRATED:
            config->group_delay_calibrated = true;
            break;
        case OPT_GROUP_DELAY_SOURCE:
            config->group_delay_calibration_source = optarg;
            break;
        case OPT_CAPABILITIES:
            config->capabilities = true;
            break;
        case 'h':
            return PARSE_HELP;
        default:
            set_error(stats, "unknown or incomplete command-line option");
            return PARSE_ERROR;
        }
    }

    if (optind != argc) {
        set_error(stats, "positional arguments are not supported");
        return PARSE_ERROR;
    }
    if (config->capabilities) {
        return PARSE_CAPABILITIES;
    }
    if (config->output_path == NULL
        || config->summary_path == NULL
        || config->ready_path == NULL) {
        set_error(stats, "--output, --summary, and --ready-file are required");
        return PARSE_ERROR;
    }
    if (odr_filter_code(config->odr_hz) < 0) {
        set_error(stats, "unsupported --odr-hz; use 125, 250, 500, 1000, 2000, or 4000");
        return PARSE_ERROR;
    }
    if (range_code(config->range_g) < 0) {
        set_error(stats, "unsupported --range-g; use 2, 4, or 8");
        return PARSE_ERROR;
    }
    if (strcmp(config->output_path, config->summary_path) == 0
        || strcmp(config->output_path, config->ready_path) == 0
        || strcmp(config->summary_path, config->ready_path) == 0) {
        set_error(stats, "--output, --summary, and --ready-file must be different paths");
        return PARSE_ERROR;
    }
    if (config->group_delay_calibrated) {
        const unsigned char *source = (const unsigned char *)
            config->group_delay_calibration_source;
        bool has_non_whitespace = false;

        if (config->group_delay_ns <= 0) {
            set_error(
                stats,
                "--group-delay-calibrated requires --group-delay-ns greater than zero");
            return PARSE_ERROR;
        }
        if (source != NULL) {
            while (*source != '\0') {
                if (!isspace(*source)) {
                    has_non_whitespace = true;
                    break;
                }
                ++source;
            }
        }
        if (!has_non_whitespace) {
            set_error(
                stats,
                "--group-delay-calibrated requires a nonempty --group-delay-source");
            return PARSE_ERROR;
        }
    } else if (config->group_delay_ns != 0) {
        set_error(
            stats,
            "a positive --group-delay-ns requires --group-delay-calibrated and --group-delay-source");
        return PARSE_ERROR;
    } else if (config->group_delay_calibration_source != NULL) {
        set_error(
            stats,
            "--group-delay-source requires --group-delay-calibrated");
        return PARSE_ERROR;
    }
    return PARSE_OK;
}

static void print_capabilities(void)
{
    (void)printf(
        "{\"schema_version\":1,\"hardware_support\":%s,"
        "\"mock_support\":true,\"gpio_event_clock\":\"CLOCK_MONOTONIC\","
        "\"gpio_backend\":\"%s\",\"gpio_uapi_version\":%s,"
        "\"line_sequence_source\":\"%s\","
        "\"line_sequence_certified\":%s,"
        "\"raw_format_version\":%u}\n",
        ADXL355_ENABLE_LINUX_HW ? "true" : "false",
        GPIO_BACKEND_NAME,
        ADXL355_ENABLE_LINUX_HW ? "2" : "null",
        GPIO_LINE_SEQUENCE_SOURCE,
        ADXL355_ENABLE_LINUX_HW ? "true" : "false",
        ADXL355_FORMAT_VERSION);
}

static char *json_escape(const char *text)
{
    size_t length;
    size_t capacity;
    size_t source;
    size_t target = 0;
    char *escaped;
    static const char hex[] = "0123456789abcdef";

    if (text == NULL) {
        text = "";
    }
    length = strlen(text);
    if (length > (SIZE_MAX - 3u) / 6u) {
        return NULL;
    }
    capacity = length * 6u + 3u;
    escaped = malloc(capacity);
    if (escaped == NULL) {
        return NULL;
    }
    escaped[target++] = '"';
    for (source = 0; source < length; ++source) {
        unsigned char byte = (unsigned char)text[source];

        switch (byte) {
        case '"':
            escaped[target++] = '\\';
            escaped[target++] = '"';
            break;
        case '\\':
            escaped[target++] = '\\';
            escaped[target++] = '\\';
            break;
        case '\b':
            escaped[target++] = '\\';
            escaped[target++] = 'b';
            break;
        case '\f':
            escaped[target++] = '\\';
            escaped[target++] = 'f';
            break;
        case '\n':
            escaped[target++] = '\\';
            escaped[target++] = 'n';
            break;
        case '\r':
            escaped[target++] = '\\';
            escaped[target++] = 'r';
            break;
        case '\t':
            escaped[target++] = '\\';
            escaped[target++] = 't';
            break;
        default:
            if (byte < 0x20u) {
                escaped[target++] = '\\';
                escaped[target++] = 'u';
                escaped[target++] = '0';
                escaped[target++] = '0';
                escaped[target++] = hex[(byte >> 4) & 0x0fu];
                escaped[target++] = hex[byte & 0x0fu];
            } else {
                escaped[target++] = (char)byte;
            }
            break;
        }
    }
    escaped[target++] = '"';
    escaped[target] = '\0';
    return escaped;
}

static bool write_all(int file_descriptor, const char *data, size_t length)
{
    size_t offset = 0;

    while (offset < length) {
        ssize_t written = write(file_descriptor, data + offset, length - offset);

        if (written < 0) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }
        if (written == 0) {
            errno = EIO;
            return false;
        }
        offset += (size_t)written;
    }
    return true;
}

static void fsync_parent_directory(const char *path)
{
    char *copy = strdup(path);
    char *slash;
    const char *directory;
    int directory_fd;

    if (copy == NULL) {
        return;
    }
    slash = strrchr(copy, '/');
    if (slash == NULL) {
        directory = ".";
    } else if (slash == copy) {
        slash[1] = '\0';
        directory = copy;
    } else {
        *slash = '\0';
        directory = copy;
    }
    directory_fd = open(directory, O_RDONLY);
    if (directory_fd >= 0) {
        (void)fsync(directory_fd);
        (void)close(directory_fd);
    }
    free(copy);
}

static bool atomic_write_text(const char *path, const char *text)
{
    size_t temporary_length;
    char *temporary_path;
    int file_descriptor = -1;
    bool success = false;
    int saved_errno = 0;

    if (strlen(path) > SIZE_MAX - 40u) {
        errno = ENAMETOOLONG;
        return false;
    }
    temporary_length = strlen(path) + 40u;
    temporary_path = malloc(temporary_length);
    if (temporary_path == NULL) {
        return false;
    }
    (void)snprintf(
        temporary_path,
        temporary_length,
        "%s.tmp.%ld",
        path,
        (long)getpid());
    file_descriptor = open(temporary_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (file_descriptor < 0) {
        goto cleanup;
    }
    if (!write_all(file_descriptor, text, strlen(text))) {
        goto cleanup;
    }
    if (fsync(file_descriptor) != 0) {
        goto cleanup;
    }
    if (close(file_descriptor) != 0) {
        file_descriptor = -1;
        goto cleanup;
    }
    file_descriptor = -1;
    if (rename(temporary_path, path) != 0) {
        goto cleanup;
    }
    fsync_parent_directory(path);
    success = true;

cleanup:
    saved_errno = errno;
    if (file_descriptor >= 0) {
        (void)close(file_descriptor);
    }
    if (!success) {
        (void)unlink(temporary_path);
    }
    free(temporary_path);
    errno = saved_errno;
    return success;
}

static char *make_config_json(const struct capture_config *config)
{
    char *spi = json_escape(config->spi_device);
    char *gpio = json_escape(config->gpiochip);
    char *group_delay_source = config->group_delay_calibration_source != NULL
        ? json_escape(config->group_delay_calibration_source)
        : strdup("null");
    const char *group_delay_calibrated = config->group_delay_calibrated
        ? "true"
        : "false";
    int length;
    char *json;

    if (spi == NULL || gpio == NULL || group_delay_source == NULL) {
        free(spi);
        free(gpio);
        free(group_delay_source);
        return NULL;
    }
    length = snprintf(
        NULL,
        0,
        "{\"spi_device\":%s,\"gpiochip\":%s,\"drdy_line\":%u,"
        "\"odr_hz\":%u,\"range_g\":%u,\"spi_hz\":%u,"
        "\"group_delay_ns\":%" PRId64 ","
        "\"group_delay_calibrated\":%s,"
        "\"group_delay_calibration_source\":%s,"
        "\"max_samples\":%" PRIu64 "}",
        spi,
        gpio,
        config->drdy_line,
        config->odr_hz,
        config->range_g,
        config->spi_hz,
        config->group_delay_ns,
        group_delay_calibrated,
        group_delay_source,
        config->max_samples);
    if (length < 0) {
        free(spi);
        free(gpio);
        free(group_delay_source);
        return NULL;
    }
    json = malloc((size_t)length + 1u);
    if (json != NULL) {
        (void)snprintf(
            json,
            (size_t)length + 1u,
            "{\"spi_device\":%s,\"gpiochip\":%s,\"drdy_line\":%u,"
            "\"odr_hz\":%u,\"range_g\":%u,\"spi_hz\":%u,"
            "\"group_delay_ns\":%" PRId64 ","
            "\"group_delay_calibrated\":%s,"
            "\"group_delay_calibration_source\":%s,"
            "\"max_samples\":%" PRIu64 "}",
            spi,
            gpio,
            config->drdy_line,
            config->odr_hz,
            config->range_g,
            config->spi_hz,
            config->group_delay_ns,
            group_delay_calibrated,
            group_delay_source,
            config->max_samples);
    }
    free(spi);
    free(gpio);
    free(group_delay_source);
    return json;
}

static bool write_ready_json(
    const struct capture_config *config,
    const struct capture_stats *stats)
{
    char *config_json = make_config_json(config);
    char *group_delay_source = config->group_delay_calibration_source != NULL
        ? json_escape(config->group_delay_calibration_source)
        : strdup("null");
    const char *group_delay_calibrated = config->group_delay_calibrated
        ? "true"
        : "false";
    int length;
    char *json;
    bool success;

    if (config_json == NULL || group_delay_source == NULL) {
        free(config_json);
        free(group_delay_source);
        errno = ENOMEM;
        return false;
    }
    length = snprintf(
        NULL,
        0,
        "{\"status\":\"ready\",\"pid\":%ld,\"start_monotonic_ns\":%" PRIu64
        ",\"group_delay_ns\":%" PRId64
        ",\"group_delay_calibrated\":%s"
        ",\"group_delay_calibration_source\":%s"
        ",\"config\":%s}\n",
        (long)getpid(),
        stats->start_monotonic_ns,
        config->group_delay_ns,
        group_delay_calibrated,
        group_delay_source,
        config_json);
    if (length < 0) {
        free(config_json);
        free(group_delay_source);
        errno = EINVAL;
        return false;
    }
    json = malloc((size_t)length + 1u);
    if (json == NULL) {
        free(config_json);
        free(group_delay_source);
        return false;
    }
    (void)snprintf(
        json,
        (size_t)length + 1u,
        "{\"status\":\"ready\",\"pid\":%ld,\"start_monotonic_ns\":%" PRIu64
        ",\"group_delay_ns\":%" PRId64
        ",\"group_delay_calibrated\":%s"
        ",\"group_delay_calibration_source\":%s"
        ",\"config\":%s}\n",
        (long)getpid(),
        stats->start_monotonic_ns,
        config->group_delay_ns,
        group_delay_calibrated,
        group_delay_source,
        config_json);
    success = atomic_write_text(config->ready_path, json);
    free(json);
    free(config_json);
    free(group_delay_source);
    return success;
}

static bool write_summary_json(
    const struct capture_config *config,
    const struct capture_stats *stats,
    bool complete)
{
    char *config_json = make_config_json(config);
    char *output = json_escape(config->output_path);
    char *reason = json_escape(stats->stop_reason);
    char *error = json_escape(stats->error_message);
    char *group_delay_source = config->group_delay_calibration_source != NULL
        ? json_escape(config->group_delay_calibration_source)
        : strdup("null");
    const char *status = complete ? "complete" : "failed";
    const char *mock = config->mock ? "true" : "false";
    const char *group_delay_calibrated = config->group_delay_calibrated
        ? "true"
        : "false";
    const char *line_sequence_source = config->mock
        ? "synthetic_mock"
        : GPIO_LINE_SEQUENCE_SOURCE;
    const char *line_sequence_certified = (!config->mock && ADXL355_ENABLE_LINUX_HW)
        ? "true"
        : "false";
    int length;
    char *json;
    bool success;

    if (config_json == NULL || output == NULL || reason == NULL || error == NULL
        || group_delay_source == NULL) {
        free(config_json);
        free(output);
        free(reason);
        free(error);
        free(group_delay_source);
        errno = ENOMEM;
        return false;
    }
    length = snprintf(
        NULL,
        0,
        "{\"schema_version\":1,\"status\":\"%s\","
        "\"samples\":%" PRIu64 ",\"samples_written\":%" PRIu64 ","
        "\"first_drdy_monotonic_ns\":%" PRIu64 ","
        "\"last_drdy_monotonic_ns\":%" PRIu64 ","
        "\"line_seq_gaps\":%" PRIu64 ",\"fifo_overruns\":%" PRIu64 ","
        "\"gpio_backlog_events\":%" PRIu64 ","
        "\"fifo_protocol_errors\":%" PRIu64 ","
        "\"fifo_xyz_mismatches\":%" PRIu64 ","
        "\"fifo_xyz_sets_drained\":%" PRIu64 ","
        "\"max_fifo_entries\":%u,"
        "\"output_file\":%s,\"clock\":\"CLOCK_MONOTONIC\","
        "\"timestamp_semantics\":\"drdy_edge\",\"mock\":%s,"
        "\"gpio_backend\":\"%s\","
        "\"line_sequence_source\":\"%s\","
        "\"line_sequence_certified\":%s,"
        "\"sample_source\":\"%s\","
        "\"timestamp_pairing\":\"%s\","
        "\"start_realtime_ns\":%" PRIu64 ","
        "\"start_monotonic_ns\":%" PRIu64 ","
        "\"group_delay_ns\":%" PRId64 ","
        "\"group_delay_calibrated\":%s,"
        "\"group_delay_calibration_source\":%s,\"stop_reason\":%s,"
        "\"error\":%s,\"config\":%s}\n",
        status,
        stats->samples_written,
        stats->samples_written,
        stats->first_drdy_ns,
        stats->last_drdy_ns,
        stats->line_seq_gaps,
        stats->fifo_overruns,
        stats->gpio_backlog_events,
        stats->fifo_protocol_errors,
        stats->fifo_xyz_mismatches,
        stats->fifo_xyz_sets_drained,
        stats->max_fifo_entries,
        output,
        mock,
        config->mock ? "synthetic_mock" : GPIO_BACKEND_NAME,
        line_sequence_source,
        line_sequence_certified,
        config->mock ? "mock" : "FIFO_DATA_oldest",
        config->mock ? "synthetic" : "one_drdy_edge_to_one_fifo_xyz",
        stats->start_realtime_ns,
        stats->start_monotonic_ns,
        stats->group_delay_ns,
        group_delay_calibrated,
        group_delay_source,
        reason,
        error,
        config_json);
    if (length < 0) {
        free(config_json);
        free(output);
        free(reason);
        free(error);
        free(group_delay_source);
        errno = EINVAL;
        return false;
    }
    json = malloc((size_t)length + 1u);
    if (json == NULL) {
        free(config_json);
        free(output);
        free(reason);
        free(error);
        free(group_delay_source);
        return false;
    }
    (void)snprintf(
        json,
        (size_t)length + 1u,
        "{\"schema_version\":1,\"status\":\"%s\","
        "\"samples\":%" PRIu64 ",\"samples_written\":%" PRIu64 ","
        "\"first_drdy_monotonic_ns\":%" PRIu64 ","
        "\"last_drdy_monotonic_ns\":%" PRIu64 ","
        "\"line_seq_gaps\":%" PRIu64 ",\"fifo_overruns\":%" PRIu64 ","
        "\"gpio_backlog_events\":%" PRIu64 ","
        "\"fifo_protocol_errors\":%" PRIu64 ","
        "\"fifo_xyz_mismatches\":%" PRIu64 ","
        "\"fifo_xyz_sets_drained\":%" PRIu64 ","
        "\"max_fifo_entries\":%u,"
        "\"output_file\":%s,\"clock\":\"CLOCK_MONOTONIC\","
        "\"timestamp_semantics\":\"drdy_edge\",\"mock\":%s,"
        "\"gpio_backend\":\"%s\","
        "\"line_sequence_source\":\"%s\","
        "\"line_sequence_certified\":%s,"
        "\"sample_source\":\"%s\","
        "\"timestamp_pairing\":\"%s\","
        "\"start_realtime_ns\":%" PRIu64 ","
        "\"start_monotonic_ns\":%" PRIu64 ","
        "\"group_delay_ns\":%" PRId64 ","
        "\"group_delay_calibrated\":%s,"
        "\"group_delay_calibration_source\":%s,\"stop_reason\":%s,"
        "\"error\":%s,\"config\":%s}\n",
        status,
        stats->samples_written,
        stats->samples_written,
        stats->first_drdy_ns,
        stats->last_drdy_ns,
        stats->line_seq_gaps,
        stats->fifo_overruns,
        stats->gpio_backlog_events,
        stats->fifo_protocol_errors,
        stats->fifo_xyz_mismatches,
        stats->fifo_xyz_sets_drained,
        stats->max_fifo_entries,
        output,
        mock,
        config->mock ? "synthetic_mock" : GPIO_BACKEND_NAME,
        line_sequence_source,
        line_sequence_certified,
        config->mock ? "mock" : "FIFO_DATA_oldest",
        config->mock ? "synthetic" : "one_drdy_edge_to_one_fifo_xyz",
        stats->start_realtime_ns,
        stats->start_monotonic_ns,
        stats->group_delay_ns,
        group_delay_calibrated,
        group_delay_source,
        reason,
        error,
        config_json);
    success = atomic_write_text(config->summary_path, json);
    free(json);
    free(config_json);
    free(output);
    free(reason);
    free(error);
    free(group_delay_source);
    return success;
}

static bool write_header(
    FILE *output,
    const struct capture_config *config,
    const struct capture_stats *stats)
{
    uint8_t bytes[ADXL355_HEADER_BYTES];
    struct adxl355_header_values values;

    memset(&values, 0, sizeof(values));
    values.flags = config->mock ? ADXL355_HEADER_FLAG_MOCK : 0u;
    values.odr_millihz = config->odr_hz * 1000u;
    values.range_g = (uint16_t)config->range_g;
    values.start_realtime_ns = stats->start_realtime_ns;
    values.start_monotonic_ns = stats->start_monotonic_ns;
    values.group_delay_ns = stats->group_delay_ns;
    adxl355_encode_header(bytes, &values);
    return fwrite(bytes, 1, sizeof(bytes), output) == sizeof(bytes);
}

static bool write_sample(
    FILE *output,
    const struct adxl355_record_values *values,
    struct capture_stats *stats,
    uint64_t *previous_line_seqno,
    bool *have_previous_line_seqno)
{
    uint8_t bytes[ADXL355_RECORD_BYTES];

    if (*have_previous_line_seqno
        && values->line_seqno > *previous_line_seqno + 1u) {
        stats->line_seq_gaps += values->line_seqno - *previous_line_seqno - 1u;
    }
    *previous_line_seqno = values->line_seqno;
    *have_previous_line_seqno = true;
    if ((values->status & ADXL355_STATUS_FIFO_OVR) != 0u) {
        ++stats->fifo_overruns;
    }
    adxl355_encode_record(bytes, values);
    if (fwrite(bytes, 1, sizeof(bytes), output) != sizeof(bytes)) {
        return false;
    }
    if (stats->samples_written == 0u) {
        stats->first_drdy_ns = values->drdy_monotonic_ns;
    }
    stats->last_drdy_ns = values->drdy_monotonic_ns;
    ++stats->samples_written;
    return true;
}

#if ADXL355_ENABLE_LINUX_HW
static bool validate_line_sequence_before_read(
    uint64_t line_seqno,
    uint64_t previous_line_seqno,
    bool have_previous_line_seqno,
    struct capture_stats *stats)
{
    if (!have_previous_line_seqno) {
        if (line_seqno == 1u) {
            return true;
        }
        stats->line_seq_gaps += line_seqno > 1u ? line_seqno - 1u : 1u;
        set_error(stats, "first DRDY line sequence is not 1; timestamp/sample pairing is unknown");
        return false;
    }
    if (previous_line_seqno == UINT64_MAX) {
        ++stats->line_seq_gaps;
        set_error(stats, "DRDY line sequence wrapped or is non-monotonic");
        return false;
    }
    if (line_seqno == previous_line_seqno + 1u) {
        return true;
    }
    if (line_seqno > previous_line_seqno + 1u) {
        stats->line_seq_gaps += line_seqno - previous_line_seqno - 1u;
        set_error(stats, "DRDY line sequence gap detected before FIFO read");
    } else {
        ++stats->line_seq_gaps;
        set_error(stats, "DRDY line sequence is non-monotonic");
    }
    return false;
}
#endif

static bool flush_and_sync(FILE *output)
{
    if (fflush(output) != 0) {
        return false;
    }
    if (fsync(fileno(output)) != 0) {
        return false;
    }
    return true;
}

static bool sleep_until_monotonic(uint64_t target_ns)
{
    while (!stop_requested) {
        uint64_t now;
        uint64_t remaining;
        struct timespec request;

        if (!clock_now_ns(CLOCK_MONOTONIC, &now)) {
            return false;
        }
        if (now >= target_ns) {
            return true;
        }
        remaining = target_ns - now;
        request.tv_sec = (time_t)(remaining / UINT64_C(1000000000));
        request.tv_nsec = (long)(remaining % UINT64_C(1000000000));
        if (nanosleep(&request, NULL) != 0 && errno != EINTR) {
            return false;
        }
    }
    return true;
}

static bool run_mock_capture(
    FILE *output,
    const struct capture_config *config,
    struct capture_stats *stats)
{
    const uint64_t period_ns = UINT64_C(1000000000) / config->odr_hz;
    uint64_t next_edge_ns = stats->start_monotonic_ns;
    uint64_t previous_line_seqno = 0;
    bool have_previous_line_seqno = false;

    while (!stop_requested) {
        struct adxl355_record_values values;

        if (config->max_samples > 0u
            && stats->samples_written >= config->max_samples) {
            (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "max_samples");
            return true;
        }
        next_edge_ns += period_ns;
        if (!sleep_until_monotonic(next_edge_ns)) {
            set_errno_error(stats, "mock timing", errno);
            return false;
        }
        if (stop_requested) {
            break;
        }
        memset(&values, 0, sizeof(values));
        values.sample_seq = stats->samples_written;
        values.line_seqno = stats->samples_written + 1u;
        if (!clock_now_ns(CLOCK_MONOTONIC, &values.drdy_monotonic_ns)
            || !clock_now_ns(CLOCK_MONOTONIC, &values.spi_complete_monotonic_ns)) {
            set_errno_error(stats, "clock_gettime", errno);
            return false;
        }
        values.x_raw = (int32_t)(stats->samples_written % 2001u) - 1000;
        values.y_raw = 2000 - (int32_t)(stats->samples_written % 4001u);
        values.z_raw = 256000;
        values.temp_raw = 1852;
        values.status = ADXL355_STATUS_DATA_RDY;
        values.fifo_entries = 0;
        if (!write_sample(
                output,
                &values,
                stats,
                &previous_line_seqno,
                &have_previous_line_seqno)) {
            set_errno_error(stats, "write sample", errno);
            return false;
        }
    }
    if (config->max_samples > 0u
        && stats->samples_written < config->max_samples) {
        (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "signal_before_target");
        set_error(stats, "terminated before --max-samples was reached");
        return false;
    }
    (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "signal");
    return true;
}

#if ADXL355_ENABLE_LINUX_HW
struct hardware_context {
    int spi_fd;
    uint32_t spi_hz;
    int gpiochip_fd;
    int gpio_line_fd;
    bool sensor_started;
};

#define ADXL355_FIFO_SNAPSHOT_LAST_REG ADXL355_REG_TEMP1
#define ADXL355_FIFO_SNAPSHOT_BYTES \
    ((size_t)(ADXL355_FIFO_SNAPSHOT_LAST_REG - ADXL355_REG_STATUS + 1u))

struct adxl355_fifo_snapshot {
    uint8_t status;
    uint8_t fifo_entries;
    int16_t temp_raw;
};

static void hardware_context_init(struct hardware_context *hardware)
{
    memset(hardware, 0, sizeof(*hardware));
    hardware->spi_fd = -1;
    hardware->gpiochip_fd = -1;
    hardware->gpio_line_fd = -1;
}

static bool spi_transfer(
    const struct hardware_context *hardware,
    const uint8_t *transmit,
    uint8_t *receive,
    size_t length)
{
    struct spi_ioc_transfer transfer;

    memset(&transfer, 0, sizeof(transfer));
    transfer.tx_buf = (uintptr_t)transmit;
    transfer.rx_buf = (uintptr_t)receive;
    transfer.len = (uint32_t)length;
    transfer.speed_hz = hardware->spi_hz;
    transfer.bits_per_word = 8;
    {
        int result = ioctl(hardware->spi_fd, SPI_IOC_MESSAGE(1), &transfer);

        if (result == (int)length) {
            return true;
        }
        if (result >= 0) {
            errno = EIO;
        }
        return false;
    }
}

static bool spi_write_register(
    const struct hardware_context *hardware,
    uint8_t register_address,
    uint8_t value)
{
    uint8_t transmit[2] = {(uint8_t)(register_address << 1), value};
    uint8_t receive[2] = {0, 0};

    return spi_transfer(hardware, transmit, receive, sizeof(transmit));
}

static bool spi_read_register(
    const struct hardware_context *hardware,
    uint8_t register_address,
    uint8_t *value)
{
    uint8_t transmit[2] = {(uint8_t)((register_address << 1) | 1u), 0};
    uint8_t receive[2] = {0, 0};

    if (!spi_transfer(hardware, transmit, receive, sizeof(transmit))) {
        return false;
    }
    *value = receive[1];
    return true;
}

static bool spi_read_shadow_registers(
    const struct hardware_context *hardware,
    uint8_t values[ADXL355_SHADOW_BYTES])
{
    uint8_t transmit[1u + ADXL355_SHADOW_BYTES];
    uint8_t receive[1u + ADXL355_SHADOW_BYTES];

    memset(transmit, 0, sizeof(transmit));
    memset(receive, 0, sizeof(receive));
    transmit[0] = (uint8_t)((ADXL355_REG_SHADOW_BASE << 1) | 1u);
    if (!spi_transfer(hardware, transmit, receive, sizeof(transmit))) {
        return false;
    }
    memcpy(values, receive + 1, ADXL355_SHADOW_BYTES);
    return true;
}

static bool spi_read_fifo_snapshot(
    const struct hardware_context *hardware,
    struct adxl355_fifo_snapshot *values)
{
    uint8_t transmit[1u + ADXL355_FIFO_SNAPSHOT_BYTES];
    uint8_t receive[1u + ADXL355_FIFO_SNAPSHOT_BYTES];

    memset(transmit, 0, sizeof(transmit));
    memset(receive, 0, sizeof(receive));
    transmit[0] = (uint8_t)((ADXL355_REG_STATUS << 1) | 1u);
    if (!spi_transfer(hardware, transmit, receive, sizeof(transmit))) {
        return false;
    }
    values->status = receive[1];
    values->fifo_entries = (uint8_t)(receive[2] & ADXL355_FIFO_ENTRIES_MASK);
    values->temp_raw = (int16_t)((((uint16_t)receive[3] & 0x0fu) << 8)
                               | (uint16_t)receive[4]);
    return true;
}

static bool spi_pop_fifo_xyz(
    const struct hardware_context *hardware,
    struct adxl355_fifo_xyz *values,
    enum adxl355_fifo_decode_result *decode_result,
    uint64_t *complete_ns)
{
    uint8_t transmit[1u + ADXL355_FIFO_XYZ_BYTES];
    uint8_t receive[1u + ADXL355_FIFO_XYZ_BYTES];

    memset(transmit, 0, sizeof(transmit));
    memset(receive, 0, sizeof(receive));
    transmit[0] = (uint8_t)((ADXL355_REG_FIFO_DATA << 1) | 1u);
    if (!spi_transfer(hardware, transmit, receive, sizeof(transmit))) {
        return false;
    }
    if (!clock_now_ns(CLOCK_MONOTONIC, complete_ns)) {
        return false;
    }
    values->command_response = receive[0];
    *decode_result = adxl355_decode_fifo_xyz(receive + 1, values);
    return true;
}

static bool sleep_milliseconds(unsigned int milliseconds)
{
    struct timespec request;

    request.tv_sec = (time_t)(milliseconds / 1000u);
    request.tv_nsec = (long)(milliseconds % 1000u) * 1000000L;
    while (nanosleep(&request, &request) != 0) {
        if (errno != EINTR) {
            return false;
        }
    }
    return true;
}

static bool wait_for_nvm_ready(
    const struct hardware_context *hardware,
    struct capture_stats *stats)
{
    unsigned int poll_count;

    for (poll_count = 0; poll_count < 255u; ++poll_count) {
        uint8_t status;

        if (!spi_read_register(hardware, ADXL355_REG_STATUS, &status)) {
            set_errno_error(stats, "read ADXL355 NVM status", errno);
            return false;
        }
        if ((status & ADXL355_STATUS_NVM_BUSY) == 0u) {
            return true;
        }
        if (!sleep_milliseconds(1u)) {
            set_errno_error(stats, "wait for ADXL355 NVM", errno);
            return false;
        }
    }
    set_error(stats, "ADXL355 NVM remained busy after software reset");
    return false;
}

static bool reset_and_verify_shadow_registers(
    const struct hardware_context *hardware,
    const uint8_t expected[ADXL355_SHADOW_BYTES],
    struct capture_stats *stats)
{
    unsigned int attempt;

    for (attempt = 0; attempt < 3u; ++attempt) {
        uint8_t observed[ADXL355_SHADOW_BYTES];

        if (!spi_write_register(hardware, ADXL355_REG_RESET, ADXL355_RESET_CODE)) {
            set_errno_error(stats, "software-reset ADXL355", errno);
            return false;
        }
        if (!wait_for_nvm_ready(hardware, stats)) {
            return false;
        }
        if (!sleep_milliseconds(1u)) {
            set_errno_error(stats, "settle ADXL355 shadow registers", errno);
            return false;
        }
        if (!spi_read_shadow_registers(hardware, observed)) {
            set_errno_error(stats, "read ADXL355 shadow registers after reset", errno);
            return false;
        }
        if (memcmp(expected, observed, ADXL355_SHADOW_BYTES) == 0) {
            return true;
        }
    }
    set_error(
        stats,
        "ADXL355 shadow registers changed across software reset after three attempts");
    return false;
}

static bool open_spi(
    struct hardware_context *hardware,
    const struct capture_config *config,
    struct capture_stats *stats)
{
    uint8_t mode = SPI_MODE_0;
    uint8_t bits = 8;
    uint32_t speed = config->spi_hz;

    hardware->spi_fd = open(config->spi_device, O_RDWR);
    if (hardware->spi_fd < 0) {
        set_errno_error(stats, "open SPI device", errno);
        return false;
    }
    hardware->spi_hz = speed;
    if (ioctl(hardware->spi_fd, SPI_IOC_WR_MODE, &mode) != 0
        || ioctl(hardware->spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) != 0
        || ioctl(hardware->spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) != 0) {
        set_errno_error(stats, "configure SPI device", errno);
        return false;
    }
    return true;
}

static bool prepare_sensor(
    const struct hardware_context *hardware,
    const struct capture_config *config,
    struct capture_stats *stats)
{
    uint8_t id_ad;
    uint8_t id_mst;
    uint8_t partid;
    uint8_t revid;
    uint8_t fifo_entries;
    uint8_t shadow_before_reset[ADXL355_SHADOW_BYTES];
    uint8_t range_readback;
    uint8_t filter_readback;
    uint8_t sync_readback;
    uint8_t power_readback;
    const uint8_t expected_range = (uint8_t)(
        ADXL355_RANGE_INT_POL_HIGH | (uint8_t)range_code(config->range_g));
    const uint8_t expected_filter = (uint8_t)odr_filter_code(config->odr_hz);

    if (!spi_read_register(hardware, ADXL355_REG_DEVID_AD, &id_ad)
        || !spi_read_register(hardware, ADXL355_REG_DEVID_MST, &id_mst)
        || !spi_read_register(hardware, ADXL355_REG_PARTID, &partid)
        || !spi_read_register(hardware, ADXL355_REG_REVID, &revid)
        || !spi_read_shadow_registers(hardware, shadow_before_reset)) {
        set_errno_error(stats, "identify ADXL355 and save NVM shadow registers", errno);
        return false;
    }
    if (id_ad != ADXL355_DEVID_AD_VALUE
        || id_mst != ADXL355_DEVID_MST_VALUE
        || partid != ADXL355_PARTID_VALUE) {
        (void)snprintf(
            stats->error_message,
            sizeof(stats->error_message),
            "ADXL355 identity mismatch: DEVID_AD=0x%02x DEVID_MST=0x%02x "
            "PARTID=0x%02x REVID=0x%02x",
            id_ad,
            id_mst,
            partid,
            revid);
        return false;
    }
    if (!reset_and_verify_shadow_registers(
            hardware,
            shadow_before_reset,
            stats)) {
        return false;
    }
    if (!spi_write_register(
            hardware,
            ADXL355_REG_POWER_CTL,
            ADXL355_POWER_CTL_STANDBY)
        || !spi_write_register(hardware, ADXL355_REG_RANGE, expected_range)
        || !spi_write_register(hardware, ADXL355_REG_FILTER, expected_filter)
        || !spi_write_register(hardware, ADXL355_REG_SYNC, ADXL355_SYNC_INTERNAL)
        || !spi_read_register(hardware, ADXL355_REG_RANGE, &range_readback)
        || !spi_read_register(hardware, ADXL355_REG_FILTER, &filter_readback)
        || !spi_read_register(hardware, ADXL355_REG_SYNC, &sync_readback)
        || !spi_read_register(hardware, ADXL355_REG_POWER_CTL, &power_readback)
        || !spi_read_register(hardware, ADXL355_REG_FIFO_ENTRIES, &fifo_entries)) {
        set_errno_error(stats, "configure and verify ADXL355 over SPI", errno);
        return false;
    }
    if (range_readback != expected_range
        || filter_readback != expected_filter
        || sync_readback != ADXL355_SYNC_INTERNAL
        || power_readback != ADXL355_POWER_CTL_STANDBY) {
        (void)snprintf(
            stats->error_message,
            sizeof(stats->error_message),
            "ADXL355 configuration readback mismatch: RANGE=0x%02x "
            "FILTER=0x%02x SYNC=0x%02x POWER_CTL=0x%02x",
            range_readback,
            filter_readback,
            sync_readback,
            power_readback);
        return false;
    }
    if ((fifo_entries & ADXL355_FIFO_ENTRIES_MASK) != 0u) {
        ++stats->fifo_protocol_errors;
        set_error(stats, "ADXL355 FIFO is not empty after reset while in standby");
        return false;
    }
    return true;
}

static bool start_sensor(
    struct hardware_context *hardware,
    struct capture_stats *stats)
{
    if (!spi_write_register(hardware, ADXL355_REG_POWER_CTL, 0x00u)) {
        set_errno_error(stats, "start ADXL355 measurement", errno);
        return false;
    }
    hardware->sensor_started = true;
    return true;
}

static bool request_drdy_line(
    struct hardware_context *hardware,
    const struct capture_config *config,
    struct capture_stats *stats)
{
    struct gpio_v2_line_request request;
    int descriptor_flags;

    hardware->gpiochip_fd = open(config->gpiochip, O_RDONLY | O_CLOEXEC);
    if (hardware->gpiochip_fd < 0) {
        set_errno_error(stats, "open GPIO chip", errno);
        return false;
    }
    memset(&request, 0, sizeof(request));
    request.offsets[0] = config->drdy_line;
    request.num_lines = 1u;
    request.event_buffer_size = GPIO_EVENT_BATCH_SIZE;
    request.config.flags = GPIO_V2_LINE_FLAG_INPUT
                         | GPIO_V2_LINE_FLAG_EDGE_RISING;
    (void)snprintf(
        request.consumer,
        sizeof(request.consumer),
        "adxl355_capture");
    /*
     * Not setting GPIO_V2_LINE_FLAG_EVENT_CLOCK_REALTIME or EVENT_CLOCK_HTE
     * selects the GPIO v2 ABI's default CLOCK_MONOTONIC event clock.
     */
    if (ioctl(hardware->gpiochip_fd, GPIO_V2_GET_LINE_IOCTL, &request) != 0) {
        if (errno == ENOTTY) {
            set_error(
                stats,
                "GPIO device/kernel lacks character-device uAPI v2; the libgpiod v1 fallback is intentionally disabled because it has no kernel line sequence number");
        } else {
            set_errno_error(stats, "request DRDY line with GPIO uAPI v2", errno);
        }
        return false;
    }
    hardware->gpio_line_fd = request.fd;
    descriptor_flags = fcntl(hardware->gpio_line_fd, F_GETFL);
    if (descriptor_flags < 0
        || fcntl(
            hardware->gpio_line_fd,
            F_SETFL,
            descriptor_flags | O_NONBLOCK) != 0) {
        set_errno_error(stats, "configure DRDY event descriptor", errno);
        return false;
    }
    return true;
}

static void close_hardware(struct hardware_context *hardware)
{
    if (hardware->sensor_started && hardware->spi_fd >= 0) {
        (void)spi_write_register(
            hardware,
            ADXL355_REG_POWER_CTL,
            ADXL355_POWER_CTL_STANDBY);
    }
    if (hardware->gpio_line_fd >= 0) {
        (void)close(hardware->gpio_line_fd);
    }
    if (hardware->gpiochip_fd >= 0) {
        (void)close(hardware->gpiochip_fd);
    }
    if (hardware->spi_fd >= 0) {
        (void)close(hardware->spi_fd);
    }
    hardware_context_init(hardware);
}

static bool run_hardware_capture(
    FILE *output,
    const struct capture_config *config,
    struct capture_stats *stats,
    struct hardware_context *hardware)
{
    uint64_t previous_line_seqno = 0;
    bool have_previous_line_seqno = false;

    while (!stop_requested) {
        struct pollfd event_poll;
        int poll_result;
        ssize_t event_bytes;
        size_t event_count;
        struct gpio_v2_line_event events[GPIO_EVENT_BATCH_SIZE];
        const struct gpio_v2_line_event *event;
        struct adxl355_fifo_snapshot snapshot = {0};
        struct adxl355_fifo_xyz fifo_xyz = {0};
        uint8_t post_fifo_entries = 0;
        enum adxl355_fifo_decode_result fifo_decode_result;
        enum adxl355_pairing_result pairing_result;
        struct adxl355_record_values values;

        if (config->max_samples > 0u
            && stats->samples_written >= config->max_samples) {
            (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "max_samples");
            return true;
        }
        memset(&event_poll, 0, sizeof(event_poll));
        event_poll.fd = hardware->gpio_line_fd;
        event_poll.events = POLLIN | POLLPRI;
        poll_result = poll(&event_poll, 1, 250);
        if (poll_result < 0) {
            if (errno == EINTR) {
                continue;
            }
            set_errno_error(stats, "wait for DRDY edge", errno);
            return false;
        }
        if (poll_result == 0) {
            continue;
        }
        if ((event_poll.revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
            set_error(stats, "DRDY GPIO event descriptor reported an error");
            return false;
        }
        event_bytes = read(hardware->gpio_line_fd, events, sizeof(events));
        if (event_bytes < 0) {
            if (errno == EINTR || errno == EAGAIN) {
                continue;
            }
            set_errno_error(stats, "read DRDY edge events", errno);
            return false;
        }
        if (event_bytes == 0
            || (size_t)event_bytes % sizeof(events[0]) != 0u) {
            set_error(stats, "GPIO uAPI v2 returned a truncated DRDY event batch");
            return false;
        }
        event_count = (size_t)event_bytes / sizeof(events[0]);
        pairing_result = adxl355_validate_pairing_snapshot(
            event_count,
            0u,
            3u);
        if (pairing_result == ADXL355_PAIRING_GPIO_BACKLOG) {
            stats->gpio_backlog_events += (uint64_t)event_count;
            set_error(
                stats,
                "multiple historical DRDY events were dequeued together; refusing ambiguous timestamp/sample pairing");
            return false;
        }
        event = &events[0];
        if (event->id != GPIO_V2_LINE_EVENT_RISING_EDGE
            || event->offset != config->drdy_line) {
            set_error(stats, "GPIO uAPI v2 returned an unexpected DRDY event");
            return false;
        }
        memset(&values, 0, sizeof(values));
        values.sample_seq = stats->samples_written;
        values.line_seqno = (uint64_t)event->line_seqno;
        values.drdy_monotonic_ns = event->timestamp_ns;
        if (!validate_line_sequence_before_read(
                values.line_seqno,
                previous_line_seqno,
                have_previous_line_seqno,
                stats)) {
            return false;
        }
        if (!spi_read_fifo_snapshot(hardware, &snapshot)) {
            set_errno_error(stats, "read ADXL355 status/FIFO/temperature snapshot", errno);
            return false;
        }
        if (snapshot.fifo_entries > stats->max_fifo_entries) {
            stats->max_fifo_entries = snapshot.fifo_entries;
        }
        pairing_result = adxl355_validate_pairing_snapshot(
            1u,
            snapshot.status,
            snapshot.fifo_entries);
        if (pairing_result == ADXL355_PAIRING_FIFO_OVERRUN) {
            ++stats->fifo_overruns;
            set_error(stats, "ADXL355 FIFO overrun reported before FIFO sample read");
            return false;
        }
        if (pairing_result == ADXL355_PAIRING_FIFO_DEPTH) {
            ++stats->fifo_protocol_errors;
            if (snapshot.fifo_entries > 3u) {
                set_error(
                    stats,
                    "ADXL355 FIFO backlog exceeds one XYZ set; refusing ambiguous timestamp/sample pairing");
            } else {
                set_error(
                    stats,
                    "ADXL355 FIFO contains fewer than one complete XYZ set for a DRDY edge");
            }
            return false;
        }
        if (!spi_pop_fifo_xyz(
                hardware,
                &fifo_xyz,
                &fifo_decode_result,
                &values.spi_complete_monotonic_ns)) {
            set_errno_error(stats, "pop ADXL355 FIFO XYZ sample", errno);
            return false;
        }
        ++stats->fifo_xyz_sets_drained;
        if (!spi_read_register(
                hardware,
                ADXL355_REG_FIFO_ENTRIES,
                &post_fifo_entries)) {
            set_errno_error(stats, "read ADXL355 post-FIFO entry count", errno);
            return false;
        }
        post_fifo_entries &= ADXL355_FIFO_ENTRIES_MASK;
        if (fifo_decode_result != ADXL355_FIFO_DECODE_OK) {
            ++stats->fifo_protocol_errors;
            switch (fifo_decode_result) {
            case ADXL355_FIFO_DECODE_EMPTY:
                set_error(stats, "ADXL355 FIFO_DATA empty indicator is set");
                break;
            case ADXL355_FIFO_DECODE_MARKER:
                (void)snprintf(
                    stats->error_message,
                    sizeof(stats->error_message),
                    "ADXL355 FIFO_DATA X-axis marker sequence is invalid "
                    "(status=%02x entries=%u post_entries=%u rx0=%02x "
                    "fifo=%02x %02x %02x %02x %02x %02x %02x %02x %02x)",
                    snapshot.status,
                    snapshot.fifo_entries,
                    post_fifo_entries,
                    fifo_xyz.command_response,
                    fifo_xyz.raw_bytes[0],
                    fifo_xyz.raw_bytes[1],
                    fifo_xyz.raw_bytes[2],
                    fifo_xyz.raw_bytes[3],
                    fifo_xyz.raw_bytes[4],
                    fifo_xyz.raw_bytes[5],
                    fifo_xyz.raw_bytes[6],
                    fifo_xyz.raw_bytes[7],
                    fifo_xyz.raw_bytes[8]);
                break;
            case ADXL355_FIFO_DECODE_VIRTUAL_BITS:
                set_error(stats, "ADXL355 FIFO_DATA virtual bits are nonzero");
                break;
            case ADXL355_FIFO_DECODE_OK:
            default:
                set_error(stats, "ADXL355 FIFO_DATA decode failed");
                break;
            }
            return false;
        }
        if (post_fifo_entries != 0u) {
            ++stats->fifo_protocol_errors;
            set_error(
                stats,
                "ADXL355 FIFO gained data before the post-read validation completed");
            return false;
        }
        values.x_raw = fifo_xyz.x_raw;
        values.y_raw = fifo_xyz.y_raw;
        values.z_raw = fifo_xyz.z_raw;
        values.temp_raw = snapshot.temp_raw;
        values.status = snapshot.status;
        values.fifo_entries = snapshot.fifo_entries;
        if (!write_sample(
                output,
                &values,
                stats,
                &previous_line_seqno,
                &have_previous_line_seqno)) {
            set_errno_error(stats, "write sample", errno);
            return false;
        }
    }
    if (config->max_samples > 0u
        && stats->samples_written < config->max_samples) {
        (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "signal_before_target");
        set_error(stats, "terminated before --max-samples was reached");
        return false;
    }
    (void)snprintf(stats->stop_reason, sizeof(stats->stop_reason), "signal");
    return true;
}
#endif

static bool install_signal_handlers(struct capture_stats *stats)
{
    struct sigaction action;

    memset(&action, 0, sizeof(action));
    action.sa_handler = handle_signal;
    action.sa_flags = SA_RESTART;
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGINT, &action, NULL) != 0
        || sigaction(SIGTERM, &action, NULL) != 0) {
        set_errno_error(stats, "install signal handlers", errno);
        return false;
    }
    return true;
}

int main(int argc, char **argv)
{
    struct capture_config config;
    struct capture_stats stats;
    enum parse_result parsed;
    FILE *output = NULL;
    bool run_ok = false;
    bool output_ok = true;
    bool complete = false;
    int exit_code = EXIT_FAILURE;
#if ADXL355_ENABLE_LINUX_HW
    struct hardware_context hardware;

    hardware_context_init(&hardware);
#endif

    memset(&stats, 0, sizeof(stats));
    parsed = parse_arguments(argc, argv, &config, &stats);
    stats.group_delay_ns = config.group_delay_ns;
    if (parsed == PARSE_HELP) {
        print_usage(stdout, argv[0]);
        return EXIT_SUCCESS;
    }
    if (parsed == PARSE_CAPABILITIES) {
        print_capabilities();
        return EXIT_SUCCESS;
    }
    if (parsed == PARSE_ERROR) {
        (void)fprintf(stderr, "adxl355_capture: %s\n", stats.error_message);
        print_usage(stderr, argv[0]);
        if (config.summary_path != NULL) {
            (void)snprintf(stats.stop_reason, sizeof(stats.stop_reason), "argument_error");
            (void)write_summary_json(&config, &stats, false);
        }
        return 2;
    }

    (void)unlink(config.ready_path);
    (void)unlink(config.summary_path);
    if (!install_signal_handlers(&stats)) {
        goto cleanup;
    }
    output = fopen(config.output_path, "wb");
    if (output == NULL) {
        set_errno_error(&stats, "open output file", errno);
        goto cleanup;
    }
    (void)setvbuf(output, NULL, _IOFBF, 1024u * 1024u);

    if (config.mock) {
        if (!clock_now_ns(CLOCK_REALTIME, &stats.start_realtime_ns)
            || !clock_now_ns(CLOCK_MONOTONIC, &stats.start_monotonic_ns)) {
            set_errno_error(&stats, "clock_gettime", errno);
            goto cleanup;
        }
        if (!write_header(output, &config, &stats) || !flush_and_sync(output)) {
            set_errno_error(&stats, "write/sync output header", errno);
            goto cleanup;
        }
        if (!write_ready_json(&config, &stats)) {
            set_errno_error(&stats, "write ready file", errno);
            goto cleanup;
        }
        run_ok = run_mock_capture(output, &config, &stats);
    } else {
#if ADXL355_ENABLE_LINUX_HW
        if (!open_spi(&hardware, &config, &stats)
            || !prepare_sensor(&hardware, &config, &stats)
            || !request_drdy_line(&hardware, &config, &stats)) {
            goto cleanup;
        }
        if (!clock_now_ns(CLOCK_REALTIME, &stats.start_realtime_ns)
            || !clock_now_ns(CLOCK_MONOTONIC, &stats.start_monotonic_ns)) {
            set_errno_error(&stats, "clock_gettime", errno);
            goto cleanup;
        }
        if (!write_header(output, &config, &stats) || !flush_and_sync(output)) {
            set_errno_error(&stats, "write/sync output header", errno);
            goto cleanup;
        }
        if (!write_ready_json(&config, &stats)) {
            set_errno_error(&stats, "write ready file", errno);
            goto cleanup;
        }
        if (!start_sensor(&hardware, &stats)) {
            goto cleanup;
        }
        run_ok = run_hardware_capture(output, &config, &stats, &hardware);
#else
        set_error(
            &stats,
            "real capture is unavailable in this build; use --mock, or build on Linux with GPIO character-device uAPI v2 and spidev headers");
        (void)snprintf(stats.stop_reason, sizeof(stats.stop_reason), "hardware_support_unavailable");
#endif
    }

cleanup:
#if ADXL355_ENABLE_LINUX_HW
    close_hardware(&hardware);
#endif
    if (output != NULL) {
        if (!flush_and_sync(output)) {
            output_ok = false;
            set_errno_error(&stats, "flush/sync output", errno);
        }
        if (fclose(output) != 0) {
            output_ok = false;
            set_errno_error(&stats, "close output", errno);
        }
    }
    if (stats.stop_reason[0] == '\0') {
        (void)snprintf(stats.stop_reason, sizeof(stats.stop_reason), "error");
    }
    if (stats.line_seq_gaps > 0u) {
        set_error(&stats, "DRDY line sequence gap detected");
    }
    if (stats.fifo_overruns > 0u) {
        set_error(&stats, "ADXL355 FIFO overrun detected");
    }
    complete = run_ok
            && output_ok
            && stats.samples_written > 0u
            && stats.error_message[0] == '\0'
            && stats.line_seq_gaps == 0u
            && stats.fifo_overruns == 0u
            && stats.gpio_backlog_events == 0u
            && stats.fifo_protocol_errors == 0u
            && stats.fifo_xyz_mismatches == 0u
            && (config.mock
                || stats.fifo_xyz_sets_drained == stats.samples_written);
    if (run_ok && stats.samples_written == 0u) {
        set_error(&stats, "capture stopped without writing any samples");
        complete = false;
    }
    if (!write_summary_json(&config, &stats, complete)) {
        (void)fprintf(
            stderr,
            "adxl355_capture: cannot write summary '%s': %s\n",
            config.summary_path,
            strerror(errno));
        complete = false;
    }
    if (!complete) {
        (void)unlink(config.ready_path);
    }
    if (!complete) {
        (void)fprintf(
            stderr,
            "adxl355_capture: failed after %" PRIu64 " samples: %s\n",
            stats.samples_written,
            stats.error_message[0] != '\0' ? stats.error_message : "capture incomplete");
    } else {
        exit_code = EXIT_SUCCESS;
    }
    return exit_code;
}
