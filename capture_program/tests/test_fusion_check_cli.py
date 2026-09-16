import json
from types import SimpleNamespace

from click.testing import CliRunner

import mmwavecapture.fusion_check_cli as fusion_check_cli


def _capture(tmp_path, *, ready, algorithm_ready=True):
    return SimpleNamespace(
        fusion_ready=ready,
        algorithm_ready=algorithm_ready,
        quality=SimpleNamespace(
            algorithm_readiness_failures=()
            if algorithm_ready
            else ("adxl_source_is_mock",),
            readiness_failures=()
            if ready
            else ("radar_reference_to_adc_latency_not_calibrated",)
        ),
        directory=tmp_path,
        provenance=SimpleNamespace(
            clock="CLOCK_MONOTONIC",
            sync_mode="hardware_trigger",
            radar_timestamp_quality="kernel_loopback_edge",
        ),
        radar_adc_sample_monotonic_ns=None
        if not ready
        else __import__("numpy").array([1, 2]),
        radar_reference_monotonic_ns=__import__("numpy").array([1, 2]),
        adxl_sample_monotonic_ns=__import__("numpy").array([1, 2, 3]),
        calibration=SimpleNamespace(
            radar_reference_edge_uncertainty_ns=500,
            radar_reference_to_adc_latency_uncertainty_ns=1_000,
            radar_latency_source="scope-v1",
            adxl_filter_group_delay_uncertainty_ns=2_000,
            adxl_group_delay_source="adxl-bench-v1",
        ),
        value_calibration=SimpleNamespace(calibration_id="fixture-v1"),
    )


def test_ready_capture_prints_machine_readable_summary(monkeypatch, tmp_path):
    monkeypatch.setattr(
        fusion_check_cli,
        "load_fusion_input",
        lambda path: _capture(tmp_path, ready=True),
    )

    result = CliRunner().invoke(fusion_check_cli.cli, [str(tmp_path)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["fusion_ready"] is True
    assert payload["algorithm_ready"] is True
    assert payload["radar_frames"] == 2
    assert payload["adxl_samples"] == 3
    assert payload["timing_uncertainty_ns"]["radar_reference_edge"] == 500


def test_algorithm_ready_capture_passes_default_operational_gate(monkeypatch, tmp_path):
    monkeypatch.setattr(
        fusion_check_cli,
        "load_fusion_input",
        lambda path: _capture(tmp_path, ready=False),
    )

    operational = CliRunner().invoke(fusion_check_cli.cli, [str(tmp_path)])
    strict = CliRunner().invoke(
        fusion_check_cli.cli,
        ["--require-calibrated", str(tmp_path)],
    )
    diagnostic = CliRunner().invoke(
        fusion_check_cli.cli,
        ["--require-calibrated", "--allow-not-ready", str(tmp_path)],
    )

    assert operational.exit_code == 0
    assert strict.exit_code != 0
    assert "latency_not_calibrated" in strict.output
    assert diagnostic.exit_code == 0
    assert json.loads(diagnostic.output)["fusion_ready"] is False


def test_default_gate_rejects_non_algorithm_ready_capture(monkeypatch, tmp_path):
    monkeypatch.setattr(
        fusion_check_cli,
        "load_fusion_input",
        lambda path: _capture(tmp_path, ready=False, algorithm_ready=False),
    )

    result = CliRunner().invoke(fusion_check_cli.cli, [str(tmp_path)])

    assert result.exit_code != 0
    assert "not algorithm-ready" in result.output
    assert "adxl_source_is_mock" in result.output
