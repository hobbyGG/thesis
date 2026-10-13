import json
import pathlib
import struct
import threading

import numpy as np
import pytest

import mmwavecapture.capture.synchronized as synchronized_module
from mmwavecapture.adxl355_input import RAW_HEADER_BYTES, RECORD_DTYPE
from mmwavecapture.capture.synchronized import SynchronizedRadarAdxl
from mmwavecapture.synchronized_input import (
    SynchronizedInputError,
    load_synchronized_timeline,
)


def complete_adxl_summary(samples):
    return {
        "schema_version": 1,
        "status": "complete",
        "samples": samples,
        "samples_written": samples,
        "first_drdy_monotonic_ns": 11_000_000_000,
        "last_drdy_monotonic_ns": 11_000_000_000 + (samples - 1) * 1_000_000,
        "line_seq_gaps": 0,
        "fifo_overruns": 0,
        "gpio_backlog_events": 0,
        "fifo_protocol_errors": 0,
        "fifo_xyz_mismatches": 0,
        "fifo_xyz_sets_drained": 0,
        "max_fifo_entries": 0,
        "mock": True,
        "sample_source": "mock",
        "timestamp_pairing": "synthetic",
        "clock": "CLOCK_MONOTONIC",
        "timestamp_semantics": "drdy_edge",
        "start_realtime_ns": 1_800_000_000_000_000_000,
        "start_monotonic_ns": 10_000_000_000,
        "group_delay_ns": 0,
        "group_delay_calibrated": False,
        "config": {"odr_hz": 1000, "range_g": 2, "spi_hz": 5_000_000},
    }


def write_adxl_artifacts(directory, samples=3):
    directory.mkdir(parents=True, exist_ok=True)
    header = bytearray(RAW_HEADER_BYTES)
    header[:8] = b"ADXLRW01"
    struct.pack_into("<HHHH", header, 8, 1, 64, 48, 1)
    struct.pack_into("<I", header, 16, 1_000_000)
    struct.pack_into("<H", header, 20, 2)
    struct.pack_into("<Q", header, 24, 1_800_000_000_000_000_000)
    struct.pack_into("<Q", header, 32, 10_000_000_000)
    struct.pack_into("<q", header, 40, 0)

    records = np.zeros(samples, dtype=RECORD_DTYPE)
    records["sample_seq"] = np.arange(samples, dtype=np.uint64)
    records["line_seqno"] = np.arange(1, samples + 1, dtype=np.uint64)
    records["drdy_monotonic_ns"] = (
        11_000_000_000 + np.arange(samples, dtype=np.uint64) * 1_000_000
    )
    records["spi_complete_monotonic_ns"] = (
        records["drdy_monotonic_ns"] + 25_000
    )
    records["z_raw"] = 256_000
    records["status"] = 1
    (directory / "samples.bin").write_bytes(bytes(header) + records.tobytes())
    summary = complete_adxl_summary(samples)
    (directory / "summary.json").write_text(
        json.dumps(summary), encoding="utf-8"
    )
    (directory / "ready.json").write_text(
        json.dumps({"status": "ready"}), encoding="utf-8"
    )
    return summary


