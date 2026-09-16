#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
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

#include "loopback_logic.h"

#ifndef FRAME_TRIGGER_ENABLE_LINUX_GPIO
#define FRAME_TRIGGER_ENABLE_LINUX_GPIO 0
#endif

#if FRAME_TRIGGER_ENABLE_LINUX_GPIO
#include <linux/gpio.h>
#include <sys/ioctl.h>
#include <sys/select.h>

#ifndef GPIO_V2_GET_LINE_IOCTL
#error "Linux GPIO character-device uAPI v2 is unavailable"
#endif
#ifndef GPIO_V2_LINE_SET_VALUES_IOCTL
#error "Linux GPIO character-device uAPI v2 output control is unavailable"
#endif
#endif

#define NS_PER_SECOND UINT64_C(1000000000)
#define NS_PER_MILLISECOND UINT64_C(1000000)
#define NS_PER_MICROSECOND UINT64_C(1000)
#define ERROR_BUFFER_SIZE 512

struct trigger_config {
    const char *events_path;
    const char *summary_path;
    const char *gpiochip_path;
    uint32_t output_line;
    uint32_t loopback_line;
    double frequency_hz;
    uint64_t count;
    uint64_t pulse_width_us;
    uint64_t initial_delay_ms;
    uint64_t period_ns;
    uint64_t pulse_width_ns;
    uint64_t initial_delay_ns;
    uint64_t final_schedule_offset_ns;
    bool has_loopback;
    bool mock;
};

struct trigger_event {
    uint64_t sequence;
    uint64_t scheduled_monotonic_ns;
    uint64_t asserted_monotonic_ns;
    uint64_t deasserted_monotonic_ns;
    uint64_t loopback_monotonic_ns;
    bool has_loopback_timestamp;
};

struct run_result {
    const char *status;
    uint64_t emitted_count;
    uint64_t observed_count;
    uint64_t matched_loopback_count;
    int exit_code;
};

static volatile sig_atomic_t stop_requested = 0;

static void handle_stop_signal(int signal_number)
{
    (void)signal_number;
    stop_requested = 1;
}

static void set_error(char *buffer, size_t buffer_size, const char *message)
{
    if (buffer_size == 0) {
        return;
    }
    (void)snprintf(buffer, buffer_size, "%s", message);
}

static void set_errno_error(char *buffer, size_t buffer_size, const char *operation)
{
    if (buffer_size == 0) {
        return;
    }
    (void)snprintf(buffer, buffer_size, "%s: %s", operation, strerror(errno));
}

static bool checked_add_u64(uint64_t left, uint64_t right, uint64_t *result)
{
    if (UINT64_MAX - left < right) {
        return false;
    }
    *result = left + right;
    return true;
}

static bool checked_multiply_u64(uint64_t left, uint64_t right, uint64_t *result)
{
    if (left != 0 && right > UINT64_MAX / left) {
        return false;
    }
    *result = left * right;
    return true;
}

static bool parse_u64(const char *text, uint64_t *value)
{
    char *end = NULL;
    unsigned long long parsed;
    const unsigned char *cursor = (const unsigned char *)text;

    if (text == NULL || *text == '\0') {
        return false;
    }
    while (*cursor != '\0') {
        if (*cursor < '0' || *cursor > '9') {
            return false;
        }
        cursor++;
    }

    errno = 0;
    parsed = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        return false;
    }
    *value = (uint64_t)parsed;
    return true;
}

static bool parse_u32(const char *text, uint32_t *value)
{
    uint64_t parsed;

    if (!parse_u64(text, &parsed) || parsed > UINT32_MAX) {
        return false;
    }
    *value = (uint32_t)parsed;
    return true;
}

static bool parse_positive_double(const char *text, double *value)
{
    char *end = NULL;
    double parsed;

    if (text == NULL || *text == '\0') {
        return false;
    }
    errno = 0;
    parsed = strtod(text, &end);
    if (errno != 0 || end == text || *end != '\0' || !isfinite(parsed) || parsed <= 0.0) {
        return false;
    }
    *value = parsed;
    return true;
}

static int64_t monotonic_ns(void)
{
    struct timespec timestamp;

    if (clock_gettime(CLOCK_MONOTONIC, &timestamp) != 0) {
        return -1;
    }
    if (timestamp.tv_sec < 0) {
        errno = ERANGE;
        return -1;
    }
    return (int64_t)((uint64_t)timestamp.tv_sec * NS_PER_SECOND +
                     (uint64_t)timestamp.tv_nsec);
}

static struct timespec ns_to_timespec(uint64_t nanoseconds)
{
    struct timespec result;

    result.tv_sec = (time_t)(nanoseconds / NS_PER_SECOND);
    result.tv_nsec = (long)(nanoseconds % NS_PER_SECOND);
    return result;
}

