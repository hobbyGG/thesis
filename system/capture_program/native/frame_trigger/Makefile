.DEFAULT_GOAL := all

CC ?= cc
MOCK_ONLY ?= 0
EXTRA_CPPFLAGS ?=
CPPFLAGS ?=
CPPFLAGS += $(EXTRA_CPPFLAGS)
CFLAGS ?= -O2
CFLAGS += -std=c11 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=
LDLIBS += -lm

TARGET ?= frame_trigger
SOURCE := frame_trigger.c
LOOPBACK_TEST ?= tests/test_loopback_logic
GPIO_UAPI_V2_PROBE := tests/probe_gpio_uapi_v2.c
UNAME_S := $(shell uname -s)

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

CPPFLAGS += -DFRAME_TRIGGER_ENABLE_LINUX_GPIO=$(HW_AVAILABLE)

.PHONY: all check-hw clean test print-hw
all: $(TARGET)

check-hw:
ifeq ($(HW_DEPENDENCY_MISSING),1)
	@echo "Linux hardware build requires GPIO character-device uAPI v2 headers." >&2
	@echo "Install linux-libc-dev, or explicitly use MOCK_ONLY=1 for a mock-only binary." >&2
	@echo "libgpiod is not used; userspace timestamps are never substituted for kernel loopback edges." >&2
	@exit 1
endif

$(TARGET): $(SOURCE) loopback_logic.h | check-hw
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

$(LOOPBACK_TEST): tests/test_loopback_logic.c loopback_logic.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. -o $@ $<

test: $(TARGET) $(LOOPBACK_TEST)
	./$(LOOPBACK_TEST)
	python3 -m unittest discover -s tests -v
	sh tests/test_build_contract.sh

print-hw:
	@echo "Frame trigger Linux hardware support: $(HW_AVAILABLE)"
	@echo "GPIO backend: $(if $(filter 1,$(HW_AVAILABLE)),linux-gpio-uapi-v2,unavailable)"
	@if test "$(UNAME_S)" = "Linux" && test "$(HW_AVAILABLE)" != "1"; then \
		if test "$(MOCK_ONLY)" = "1"; then \
			echo "Mock-only build explicitly selected with MOCK_ONLY=1."; \
		else \
			echo "Install Linux GPIO uAPI v2 headers from linux-libc-dev before building."; \
		fi; \
	fi

clean:
	rm -f $(TARGET) $(LOOPBACK_TEST)
	rm -rf $(TARGET).dSYM
	rm -rf $(LOOPBACK_TEST).dSYM