class FakeRadar:
    def __init__(self, frames=3, frame_period_s=0.1):
        self.calls = []
        self.base_path = None
        self.frames = frames
        self.frame_period_s = frame_period_s

    def prepare_capture(self):
        self.calls.append("prepare")

    def start_capture(self):
        self.calls.append("start")

    def stop_capture(self):
        self.calls.append("stop")

    def request_continuous_stop(self):
        self.calls.append("request_continuous_stop")

    def abort_capture(self):
        self.calls.append("abort")

    def dump_config(self):
        self.calls.append("dump")
        (self.base_path / "radar.cfg").write_text("mock\n", encoding="utf-8")
        (self.base_path / "dca.json").write_text("{}\n", encoding="utf-8")

    def finalize_capture(self):
        self.calls.append("finalize")
        algorithm_input = self.base_path / "algorithm_input"
        algorithm_input.mkdir(exist_ok=True)
        (algorithm_input / "manifest.json").write_text(
            json.dumps(
                {
                    "schema": "mmwavecapture.algorithm-input",
                    "schema_version": 1,
                    "packet_integrity": {"complete": True},
                    "radar": {
                        "frames": self.frames,
                        "frame_period_s": self.frame_period_s,
                    },
                    "arrays": {
                        "adc_cube": {
                            "file": "adc_cube.npy",
                            "dtype": "complex64",
                            "shape": [self.frames, 1, 1],
                            "axes": [
                                "frame",
                                "virtual_antenna",
                                "adc_sample",
                            ],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def close(self):
        self.calls.append("close")


class FakeAdxl:
    def __init__(self):
        self.calls = []
        self.summary = None
        self.config = {"implementation": "fake-adxl"}

    def start(self, output_dir):
        self.calls.append("start")
        self.summary = write_adxl_artifacts(output_dir)
        return {"status": "ready"}

    def stop(self):
        self.calls.append("stop")
        return dict(self.summary)

    def check_running(self):
        self.calls.append("check_running")
        return {"status": "running"}

    def validate_summary(self):
        self.calls.append("validate")
        return dict(self.summary)

    def abort(self):
        self.calls.append("abort")

    def close(self):
        self.calls.append("close")


class FakeTrigger:
    EVENTS_FILENAME = "frame_trigger_events.csv"
    SUMMARY_FILENAME = "frame_trigger_summary.json"
    instances = []

    def __init__(self, sync_dir, **options):
        self.sync_dir = sync_dir
        self.options = options
        self.count = options["count"]
        self.frequency_hz = options["frequency_hz"]
        self.config = dict(options)
        self.summary = None
        self.calls = []
        self.__class__.instances.append(self)

    def start(self):
        self.calls.append("start")

    def wait(self):
        self.calls.append("wait")
        rows = [
            "sequence,scheduled_monotonic_ns,asserted_monotonic_ns,"
            "deasserted_monotonic_ns,loopback_monotonic_ns"
        ]
        for sequence in range(self.count):
            period_ns = round(1_000_000_000.0 / self.frequency_hz)
            asserted = 20_000_000_000 + sequence * period_ns
            rows.append(
                f"{sequence},{asserted},{asserted},{asserted + 100000},"
            )
        (self.sync_dir / self.EVENTS_FILENAME).write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )
        self.summary = {
            "schema_version": 1,
            "status": "ok",
            "requested_count": self.count,
            "emitted_count": self.count,
            "observed_count": 0,
            "missed_loopback": 0,
            "timestamp_quality": "userspace_set_completed",
            "clock": "CLOCK_MONOTONIC",
        }
        return dict(self.summary)

    def abort(self):
        self.calls.append("abort")

    def close(self):
        self.calls.append("close")


def radar_config(path, trigger_select, num_frames=3):
    path.write_text(
        "\n".join(
            [
                "channelCfg 15 7 0",
                "profileCfg 0 77 7 7 57 0 0 70 1 256 5000 0 0 30",
                "frameCfg 0 2 16 {} 100.0 {} 0".format(
                    num_frames,
                    trigger_select,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def fusion_calibration(path):
    path.write_text(
        json.dumps(
            {
                "schema": "mmwavecapture.fusion-calibration",
                "schema_version": 1,
                "calibration_id": "sync-fixture-v1",
                "validated": True,
                "adxl355": {
                    "bias_mps2": [0.0, 0.0, 0.0],
                    "scale_matrix": [
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                    ],
                    "sensor_to_structure_rotation": [
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                    ],
                    "structural_axis_unit": [1.0, 0.0, 0.0],
                    "source": "fixture-installation-survey",
                },
                "radar": {
                    "azimuth_virtual_channel_indices": [0],
                    "virtual_array_positions_wavelengths": [0.0],
                    "channel_correction_real": [1.0],
                    "channel_correction_imag": [0.0],
                    "range_bias_correction_m": 0.0,
                    "source": "fixture-reflector",
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def run_lifecycle(capture, base_path):
    capture.base_path = base_path
    capture.prepare_capture()
    capture.start_capture()
    capture.stop_capture()
    capture.dump_config()
    capture.finalize_capture()


def create_completed_software_capture(tmp_path):
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=FakeRadar(),
        adxl_capture=FakeAdxl(),
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    run_lifecycle(capture, output)
    return output


def test_software_capture_exports_adxl_and_truthful_manifest(tmp_path):
    radar = FakeRadar()
    adxl = FakeAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        adxl_capture=adxl,
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )

    run_lifecycle(capture, output)

    manifest = json.loads((output / "sync" / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert manifest["timestamp_quality"] == "sensor_start_bracket_estimate"
    assert manifest["uncertainty"]["packet_receive_time_is_frame_start"] is False
    assert manifest["validation"]["adxl355_finalized"] is True
    assert manifest["validation"]["sync_timeline_exported"] is True
    assert (output / "adxl355" / "algorithm_input" / "manifest.json").is_file()
    timeline = load_synchronized_timeline(output)
    assert timeline.combined_manifest == manifest
    assert timeline.radar_frame_monotonic_ns.shape == (3,)
    assert np.diff(timeline.radar_frame_monotonic_ns).tolist() == [
        100_000_000,
        100_000_000,
    ]
    assert timeline.manifest["provenance"]["is_measured_radar_frame_start"] is False
    event_names = [event["name"] for event in manifest["events"]]
    assert event_names.index("adxl_ready") < event_names.index(
        "radar_prepare_begin"
    )
    assert event_names.index("radar_sensor_start_send_before") < event_names.index(
        "radar_sensor_start_return_after"
    )
    assert radar.calls == ["prepare", "start", "stop", "dump", "finalize"]
    assert adxl.calls == [
        "start",
        "check_running",
        "check_running",
        "stop",
        "validate",
    ]


def test_hardware_mode_builds_finite_trigger_from_radar_contract(
    monkeypatch, tmp_path
):
    FakeTrigger.instances = []
    monkeypatch.setattr(synchronized_module, "FrameTriggerProcess", FakeTrigger)
    radar = FakeRadar()
    adxl = FakeAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
        adxl_capture=adxl,
        trigger_kwargs={
            "binary_path": "frame_trigger",
            "initial_delay_ms": 0,
            "mock": True,
        },
        sync_mode="hardware_trigger",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )

    run_lifecycle(capture, output)

    trigger = FakeTrigger.instances[0]
    assert trigger.count == 3
    assert trigger.frequency_hz == pytest.approx(9.0)
    assert trigger.calls == ["start", "wait"]
    manifest = json.loads((output / "sync" / "manifest.json").read_text())
    assert manifest["timestamp_quality"] == "userspace_set_completed"
    assert manifest["hardware_validated"] is False
    assert manifest["validation"]["radar_trigger_config_validated"] is True
    assert manifest["validation"]["trigger"]["emitted_count"] == 3
    timeline = np.load(output / "sync" / "radar_frame_monotonic_ns.npy")
    assert timeline.tolist() == [
        20_000_000_000,
        20_111_111_111,
        20_222_222_222,
    ]
    loaded = load_synchronized_timeline(output)
    assert loaded.combined_manifest["timestamp_quality"] == (
        "userspace_set_completed"
    )
    timeline_manifest = json.loads((output / "sync" / "timeline.json").read_text())
    assert timeline_manifest["provenance"]["edge_observation"] == (
        "userspace_gpio_set_completion"
    )
    assert "not an observation of the physical SYNC_IN edge" in (
        timeline_manifest["provenance"]["semantics"]
    )
    assert "not an observed physical SYNC_IN edge" in (
        manifest["timestamp_semantics"]["radar"]
    )


def test_hardware_mode_packages_value_and_timing_calibration(monkeypatch, tmp_path):
    FakeTrigger.instances = []
    monkeypatch.setattr(synchronized_module, "FrameTriggerProcess", FakeTrigger)
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=FakeRadar(),
        radar_kwargs={
            "radar_config_filename": radar_config(
                tmp_path / "hardware-calibrated.cfg", trigger_select=2
            ),
            "capture_frames": 3,
        },
        adxl_capture=FakeAdxl(),
        trigger_kwargs={
            "binary_path": "frame_trigger",
            "initial_delay_ms": 0,
            "mock": True,
        },
        sync_mode="hardware_trigger",
        hardware_validated=True,
        fusion_calibration_filename=fusion_calibration(
            tmp_path / "fusion_calibration.json"
        ),
        trigger_edge_uncertainty_ns=500,
        radar_trigger_latency_ns=125_000,
        radar_trigger_latency_uncertainty_ns=2_000,
        radar_trigger_latency_source="scope-fixture-v1",
        adxl_filter_group_delay_uncertainty_ns=3_000,
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )

    run_lifecycle(capture, output)

    manifest = json.loads((output / "sync" / "manifest.json").read_text())
    assert manifest["files"]["sync"]["fusion_calibration"] == (
        "sync/fusion_calibration.json"
    )
    assert (output / "sync" / "fusion_calibration.json").is_file()
    assert manifest["uncertainty"]["trigger_edge_uncertainty_ns"] == 500
    assert manifest["uncertainty"]["radar_trigger_latency_ns"] == 125_000
    assert manifest["uncertainty"]["radar_trigger_latency_calibrated"] is True
    assert manifest["uncertainty"]["radar_trigger_latency_source"] == (
        "scope-fixture-v1"
    )
    assert manifest["uncertainty"]["status"] == "not_characterized"


def test_partial_radar_latency_calibration_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="requires value, uncertainty, and source"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={
                "radar_config_filename": radar_config(
                    tmp_path / "hardware-partial.cfg", trigger_select=2
                ),
                "capture_frames": 3,
            },
            adxl_capture=FakeAdxl(),
            trigger_capture=FakeTrigger(
                pathlib.Path("."), count=3, frequency_hz=9.0
            ),
            sync_mode="hardware_trigger",
            radar_trigger_latency_ns=125_000,
        )


def test_hardware_continuous_radar_stops_normally_after_finite_trigger_train(
    monkeypatch,
    tmp_path,
):
    FakeTrigger.instances = []
    monkeypatch.setattr(synchronized_module, "FrameTriggerProcess", FakeTrigger)
    output = tmp_path / "synchronized"
    output.mkdir()
    radar = FakeRadar(frames=3)
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        radar_kwargs={
            "radar_config_filename": radar_config(
                tmp_path / "hardware-continuous.cfg",
                trigger_select=2,
                num_frames=0,
            ),
            "capture_frames": 0,
        },
        adxl_capture=FakeAdxl(),
        trigger_kwargs={
            "binary_path": "frame_trigger",
            "count": 3,
            "frequency_hz": 9.0,
            "initial_delay_ms": 0,
            "mock": True,
        },
        sync_mode="hardware_trigger",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )

    run_lifecycle(capture, output)

    request_index = radar.calls.index("request_continuous_stop")
    assert request_index < radar.calls.index("stop")
    timeline = np.load(output / "sync" / "radar_frame_monotonic_ns.npy")
    assert timeline.shape == (3,)


def test_hardware_mode_rejects_wrong_radar_trigger_select_before_capture(tmp_path):
    cfg = radar_config(tmp_path / "software.cfg", trigger_select=1)

    with pytest.raises(ValueError, match="requires frameCfg triggerSelect=2"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
            adxl_capture=FakeAdxl(),
            trigger_kwargs={"count": 3, "frequency_hz": 10.0},
            sync_mode="hardware_trigger",
        )


def test_hardware_mode_rejects_trigger_faster_than_frame_period(tmp_path):
    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)

    with pytest.raises(ValueError, match="must not exceed 90%"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
            adxl_capture=FakeAdxl(),
            trigger_kwargs={"count": 3, "frequency_hz": 20.0},
            sync_mode="hardware_trigger",
        )


def test_hardware_mode_rejects_initial_delay_near_dca_no_data_timeout(tmp_path):
    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)

    with pytest.raises(ValueError, match="initial_delay_ms must stay below 5000"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
            adxl_capture=FakeAdxl(),
            trigger_kwargs={
                "count": 3,
                "frequency_hz": 9.0,
                "initial_delay_ms": 5000,
            },
            sync_mode="hardware_trigger",
        )


def test_hardware_mode_rejects_trigger_period_at_five_second_guard(tmp_path):
    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)

    with pytest.raises(ValueError, match="period must stay below 5 s"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
            adxl_capture=FakeAdxl(),
            trigger_kwargs={"count": 3, "frequency_hz": 0.2},
            sync_mode="hardware_trigger",
        )


def test_injected_trigger_fields_receive_same_five_second_guards(tmp_path):
    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)
    trigger = FakeTrigger(pathlib.Path("."), count=3, frequency_hz=9.0)
    trigger.initial_delay_ms = 5000

    with pytest.raises(ValueError, match="initial_delay_ms must stay below 5000"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
            adxl_capture=FakeAdxl(),
            trigger_capture=trigger,
            sync_mode="hardware_trigger",
        )


def test_sync_timeline_requires_radar_algorithm_export_at_construction():
    with pytest.raises(ValueError, match="requires RadarDCA export_algorithm_data=true"):
        SynchronizedRadarAdxl(
            "synchronized",
            radar_capture=FakeRadar(),
            radar_kwargs={"export_algorithm_data": False},
            adxl_capture=FakeAdxl(),
            sync_mode="software_timestamp",
            export_sync_timeline=True,
        )


def test_timeline_never_falls_back_to_configured_frame_count(tmp_path):
    class NoAlgorithmManifestRadar(FakeRadar):
        def finalize_capture(self):
            self.calls.append("finalize")

    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=NoAlgorithmManifestRadar(),
        adxl_capture=FakeAdxl(),
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )
    capture.base_path = output
    capture.prepare_capture()
    capture.start_capture()
    capture.stop_capture()
    capture.dump_config()

    with pytest.raises(RuntimeError, match="configuration frame counts are not accepted"):
        capture.finalize_capture()

    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["status"] == "failed"


def test_manifest_omits_disabled_optional_outputs(tmp_path):
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=FakeRadar(),
        radar_kwargs={"export_algorithm_data": False},
        adxl_capture=FakeAdxl(),
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
        export_sync_timeline=False,
    )
    run_lifecycle(capture, output)

    files = json.loads((output / "sync" / "manifest.json").read_text())["files"]
    assert "algorithm_input_directory" not in files["radar"]
    assert "algorithm_input_manifest" not in files["radar"]
    assert "algorithm_input_directory" not in files["adxl355"]
    assert "algorithm_input_manifest" not in files["adxl355"]
    assert "radar_frame_monotonic_ns" not in files["sync"]
    assert "timeline_manifest" not in files["sync"]


def test_adxl_running_check_fails_before_radar_is_armed(tmp_path):
    class ExitedAdxl(FakeAdxl):
        def check_running(self):
            self.calls.append("check_running")
            raise RuntimeError("ADXL355 exited during pre-roll")

    radar = FakeRadar()
    adxl = ExitedAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        adxl_capture=adxl,
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    capture.base_path = output

    with pytest.raises(RuntimeError, match="exited during pre-roll"):
        capture.prepare_capture()

    assert radar.calls == []
    assert adxl.calls == ["start", "check_running", "abort"]
    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["error"]["phase"] == "prepare_capture"


def test_adxl_rechecked_after_radar_prepare_before_sensor_start(tmp_path):
    class ExitedDuringRadarPrepareAdxl(FakeAdxl):
        def check_running(self):
            self.calls.append("check_running")
            if self.calls.count("check_running") == 2:
                raise RuntimeError("ADXL355 exited while DCA was preparing")
            return {"status": "running"}

    radar = FakeRadar()
    adxl = ExitedDuringRadarPrepareAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        adxl_capture=adxl,
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    capture.base_path = output
    capture.prepare_capture()

    with pytest.raises(RuntimeError, match="exited while DCA was preparing"):
        capture.start_capture()

    assert radar.calls == ["prepare", "abort"]
    assert adxl.calls == [
        "start",
        "check_running",
        "check_running",
        "abort",
    ]
    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["error"]["phase"] == "start_capture"


def test_hardware_timeline_rejects_measured_trigger_period_below_frame_period(
    tmp_path,
):
    class TooFastMeasuredTrigger(FakeTrigger):
        def wait(self):
            self.calls.append("wait")
            rows = [
                "sequence,scheduled_monotonic_ns,asserted_monotonic_ns,"
                "deasserted_monotonic_ns,loopback_monotonic_ns"
            ]
            for sequence in range(self.count):
                asserted = 20_000_000_000 + sequence * 99_999_999
                rows.append(
                    f"{sequence},{asserted},{asserted},{asserted + 100000},"
                )
            (self.sync_dir / self.EVENTS_FILENAME).write_text(
                "\n".join(rows) + "\n", encoding="utf-8"
            )
            self.summary = {
                "schema_version": 1,
                "status": "ok",
                "requested_count": self.count,
                "emitted_count": self.count,
                "observed_count": 0,
                "missed_loopback": 0,
                "timestamp_quality": "userspace_set_completed",
                "clock": "CLOCK_MONOTONIC",
            }
            return dict(self.summary)

    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)
    output = tmp_path / "synchronized"
    output.mkdir()
    trigger = TooFastMeasuredTrigger(
        pathlib.Path("."), count=3, frequency_hz=9.0
    )
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=FakeRadar(),
        radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
        adxl_capture=FakeAdxl(),
        trigger_capture=trigger,
        sync_mode="hardware_trigger",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )
    capture.base_path = output
    capture.prepare_capture()
    capture.start_capture()
    capture.stop_capture()
    capture.dump_config()

    with pytest.raises(RuntimeError, match="shorter than radar frame period"):
        capture.finalize_capture()

    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["status"] == "failed"
    assert failed["error"]["phase"] == "finalize_capture"


def test_start_failure_unwinds_radar_before_adxl(tmp_path):
    order = []

    class FailingRadar(FakeRadar):
        def start_capture(self):
            order.append("radar_start")
            raise RuntimeError("synthetic sensorStart failure")

        def abort_capture(self):
            order.append("radar_abort")

    class OrderedAdxl(FakeAdxl):
        def abort(self):
            order.append("adxl_abort")

    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=FailingRadar(),
        adxl_capture=OrderedAdxl(),
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    capture.base_path = output
    capture.prepare_capture()

    with pytest.raises(RuntimeError, match="synthetic sensorStart failure"):
        capture.start_capture()

    assert order == ["radar_start", "radar_abort", "adxl_abort"]
    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["status"] == "failed"
    assert failed["error"]["phase"] == "start_capture"


def test_adxl_supervision_allows_normal_radar_completion(tmp_path):
    radar_released = threading.Event()

    class BlockingRadar(FakeRadar):
        def stop_capture(self):
            self.calls.append("stop")
            if not radar_released.wait(timeout=2):
                raise RuntimeError("test radar stop was never released")

        def abort_capture(self):
            self.calls.append("abort")
            radar_released.set()

    class HealthyAdxl(FakeAdxl):
        def check_running(self):
            self.calls.append("check_running")
            if self.calls.count("check_running") == 3:
                radar_released.set()
            return {"status": "running"}

    radar = BlockingRadar()
    adxl = HealthyAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        adxl_capture=adxl,
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    capture.base_path = output
    capture.prepare_capture()
    capture.start_capture()

    capture.stop_capture()

    assert radar.calls == ["prepare", "start", "stop"]
    assert adxl.calls == [
        "start",
        "check_running",
        "check_running",
        "check_running",
        "stop",
    ]


def test_adxl_exit_during_radar_completion_interrupts_wait_and_aborts(
    tmp_path,
):
    radar_released = threading.Event()

    class BlockingRadar(FakeRadar):
        def stop_capture(self):
            self.calls.append("stop")
            if not radar_released.wait(timeout=2):
                raise RuntimeError("test radar stop was never interrupted")

        def abort_capture(self):
            self.calls.append("abort")
            radar_released.set()

    class ExitedAdxl(FakeAdxl):
        def check_running(self):
            self.calls.append("check_running")
            if self.calls.count("check_running") == 3:
                raise RuntimeError("ADXL355 exited during radar wait")
            return {"status": "running"}

    radar = BlockingRadar()
    adxl = ExitedAdxl()
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        adxl_capture=adxl,
        sync_mode="software_timestamp",
        pre_roll_s=0,
        post_roll_s=0,
    )
    capture.base_path = output
    capture.prepare_capture()
    capture.start_capture()

    with pytest.raises(
        RuntimeError,
        match="ADXL355 collector failed during radar completion wait",
    ):
        capture.stop_capture()

    assert radar.calls == ["prepare", "start", "stop", "abort"]
    assert adxl.calls == [
        "start",
        "check_running",
        "check_running",
        "check_running",
        "abort",
    ]
    assert capture._state == "aborted"
    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["status"] == "failed"
    assert failed["error"]["phase"] == "stop_capture"
    runtime_failure = next(
        event
        for event in failed["events"]
        if event["name"] == "adxl_runtime_failure"
    )
    assert runtime_failure["details"]["wait"] == "radar completion wait"
    assert runtime_failure["details"]["blocking_operation_stopped"] is True