static int sleep_until_monotonic(uint64_t deadline_ns)
{
#if defined(__linux__)
    struct timespec deadline = ns_to_timespec(deadline_ns);

    for (;;) {
        int result = clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &deadline, NULL);
        if (result == 0) {
            return 0;
        }
        if (result == EINTR) {
            if (stop_requested) {
                return 1;
            }
            continue;
        }
        errno = result;
        return -1;
    }
#else
    for (;;) {
        int64_t now = monotonic_ns();
        struct timespec remaining;

        if (now < 0) {
            return -1;
        }
        if ((uint64_t)now >= deadline_ns) {
            return 0;
        }
        remaining = ns_to_timespec(deadline_ns - (uint64_t)now);
        if (nanosleep(&remaining, NULL) == 0) {
            return 0;
        }
        if (errno == EINTR) {
            if (stop_requested) {
                return 1;
            }
            continue;
        }
        return -1;
    }
#endif
}

static void print_usage(FILE *stream, const char *program)
{
    (void)fprintf(
        stream,
        "Usage: %s --events PATH --summary PATH --gpiochip PATH "
        "--output-line N --frequency-hz FLOAT --count N --pulse-width-us N "
        "--initial-delay-ms N [--loopback-line N] [--mock]\n",
        program);
}

enum required_argument_bit {
    ARG_EVENTS = 1U << 0,
    ARG_SUMMARY = 1U << 1,
    ARG_GPIOCHIP = 1U << 2,
    ARG_OUTPUT_LINE = 1U << 3,
    ARG_FREQUENCY = 1U << 4,
    ARG_COUNT = 1U << 5,
    ARG_PULSE_WIDTH = 1U << 6,
    ARG_INITIAL_DELAY = 1U << 7,
    ARG_LOOPBACK = 1U << 8,
    ARG_MOCK = 1U << 9
};

static bool mark_once(unsigned int *seen, unsigned int bit, const char *name,
                      char *error, size_t error_size)
{
    if ((*seen & bit) != 0U) {
        (void)snprintf(error, error_size, "duplicate argument: %s", name);
        return false;
    }
    *seen |= bit;
    return true;
}

static bool require_value(int argc, char **argv, int *index, const char **value,
                          char *error, size_t error_size)
{
    if (*index + 1 >= argc) {
        (void)snprintf(error, error_size, "missing value for %s", argv[*index]);
        return false;
    }
    *index += 1;
    *value = argv[*index];
    return true;
}

static bool finalize_config(struct trigger_config *config, char *error, size_t error_size)
{
    long double period;
    uint64_t schedule_span;
    uint64_t final_offset;

    period = (long double)NS_PER_SECOND / (long double)config->frequency_hz;
    if (period < 1.0L || period > (long double)INT64_MAX) {
        set_error(error, error_size, "frequency-hz produces an unsupported period");
        return false;
    }
    config->period_ns = (uint64_t)llroundl(period);
    if (config->period_ns == 0) {
        set_error(error, error_size, "frequency-hz produces a zero nanosecond period");
        return false;
    }
    if (!checked_multiply_u64(config->pulse_width_us, NS_PER_MICROSECOND,
                              &config->pulse_width_ns) ||
        config->pulse_width_ns == 0) {
        set_error(error, error_size, "pulse-width-us must be positive and representable");
        return false;
    }
    if (config->pulse_width_ns >= config->period_ns) {
        set_error(error, error_size, "pulse-width-us must be shorter than one trigger period");
        return false;
    }
    if (!checked_multiply_u64(config->initial_delay_ms, NS_PER_MILLISECOND,
                              &config->initial_delay_ns)) {
        set_error(error, error_size, "initial-delay-ms is too large");
        return false;
    }
    if (config->count > SIZE_MAX / sizeof(struct trigger_event)) {
        set_error(error, error_size, "count is too large for this process");
        return false;
    }
    if (!checked_multiply_u64(config->count - 1, config->period_ns, &schedule_span) ||
        !checked_add_u64(config->initial_delay_ns, schedule_span, &final_offset) ||
        !checked_add_u64(final_offset, config->pulse_width_ns, &final_offset) ||
        final_offset > INT64_MAX) {
        set_error(error, error_size, "trigger schedule duration overflows the monotonic clock");
        return false;
    }
    config->final_schedule_offset_ns = final_offset;
    if (config->has_loopback && config->loopback_line == config->output_line) {
        set_error(error, error_size, "loopback-line must differ from output-line");
        return false;
    }
    if (config->mock && config->has_loopback) {
        set_error(error, error_size,
                  "--mock cannot use --loopback-line; mock mode never fabricates kernel edges");
        return false;
    }
#if !FRAME_TRIGGER_ENABLE_LINUX_GPIO
    if (!config->mock) {
        set_error(error, error_size,
                  "hardware mode is unavailable in this build; Linux GPIO character-device uAPI v2 is required, or use --mock");
        return false;
    }
#endif
    return true;
}

