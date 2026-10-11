import pathlib

import toml

import mmwavecapture.capture.synchronized as synchronized_module
from mmwavecapture.radar import RadarCoreConfig


PROJECT = pathlib.Path(__file__).resolve().parents[1]


def load_example(name):
    config = toml.load(PROJECT / "examples" / name)
    return config["hardware"]["synchronized"]


def active_frame_time_ms(radar):
    frame = radar.command_args("frameCfg")[0]
    profile = radar.command_args("profileCfg")[0]
    chirps_per_frame = (int(frame[1]) - int(frame[0]) + 1) * int(frame[2])
    chirp_period_us = float(profile[2]) + float(profile[4])
    return chirps_per_frame * chirp_period_us / 1000.0


def test_software_example_has_matching_radar_and_adxl_contracts():
    hardware = load_example("capture_synchronized_software.toml")
    radar_path = PROJECT / hardware["radar_kwargs"]["radar_config_filename"]
    radar = RadarCoreConfig(radar_path)

    assert int(radar.command_args("frameCfg")[0][2]) == 4
    assert hardware["radar_kwargs"]["algorithm_chirp_aggregation"] == "coherent_mean"
    assert hardware["sync_mode"] == "software_timestamp"
    assert int(radar.command_args("frameCfg")[0][5]) == 1
    assert radar.frame_period == 1.130134
    assert active_frame_time_ms(radar) <= 0.9 * radar.frame_period
    assert hardware["adxl_kwargs"]["drdy_line"] == 25
    assert hardware["adxl_kwargs"]["odr_hz"] == 2000
    assert hardware["adxl_kwargs"]["spi_device"] == "/dev/spidev0.0"


def test_hardware_example_has_one_trigger_per_radar_frame():
    hardware = load_example("capture_synchronized_hardware.toml")
    radar_path = PROJECT / hardware["radar_kwargs"]["radar_config_filename"]
    radar = RadarCoreConfig(radar_path)
    trigger = hardware["trigger_kwargs"]

    assert int(radar.command_args("frameCfg")[0][2]) == 4
    assert hardware["radar_kwargs"]["algorithm_chirp_aggregation"] == "coherent_mean"
    assert hardware["sync_mode"] == "hardware_trigger"
    assert hardware["hardware_validated"] is False
    assert int(radar.command_args("frameCfg")[0][5]) == 2
    assert radar.frame_period == 1.01712
    assert active_frame_time_ms(radar) <= radar.frame_period + 1e-12
    assert trigger["count"] == hardware["radar_kwargs"]["capture_frames"]
    assert trigger["frequency_hz"] == 884.850822998
    assert abs(1000.0 / trigger["frequency_hz"] - 1.130134) < 1e-9
    assert trigger["frequency_hz"] <= 0.9 * 1000.0 / radar.frame_period
    assert 1000.0 / trigger["frequency_hz"] < 5000.0
    assert trigger["initial_delay_ms"] < 5000
    assert trigger["output_line"] == 18
    assert "loopback_line" not in trigger
    assert trigger["use_loopback"] is False


def test_both_examples_construct_without_touching_hardware(monkeypatch):
    instances = []

    class StubRadarDCA:
        def __init__(self, hw_name, **options):
            self.hw_name = hw_name
            self.options = options
            instances.append(self)

        def close(self):
            pass

    monkeypatch.setattr(synchronized_module, "RadarDCA", StubRadarDCA)

    for name in (
        "capture_synchronized_software.toml",
        "capture_synchronized_hardware.toml",
    ):
        hardware = load_example(name)
        capture = synchronized_module.SynchronizedRadarAdxl(
            hw_name="synchronized",
            **hardware,
        )
        assert capture.state == "initialized"
        capture.close()

    assert len(instances) == 2