def test_adxl_exit_during_trigger_wait_unwinds_trigger_radar_adxl(
    tmp_path,
):
    order = []
    trigger_released = threading.Event()

    class OrderedRadar(FakeRadar):
        def abort_capture(self):
            self.calls.append("abort")
            order.append("radar_abort")

    class OrderedAdxl(FakeAdxl):
        def check_running(self):
            self.calls.append("check_running")
            if self.calls.count("check_running") == 3:
                raise RuntimeError("ADXL355 exited during trigger wait")
            return {"status": "running"}

        def abort(self):
            self.calls.append("abort")
            order.append("adxl_abort")

    class BlockingTrigger(FakeTrigger):
        def wait(self):
            self.calls.append("wait")
            if not trigger_released.wait(timeout=2):
                raise RuntimeError("test trigger wait was never interrupted")
            return {"status": "aborted"}

        def abort(self):
            self.calls.append("abort")
            order.append("trigger_abort")
            trigger_released.set()

    cfg = radar_config(tmp_path / "hardware.cfg", trigger_select=2)
    radar = OrderedRadar()
    adxl = OrderedAdxl()
    trigger = BlockingTrigger(
        pathlib.Path("."), count=3, frequency_hz=9.0
    )
    output = tmp_path / "synchronized"
    output.mkdir()
    capture = SynchronizedRadarAdxl(
        "synchronized",
        radar_capture=radar,
        radar_kwargs={"radar_config_filename": cfg, "capture_frames": 3},
        adxl_capture=adxl,
        trigger_capture=trigger,
        sync_mode="hardware_trigger",
        pre_roll_s=0,
        post_roll_s=0,
        export_adxl_algorithm_data=False,
    )
    capture.base_path = output
    capture.prepare_capture()
    capture.start_capture()

    with pytest.raises(
        RuntimeError,
        match="ADXL355 collector failed during frame-trigger wait",
    ):
        capture.stop_capture()

    assert order == ["trigger_abort", "radar_abort", "adxl_abort"]
    assert trigger.calls == ["start", "wait", "abort"]
    assert radar.calls == ["prepare", "start", "abort"]
    assert adxl.calls == [
        "start",
        "check_running",
        "check_running",
        "check_running",
        "abort",
    ]
    failed = json.loads((output / "sync" / "manifest.json").read_text())
    assert failed["status"] == "failed"
    assert failed["error"]["phase"] == "stop_capture"