static bool parse_arguments(int argc, char **argv, struct trigger_config *config,
                            char *error, size_t error_size)
{
    const unsigned int required = ARG_EVENTS | ARG_SUMMARY | ARG_GPIOCHIP |
                                  ARG_OUTPUT_LINE | ARG_FREQUENCY | ARG_COUNT |
                                  ARG_PULSE_WIDTH | ARG_INITIAL_DELAY;
    unsigned int seen = 0;
    int index;

    memset(config, 0, sizeof(*config));

    for (index = 1; index < argc; index++) {
        const char *argument = argv[index];
        const char *value = NULL;

        if (strcmp(argument, "--events") == 0) {
            if (!mark_once(&seen, ARG_EVENTS, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size)) {
                return false;
            }
            config->events_path = value;
        } else if (strcmp(argument, "--summary") == 0) {
            if (!mark_once(&seen, ARG_SUMMARY, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size)) {
                return false;
            }
            config->summary_path = value;
        } else if (strcmp(argument, "--gpiochip") == 0) {
            if (!mark_once(&seen, ARG_GPIOCHIP, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size)) {
                return false;
            }
            config->gpiochip_path = value;
        } else if (strcmp(argument, "--output-line") == 0) {
            if (!mark_once(&seen, ARG_OUTPUT_LINE, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_u32(value, &config->output_line)) {
                set_error(error, error_size, "output-line must be an unsigned 32-bit integer");
                return false;
            }
        } else if (strcmp(argument, "--loopback-line") == 0) {
            if (!mark_once(&seen, ARG_LOOPBACK, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_u32(value, &config->loopback_line)) {
                set_error(error, error_size, "loopback-line must be an unsigned 32-bit integer");
                return false;
            }
            config->has_loopback = true;
        } else if (strcmp(argument, "--frequency-hz") == 0) {
            if (!mark_once(&seen, ARG_FREQUENCY, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_positive_double(value, &config->frequency_hz)) {
                set_error(error, error_size, "frequency-hz must be finite and positive");
                return false;
            }
        } else if (strcmp(argument, "--count") == 0) {
            if (!mark_once(&seen, ARG_COUNT, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_u64(value, &config->count) || config->count == 0) {
                set_error(error, error_size, "count must be a positive integer");
                return false;
            }
        } else if (strcmp(argument, "--pulse-width-us") == 0) {
            if (!mark_once(&seen, ARG_PULSE_WIDTH, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_u64(value, &config->pulse_width_us) || config->pulse_width_us == 0) {
                set_error(error, error_size, "pulse-width-us must be a positive integer");
                return false;
            }
        } else if (strcmp(argument, "--initial-delay-ms") == 0) {
            if (!mark_once(&seen, ARG_INITIAL_DELAY, argument, error, error_size) ||
                !require_value(argc, argv, &index, &value, error, error_size) ||
                !parse_u64(value, &config->initial_delay_ms)) {
                set_error(error, error_size, "initial-delay-ms must be a non-negative integer");
                return false;
            }
        } else if (strcmp(argument, "--mock") == 0) {
            if (!mark_once(&seen, ARG_MOCK, argument, error, error_size)) {
                return false;
            }
            config->mock = true;
        } else if (strcmp(argument, "--help") == 0 || strcmp(argument, "-h") == 0) {
            print_usage(stdout, argv[0]);
            exit(EXIT_SUCCESS);
        } else {
            (void)snprintf(error, error_size, "unknown argument: %s", argument);
            return false;
        }
    }

    if ((seen & required) != required) {
        set_error(error, error_size, "one or more required arguments are missing");
        return false;
    }
    if (config->events_path[0] == '\0' || config->summary_path[0] == '\0' ||
        config->gpiochip_path[0] == '\0') {
        set_error(error, error_size, "path arguments must not be empty");
        return false;
    }
    return finalize_config(config, error, error_size);
}

static char *temporary_path_for(const char *destination)
{
    size_t length = strlen(destination) + 64;
    char *temporary = malloc(length);

    if (temporary == NULL) {
        return NULL;
    }
    (void)snprintf(temporary, length, "%s.tmp.%ld", destination, (long)getpid());
    return temporary;
}

static int open_temporary_file(const char *destination, char **temporary_path,
                               FILE **stream, char *error, size_t error_size)
{
    int descriptor;

    *temporary_path = temporary_path_for(destination);
    if (*temporary_path == NULL) {
        set_error(error, error_size, "failed to allocate a temporary path");
        return -1;
    }
    descriptor = open(*temporary_path, O_WRONLY | O_CREAT | O_EXCL, 0644);
    if (descriptor < 0) {
        set_errno_error(error, error_size, "failed to create temporary output");
        free(*temporary_path);
        *temporary_path = NULL;
        return -1;
    }
    *stream = fdopen(descriptor, "w");
    if (*stream == NULL) {
        set_errno_error(error, error_size, "failed to open temporary output stream");
        (void)close(descriptor);
        (void)unlink(*temporary_path);
        free(*temporary_path);
        *temporary_path = NULL;
        return -1;
    }
    return 0;
}

static int commit_temporary_file(FILE *stream, char *temporary_path,
                                 const char *destination, char *error,
                                 size_t error_size)
{
    int descriptor = fileno(stream);

    if (fflush(stream) != 0 || fsync(descriptor) != 0) {
        set_errno_error(error, error_size, "failed to flush output");
        (void)fclose(stream);
        (void)unlink(temporary_path);
        free(temporary_path);
        return -1;
    }
    if (fclose(stream) != 0) {
        set_errno_error(error, error_size, "failed to close output");
        (void)unlink(temporary_path);
        free(temporary_path);
        return -1;
    }
    if (rename(temporary_path, destination) != 0) {
        set_errno_error(error, error_size, "failed to atomically publish output");
        (void)unlink(temporary_path);
        free(temporary_path);
        return -1;
    }
    free(temporary_path);
    return 0;
}

static int write_events_csv(const struct trigger_config *config,
                            const struct trigger_event *events,
                            uint64_t emitted_count, char *error, size_t error_size)
{
    FILE *stream = NULL;
    char *temporary_path = NULL;
    uint64_t index;

    if (open_temporary_file(config->events_path, &temporary_path, &stream,
                            error, error_size) != 0) {
        return -1;
    }
    if (fprintf(stream,
                "sequence,scheduled_monotonic_ns,asserted_monotonic_ns,"
                "deasserted_monotonic_ns,loopback_monotonic_ns\n") < 0) {
        set_errno_error(error, error_size, "failed to write events header");
        (void)fclose(stream);
        (void)unlink(temporary_path);
        free(temporary_path);
        return -1;
    }
    for (index = 0; index < emitted_count; index++) {
        const struct trigger_event *event = &events[index];
        int result;

        result = fprintf(stream, "%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",",
                         event->sequence,
                         event->scheduled_monotonic_ns,
                         event->asserted_monotonic_ns,
                         event->deasserted_monotonic_ns);
        if (result >= 0 && event->has_loopback_timestamp) {
            result = fprintf(stream, "%" PRIu64, event->loopback_monotonic_ns);
        }
        if (result < 0 || fputc('\n', stream) == EOF) {
            set_errno_error(error, error_size, "failed to write trigger event");
            (void)fclose(stream);
            (void)unlink(temporary_path);
            free(temporary_path);
            return -1;
        }
    }
    return commit_temporary_file(stream, temporary_path, config->events_path,
                                 error, error_size);
}

static int write_json_string(FILE *stream, const char *text)
{
    const unsigned char *cursor = (const unsigned char *)text;

    if (fputc('"', stream) == EOF) {
        return -1;
    }
    while (*cursor != '\0') {
        unsigned char character = *cursor++;
        switch (character) {
        case '"':
            if (fputs("\\\"", stream) == EOF) return -1;
            break;
        case '\\':
            if (fputs("\\\\", stream) == EOF) return -1;
            break;
        case '\b':
            if (fputs("\\b", stream) == EOF) return -1;
            break;
        case '\f':
            if (fputs("\\f", stream) == EOF) return -1;
            break;
        case '\n':
            if (fputs("\\n", stream) == EOF) return -1;
            break;
        case '\r':
            if (fputs("\\r", stream) == EOF) return -1;
            break;
        case '\t':
            if (fputs("\\t", stream) == EOF) return -1;
            break;
        default:
            if (character < 0x20U) {
                if (fprintf(stream, "\\u%04x", (unsigned int)character) < 0) return -1;
            } else if (fputc((int)character, stream) == EOF) {
                return -1;
            }
            break;
        }
    }
    return fputc('"', stream) == EOF ? -1 : 0;
}

static int write_summary_json(const struct trigger_config *config,
                              const struct run_result *result,
                              const char *error_detail, char *error,
                              size_t error_size)
{
    FILE *stream = NULL;
    char *temporary_path = NULL;
    uint64_t missed_loopback = 0;
    const char *timestamp_quality = "userspace_set_completed";

    if (config->has_loopback) {
        if (result->matched_loopback_count < result->emitted_count) {
            missed_loopback = result->emitted_count - result->matched_loopback_count;
        }
        if (result->observed_count > 0) {
            timestamp_quality = "kernel_loopback_edge";
        }
    }

    if (open_temporary_file(config->summary_path, &temporary_path, &stream,
                            error, error_size) != 0) {
        return -1;
    }

    if (fprintf(stream,
                "{\n"
                "  \"schema_version\": 1,\n"
                "  \"status\": \"%s\",\n"
                "  \"requested_count\": %" PRIu64 ",\n"
                "  \"emitted_count\": %" PRIu64 ",\n"
                "  \"observed_count\": %" PRIu64 ",\n"
                "  \"missed_loopback\": %" PRIu64 ",\n"
                "  \"timestamp_quality\": \"%s\",\n"
                "  \"clock\": \"CLOCK_MONOTONIC\",\n"
                "  \"configuration\": {\n"
                "    \"gpiochip\": ",
                result->status,
                config->count,
                result->emitted_count,
                result->observed_count,
                missed_loopback,
                timestamp_quality) < 0 ||
        write_json_string(stream, config->gpiochip_path) != 0 ||
        fprintf(stream,
                ",\n"
                "    \"output_line\": %" PRIu32 ",\n"
                "    \"loopback_line\": ",
                config->output_line) < 0) {
        goto write_failure;
    }
    if (config->has_loopback) {
        if (fprintf(stream, "%" PRIu32, config->loopback_line) < 0) {
            goto write_failure;
        }
    } else if (fputs("null", stream) == EOF) {
        goto write_failure;
    }
    if (fprintf(stream,
                ",\n"
                "    \"frequency_hz\": %.17g,\n"
                "    \"count\": %" PRIu64 ",\n"
                "    \"pulse_width_us\": %" PRIu64 ",\n"
                "    \"initial_delay_ms\": %" PRIu64 ",\n"
                "    \"period_ns\": %" PRIu64 ",\n"
                "    \"mock\": %s\n"
                "  },\n"
                "  \"error\": ",
                config->frequency_hz,
                config->count,
                config->pulse_width_us,
                config->initial_delay_ms,
                config->period_ns,
                config->mock ? "true" : "false") < 0) {
        goto write_failure;
    }
    if (error_detail != NULL && error_detail[0] != '\0') {
        if (write_json_string(stream, error_detail) != 0) {
            goto write_failure;
        }
    } else if (fputs("null", stream) == EOF) {
        goto write_failure;
    }
    if (fputs("\n}\n", stream) == EOF) {
        goto write_failure;
    }
    return commit_temporary_file(stream, temporary_path, config->summary_path,
                                 error, error_size);

write_failure:
    set_errno_error(error, error_size, "failed to write summary JSON");
    (void)fclose(stream);
    (void)unlink(temporary_path);
    free(temporary_path);
    return -1;
}

#if FRAME_TRIGGER_ENABLE_LINUX_GPIO
struct gpio_context {
    int chip_fd;
    int output_fd;
    int loopback_fd;
    uint32_t output_line;
    uint32_t loopback_line;
    bool has_loopback;
};

static void gpio_context_init(struct gpio_context *context)
{
    memset(context, 0, sizeof(*context));
    context->chip_fd = -1;
    context->output_fd = -1;
    context->loopback_fd = -1;
}

static int gpio_write_output(int output_fd, bool active)
{
    struct gpio_v2_line_values values;

    memset(&values, 0, sizeof(values));
    values.mask = UINT64_C(1);
    values.bits = active ? UINT64_C(1) : UINT64_C(0);
    return ioctl(output_fd, GPIO_V2_LINE_SET_VALUES_IOCTL, &values);
}

static void gpio_force_low(struct gpio_context *context)
{
    if (context->output_fd >= 0) {
        (void)gpio_write_output(context->output_fd, false);
    }
}

static void gpio_context_close(struct gpio_context *context)
{
    gpio_force_low(context);
    if (context->loopback_fd >= 0) {
        (void)close(context->loopback_fd);
    }
    if (context->output_fd >= 0) {
        (void)close(context->output_fd);
    }
    if (context->chip_fd >= 0) {
        (void)close(context->chip_fd);
    }
    gpio_context_init(context);
}

static void set_gpio_request_error(char *error, size_t error_size,
                                   const char *operation)
{
    if (errno == ENOTTY) {
        set_error(
            error,
            error_size,
            "GPIO device/kernel lacks character-device uAPI v2; refusing userspace timestamp fallback");
    } else {
        set_errno_error(error, error_size, operation);
    }
}

static int gpio_context_open(struct gpio_context *context,
                             const struct trigger_config *config,
                             char *error, size_t error_size)
{
    struct gpio_v2_line_request output_request;
    struct gpio_v2_line_request loopback_request;
    int descriptor_flags;
    int result = -1;

    gpio_context_init(context);
    context->output_line = config->output_line;
    context->loopback_line = config->loopback_line;
    context->has_loopback = config->has_loopback;

    context->chip_fd = open(config->gpiochip_path, O_RDONLY | O_CLOEXEC);
    if (context->chip_fd < 0) {
        set_errno_error(error, error_size, "failed to open gpiochip");
        goto cleanup;
    }

    memset(&output_request, 0, sizeof(output_request));
    output_request.offsets[0] = config->output_line;
    output_request.num_lines = 1U;
    output_request.config.flags = GPIO_V2_LINE_FLAG_OUTPUT;
    (void)snprintf(
        output_request.consumer,
        sizeof(output_request.consumer),
        "mmwave-frame-trigger-out");
    if (ioctl(context->chip_fd, GPIO_V2_GET_LINE_IOCTL, &output_request) != 0) {
        set_gpio_request_error(
            error, error_size, "failed to request trigger output with GPIO uAPI v2");
        goto cleanup;
    }
    context->output_fd = output_request.fd;
    if (gpio_write_output(context->output_fd, false) != 0) {
        set_errno_error(error, error_size, "failed to initialize trigger output LOW");
        goto cleanup;
    }

    if (config->has_loopback) {
        memset(&loopback_request, 0, sizeof(loopback_request));
        loopback_request.offsets[0] = config->loopback_line;
        loopback_request.num_lines = 1U;
        loopback_request.event_buffer_size = 64U;
        loopback_request.config.flags = GPIO_V2_LINE_FLAG_INPUT
                                      | GPIO_V2_LINE_FLAG_EDGE_RISING;
        (void)snprintf(
            loopback_request.consumer,
            sizeof(loopback_request.consumer),
            "mmwave-frame-trigger-loopback");
        /*
         * Omitting REALTIME and HTE event-clock flags selects the GPIO v2
         * ABI's default CLOCK_MONOTONIC kernel edge timestamp.
         */
        if (ioctl(context->chip_fd, GPIO_V2_GET_LINE_IOCTL,
                  &loopback_request) != 0) {
            set_gpio_request_error(
                error, error_size,
                "failed to request loopback input with GPIO uAPI v2");
            goto cleanup;
        }
        context->loopback_fd = loopback_request.fd;
        descriptor_flags = fcntl(context->loopback_fd, F_GETFL);
        if (descriptor_flags < 0 ||
            fcntl(context->loopback_fd, F_SETFL,
                  descriptor_flags | O_NONBLOCK) != 0) {
            set_errno_error(error, error_size,
                            "failed to configure loopback event descriptor");
            goto cleanup;
        }
    }
    result = 0;

cleanup:
    if (result != 0) gpio_context_close(context);
    return result;
}

static int gpio_set_output(struct gpio_context *context, bool active,
                           char *error, size_t error_size)
{
    if (gpio_write_output(context->output_fd, active) != 0) {
        set_errno_error(error, error_size,
                        active ? "failed to assert trigger output"
                               : "failed to deassert trigger output");
        return -1;
    }
    return 0;
}

static int collect_loopback_until(struct gpio_context *context,
                                  uint64_t current_schedule_ns,
                                  uint64_t deadline_ns,
                                  struct trigger_event *record,
                                  uint64_t *observed_count,
                                  uint64_t *matched_count,
                                  char *error, size_t error_size)
{
    while (!stop_requested) {
        int64_t now = monotonic_ns();
        int wait_result;
        fd_set read_fds;
        struct timespec timeout;

        if (now < 0) {
            set_errno_error(error, error_size, "failed to read monotonic clock");
            return -1;
        }
        if ((uint64_t)now >= deadline_ns) {
            return 0;
        }
        FD_ZERO(&read_fds);
        FD_SET(context->loopback_fd, &read_fds);
        timeout = ns_to_timespec(deadline_ns - (uint64_t)now);
        wait_result = pselect(
            context->loopback_fd + 1,
            &read_fds,
            NULL,
            NULL,
            &timeout,
            NULL);
        if (wait_result < 0) {
            if (errno == EINTR && stop_requested) {
                return 0;
            }
            set_errno_error(error, error_size, "failed while waiting for loopback edge");
            return -1;
        }
        if (wait_result == 0) {
            return 0;
        }
        for (;;) {
            struct gpio_v2_line_event events[64];
            ssize_t event_bytes = read(
                context->loopback_fd, events, sizeof(events));
            size_t event_count;
            size_t index;

            if (event_bytes < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    break;
                }
                if (errno == EINTR) {
                    continue;
                }
                set_errno_error(error, error_size,
                                "failed to read loopback edge");
                return -1;
            }
            if (event_bytes == 0 ||
                (size_t)event_bytes % sizeof(events[0]) != 0U) {
                set_error(
                    error,
                    error_size,
                    "GPIO uAPI v2 returned a truncated loopback event batch");
                return -1;
            }
            event_count = (size_t)event_bytes / sizeof(events[0]);
            for (index = 0; index < event_count; index++) {
                const struct gpio_v2_line_event *event = &events[index];

                if (event->id != GPIO_V2_LINE_EVENT_RISING_EDGE ||
                    event->offset != context->loopback_line) {
                    set_error(
                        error,
                        error_size,
                        "GPIO uAPI v2 returned an unexpected loopback event");
                    return -1;
                }
                frame_trigger_record_loopback_edge(
                    event->timestamp_ns,
                    current_schedule_ns,
                    deadline_ns,
                    &record->has_loopback_timestamp,
                    &record->loopback_monotonic_ns,
                    observed_count,
                    matched_count);
            }
        }
    }
    return 0;
}
#endif

static struct run_result run_mock(const struct trigger_config *config,
                                  struct trigger_event *events,
                                  char *error, size_t error_size)
{
    struct run_result result = {"ok", 0, 0, 0, 0};
    int64_t now = monotonic_ns();
    uint64_t first_schedule;
    uint64_t index;

    if (now < 0) {
        set_errno_error(error, error_size, "failed to read monotonic clock");
        result.status = "error";
        result.exit_code = 1;
        return result;
    }
    if ((uint64_t)now > (uint64_t)INT64_MAX - config->final_schedule_offset_ns ||
        !checked_add_u64((uint64_t)now, config->initial_delay_ns,
                         &first_schedule)) {
        set_error(error, error_size, "mock trigger schedule exceeds the monotonic clock range");
        result.status = "error";
        result.exit_code = 1;
        return result;
    }

    for (index = 0; index < config->count; index++) {
        struct trigger_event *record = &events[index];
        uint64_t offset;
        uint64_t deassert_schedule;
        int sleep_result;
        int64_t timestamp;

        if (stop_requested) break;
        if (!checked_multiply_u64(index, config->period_ns, &offset) ||
            !checked_add_u64(first_schedule, offset,
                             &record->scheduled_monotonic_ns)) {
            set_error(error, error_size, "mock trigger schedule overflowed");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->sequence = index;

        sleep_result = sleep_until_monotonic(record->scheduled_monotonic_ns);
        if (sleep_result < 0) {
            set_errno_error(error, error_size, "failed to wait for mock trigger assertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        if (sleep_result > 0 || stop_requested) break;
        timestamp = monotonic_ns();
        if (timestamp < 0) {
            set_errno_error(error, error_size, "failed to timestamp mock trigger assertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->asserted_monotonic_ns = (uint64_t)timestamp;
        /*
         * Assertions follow the absolute schedule.  Deassertion is relative to
         * the completed assertion so scheduler lateness cannot collapse an
         * active-high pulse to zero width.
         */
        if (!checked_add_u64(record->asserted_monotonic_ns,
                             config->pulse_width_ns, &deassert_schedule)) {
            set_error(error, error_size, "mock trigger deassertion schedule overflowed");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        sleep_result = sleep_until_monotonic(deassert_schedule);
        timestamp = monotonic_ns();
        if (timestamp < 0) {
            set_errno_error(error, error_size, "failed to timestamp mock trigger deassertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->deasserted_monotonic_ns = (uint64_t)timestamp;
        result.emitted_count += 1;
        if (sleep_result < 0) {
            set_errno_error(error, error_size, "failed to wait for mock trigger deassertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        if (sleep_result > 0 || stop_requested) break;
    }

    if (stop_requested && result.exit_code == 0) {
        result.status = "interrupted";
        result.exit_code = 130;
    } else if (result.exit_code == 0 && result.emitted_count != config->count) {
        set_error(error, error_size, "mock emitted count differs from requested count");
        result.status = "error";
        result.exit_code = 1;
    }
    return result;
}

#if FRAME_TRIGGER_ENABLE_LINUX_GPIO
static struct run_result run_hardware(const struct trigger_config *config,
                                      struct trigger_event *events,
                                      char *error, size_t error_size)
{
    struct run_result result = {"ok", 0, 0, 0, 0};
    struct gpio_context gpio;
    int64_t now;
    uint64_t first_schedule;
    uint64_t index;

    gpio_context_init(&gpio);
    if (gpio_context_open(&gpio, config, error, error_size) != 0) {
        result.status = "error";
        result.exit_code = 1;
        return result;
    }
    now = monotonic_ns();
    if (now < 0) {
        set_errno_error(error, error_size, "failed to read monotonic clock");
        result.status = "error";
        result.exit_code = 1;
        goto cleanup;
    }
    if ((uint64_t)now > (uint64_t)INT64_MAX - config->final_schedule_offset_ns ||
        !checked_add_u64((uint64_t)now, config->initial_delay_ns,
                         &first_schedule)) {
        set_error(error, error_size, "hardware trigger schedule exceeds the monotonic clock range");
        result.status = "error";
        result.exit_code = 1;
        goto cleanup;
    }

    for (index = 0; index < config->count; index++) {
        struct trigger_event *record = &events[index];
        uint64_t offset;
        uint64_t deassert_schedule;
        int sleep_result;
        int64_t timestamp;

        if (stop_requested) break;
        if (!checked_multiply_u64(index, config->period_ns, &offset) ||
            !checked_add_u64(first_schedule, offset,
                             &record->scheduled_monotonic_ns)) {
            set_error(error, error_size, "hardware trigger schedule overflowed");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->sequence = index;
        sleep_result = sleep_until_monotonic(record->scheduled_monotonic_ns);
        if (sleep_result < 0) {
            set_errno_error(error, error_size, "failed to wait for trigger assertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        if (sleep_result > 0 || stop_requested) break;
        if (gpio_set_output(&gpio, true, error, error_size) != 0) {
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        timestamp = monotonic_ns();
        if (timestamp < 0) {
            set_errno_error(error, error_size, "failed to timestamp trigger assertion");
            gpio_force_low(&gpio);
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->asserted_monotonic_ns = (uint64_t)timestamp;
        /*
         * Assertions follow the absolute schedule.  Deassertion is relative to
         * the completed GPIO set so scheduler lateness cannot collapse the
         * electrical pulse.
         */
        if (!checked_add_u64(record->asserted_monotonic_ns,
                             config->pulse_width_ns, &deassert_schedule)) {
            set_error(error, error_size,
                      "hardware trigger deassertion schedule overflowed");
            gpio_force_low(&gpio);
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        if (config->has_loopback &&
            collect_loopback_until(&gpio, record->scheduled_monotonic_ns,
                                   deassert_schedule, record,
                                   &result.observed_count,
                                   &result.matched_loopback_count,
                                   error, error_size) != 0) {
            gpio_force_low(&gpio);
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        sleep_result = sleep_until_monotonic(deassert_schedule);
        if (gpio_set_output(&gpio, false, error, error_size) != 0) {
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        timestamp = monotonic_ns();
        if (timestamp < 0) {
            set_errno_error(error, error_size, "failed to timestamp trigger deassertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        record->deasserted_monotonic_ns = (uint64_t)timestamp;
        result.emitted_count += 1;
        if (sleep_result < 0) {
            set_errno_error(error, error_size, "failed to wait for trigger deassertion");
            result.status = "error";
            result.exit_code = 1;
            break;
        }
        if (sleep_result > 0 || stop_requested) break;
    }

    if (stop_requested && result.exit_code == 0) {
        result.status = "interrupted";
        result.exit_code = 130;
    } else if (result.exit_code == 0 && result.emitted_count != config->count) {
        set_error(error, error_size, "emitted count differs from requested count");
        result.status = "error";
        result.exit_code = 1;
    } else if (result.exit_code == 0 && config->has_loopback &&
               (result.observed_count != config->count ||
                result.matched_loopback_count != config->count)) {
        set_error(error, error_size,
                  "kernel loopback edge count differs from requested count");
        result.status = "error";
        result.exit_code = 1;
    }

cleanup:
    gpio_context_close(&gpio);
    return result;
}
#endif

static int install_signal_handlers(char *error, size_t error_size)
{
    struct sigaction action;

    memset(&action, 0, sizeof(action));
    action.sa_handler = handle_stop_signal;
    if (sigemptyset(&action.sa_mask) != 0 ||
        sigaction(SIGINT, &action, NULL) != 0 ||
        sigaction(SIGTERM, &action, NULL) != 0) {
        set_errno_error(error, error_size, "failed to install signal handlers");
        return -1;
    }
    return 0;
}

int main(int argc, char **argv)
{
    struct trigger_config config;
    struct trigger_event *events;
    struct run_result result;
    char run_error[ERROR_BUFFER_SIZE] = {0};
    char write_error[ERROR_BUFFER_SIZE] = {0};

    if (!parse_arguments(argc, argv, &config, run_error, sizeof(run_error))) {
        (void)fprintf(stderr, "frame_trigger: %s\n", run_error);
        print_usage(stderr, argv[0]);
        return 2;
    }
    if (install_signal_handlers(run_error, sizeof(run_error)) != 0) {
        (void)fprintf(stderr, "frame_trigger: %s\n", run_error);
        return 1;
    }
    events = calloc((size_t)config.count, sizeof(*events));
    if (events == NULL) {
        (void)fprintf(stderr, "frame_trigger: failed to allocate event records\n");
        return 1;
    }

    if (config.mock) {
        result = run_mock(&config, events, run_error, sizeof(run_error));
    } else {
#if FRAME_TRIGGER_ENABLE_LINUX_GPIO
        result = run_hardware(&config, events, run_error, sizeof(run_error));
#else
        result.status = "error";
        result.emitted_count = 0;
        result.observed_count = 0;
        result.matched_loopback_count = 0;
        result.exit_code = 1;
        set_error(run_error, sizeof(run_error), "hardware support is not compiled in");
#endif
    }

    if (write_events_csv(&config, events, result.emitted_count,
                         write_error, sizeof(write_error)) != 0) {
        (void)fprintf(stderr, "frame_trigger: %s\n", write_error);
        if (result.exit_code == 0) {
            result.status = "error";
            result.exit_code = 1;
            set_error(run_error, sizeof(run_error), write_error);
        }
    }
    write_error[0] = '\0';
    if (write_summary_json(&config, &result, run_error,
                           write_error, sizeof(write_error)) != 0) {
        (void)fprintf(stderr, "frame_trigger: %s\n", write_error);
        result.exit_code = result.exit_code == 0 ? 1 : result.exit_code;
    }
    if (run_error[0] != '\0') {
        (void)fprintf(stderr, "frame_trigger: %s\n", run_error);
    }
    free(events);
    return result.exit_code;
}
