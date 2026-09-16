CC ?= cc
MOCK_ONLY ?= 0
EXTRA_CPPFLAGS ?=
UNAME_S := $(shell uname -s)
BUILD_DIR := build
PROGRAM := $(BUILD_DIR)/adxl355_capture
UNIT_TEST := $(BUILD_DIR)/test_codec
GPIO_UAPI_V2_PROBE := tests/probe_gpio_uapi_v2.c

CPPFLAGS += -D_POSIX_C_SOURCE=200809L -I.
CPPFLAGS += $(EXTRA_CPPFLAGS)
CFLAGS ?= -O2 -g
CFLAGS += -std=c11 -Wall -Wextra -Wpedantic -Werror

ifneq ($(filter $(MOCK_ONLY),0 1),$(MOCK_ONLY))
$(error MOCK_ONLY must be 0 or 1)
endif

HW_AVAILABLE := 0
HW_DEPENDENCY_MISSING := 0
ifeq ($(UNAME_S),Linux)
ifeq ($(MOCK_ONLY),0)
ifeq ($(origin GPIO_UAPI_V2_AVAILABLE),undefined)
GPIO_UAPI_V2_AVAILABLE := $(shell $(CC) $(CPPFLAGS) $(CFLAGS) -fsyntax-only $(GPIO_UAPI_V2_PROBE) >/dev/null 2>&1 && echo 1 || echo 0)
endif
ifeq ($(GPIO_UAPI_V2_AVAILABLE),1)
HW_AVAILABLE := 1
else
HW_DEPENDENCY_MISSING := 1
endif
endif
endif

CPPFLAGS += -DADXL355_ENABLE_LINUX_HW=$(HW_AVAILABLE)

.PHONY: all check-hw clean test print-hw

all: $(PROGRAM)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

check-hw:
ifeq ($(HW_DEPENDENCY_MISSING),1)
	@echo "Linux hardware build requires GPIO character-device uAPI v2 headers." >&2
	@echo "Install linux-libc-dev, or explicitly use MOCK_ONLY=1 for a mock-only binary." >&2
	@echo "libgpiod 1.x is not used as a fallback because its event API has no kernel line sequence number." >&2
	@exit 1
endif

$(PROGRAM): adxl355_capture.c record_format.c record_format.h adxl355_regs.h | $(BUILD_DIR) check-hw
	$(CC) $(CPPFLAGS) $(CFLAGS) adxl355_capture.c record_format.c $(LDFLAGS) $(LDLIBS) -o $@

$(UNIT_TEST): tests/test_codec.c record_format.c record_format.h adxl355_regs.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/test_codec.c record_format.c $(LDFLAGS) -o $@

test: $(PROGRAM) $(UNIT_TEST)
	$(UNIT_TEST)
	sh tests/test_mock.sh $(PROGRAM)
	sh tests/test_build_contract.sh

print-hw:
	@echo "ADXL355 Linux hardware support: $(HW_AVAILABLE)"
	@echo "GPIO backend: $(if $(filter 1,$(HW_AVAILABLE)),linux-gpio-uapi-v2,unavailable)"
	@if test "$(UNAME_S)" = "Linux" && test "$(HW_AVAILABLE)" != "1"; then \
		if test "$(MOCK_ONLY)" = "1"; then \
			echo "Mock-only build explicitly selected with MOCK_ONLY=1."; \
		else \
			echo "Install Linux GPIO uAPI v2 headers from linux-libc-dev before building."; \
		fi; \
	fi

clean:
	rm -rf $(BUILD_DIR)