def test_loader_rejects_incomplete_combined_manifest(tmp_path):
    output = create_completed_software_capture(tmp_path)
    combined_path = output / "sync" / "manifest.json"
    combined = json.loads(combined_path.read_text())
    combined["status"] = "failed"
    combined_path.write_text(json.dumps(combined), encoding="utf-8")

    with pytest.raises(SynchronizedInputError, match="combined.*not complete"):
        load_synchronized_timeline(output)


def test_loader_rejects_failed_capture_root_status(tmp_path):
    output = create_completed_software_capture(tmp_path)
    (output / "status.json").write_text(
        json.dumps(
            {"schema_version": 1, "status": "failed", "phase": "capture"}
        ),
        encoding="utf-8",
    )

    with pytest.raises(SynchronizedInputError, match="capture root status"):
        load_synchronized_timeline(output)


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        (None, "unit", "seconds", "unit must be nanoseconds"),
        (None, "sync_mode", "unknown", "sync_mode"),
        (None, "timestamp_quality", "unknown", "timestamp_quality"),
        (None, "hardware_validated", True, "hardware_validated"),
        ("array", "dtype", "uint64", "array dtype"),
        ("array", "shape", [99], "array shape"),
        ("array", "axes", ["sample"], "array axes"),
        (None, "nominal_frame_period_ns", 0, "positive integer"),
        ("provenance", "source", "pcap_receive", "provenance"),
    ],
)
def test_loader_rejects_inconsistent_timeline_metadata(
    tmp_path, section, field, value, message
):
    output = create_completed_software_capture(tmp_path)
    timeline_path = output / "sync" / "timeline.json"
    timeline = json.loads(timeline_path.read_text())
    target = timeline if section is None else timeline[section]
    target[field] = value
    timeline_path.write_text(json.dumps(timeline), encoding="utf-8")

    with pytest.raises(SynchronizedInputError, match=message):
        load_synchronized_timeline(output)


def test_loader_rejects_radar_manifest_without_packet_integrity(tmp_path):
    output = create_completed_software_capture(tmp_path)
    radar_manifest_path = output / "radar" / "algorithm_input" / "manifest.json"
    radar_manifest = json.loads(radar_manifest_path.read_text())
    radar_manifest["packet_integrity"]["complete"] = False
    radar_manifest_path.write_text(json.dumps(radar_manifest), encoding="utf-8")

    with pytest.raises(SynchronizedInputError, match="packet integrity"):
        load_synchronized_timeline(output)
