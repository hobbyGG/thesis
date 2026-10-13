import json
import types

import pytest
import toml

import mmwavecapture.capture.capture as capture_module


class FakeHardware(capture_module.CaptureHardware):
    instances = []

    def __init__(
        self,
        hw_name,
        fail_init=False,
        fail_stop=False,
        fail_finalize=False,
        **_kwargs,
    ):
        self.hw_name = hw_name
        self.fail_stop = fail_stop
        self.fail_finalize = fail_finalize
        self.calls = []
        self.__class__.instances.append(self)
        if fail_init:
            raise RuntimeError("synthetic initialization failure")

    def init_capture_hw(self):
        self.calls.append("init_capture_hw")

    def prepare_capture(self):
        self.calls.append("prepare_capture")

    def start_capture(self):
        self.calls.append("start_capture")

    def stop_capture(self):
        self.calls.append("stop_capture")
        if self.fail_stop:
            raise RuntimeError("synthetic stop failure")

    def abort_capture(self):
        self.calls.append("abort_capture")

    def dump_config(self):
        self.calls.append("dump_config")
        (self.base_path / "fake.json").write_text("{}\n", encoding="utf-8")

    def finalize_capture(self):
        self.calls.append("finalize_capture")
        if self.fail_finalize:
            raise RuntimeError("synthetic finalize failure")

    def close(self):
        self.calls.append("close")


def manager_config(
    tmp_path,
    *,
    fail_init=False,
    fail_stop=False,
    fail_finalize=False,
):
    config = {
        "dataset_dir": str(tmp_path / "dataset"),
        "hardware": {
            "fake": {
                "hw_def_class": "fake.module.FakeHardware",
                "fail_init": fail_init,
                "fail_stop": fail_stop,
                "fail_finalize": fail_finalize,
            }
        },
    }
    path = tmp_path / "capture.toml"
    path.write_text(toml.dumps(config), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def fake_hardware_module(monkeypatch):
    FakeHardware.instances = []
    module = types.SimpleNamespace(FakeHardware=FakeHardware)
    monkeypatch.setattr(capture_module.importlib, "import_module", lambda _name: module)


def test_manager_persists_config_and_complete_status(tmp_path):
    manager = capture_module.CaptureManager(manager_config(tmp_path))

    assert (manager._capture_dir / "config.toml").is_file()
    persisted_config = toml.load(manager._capture_dir / "config.toml")
    assert persisted_config["metadata"]["title"] == "Millimeter-wave dataset"
    assert persisted_config["logging"]["logfile"]["enable"] is True
    created = json.loads((manager._capture_dir / "status.json").read_text())
    assert created["status"] == "pending"
    assert created["phase"] == "created"

    manager.init_hw()
    manager.capture()

    status = json.loads((manager._capture_dir / "status.json").read_text())
    assert status["status"] == "complete"
    assert status["phase"] == "complete"
    assert (manager._capture_dir / "fake" / "fake.json").is_file()
    assert FakeHardware.instances[0].calls == [
        "prepare_capture",
        "start_capture",
        "stop_capture",
        "dump_config",
        "finalize_capture",
        "close",
    ]


def test_manager_records_initialization_failure(tmp_path):
    manager = capture_module.CaptureManager(manager_config(tmp_path, fail_init=True))

    with pytest.raises(RuntimeError, match="synthetic initialization failure"):
        manager.init_hw()

    status = json.loads((manager._capture_dir / "status.json").read_text())
    assert status["status"] == "failed"
    assert status["phase"] == "initialization"
    assert status["error"]["type"] == "RuntimeError"


def test_manager_preserves_failure_evidence_and_original_exception(tmp_path):
    manager = capture_module.CaptureManager(manager_config(tmp_path, fail_stop=True))
    manager.init_hw()

    with pytest.raises(RuntimeError, match="synthetic stop failure"):
        manager.capture()

    status = json.loads((manager._capture_dir / "status.json").read_text())
    assert status["status"] == "failed"
    assert status["phase"] == "capture"
    assert status["error"]["type"] == "RuntimeError"
    assert status["error"]["message"] == "synthetic stop failure"
    assert (manager._capture_dir / "config.toml").is_file()
    assert (manager._capture_dir / "fake" / "fake.json").is_file()
    assert FakeHardware.instances[0].calls == [
        "prepare_capture",
        "start_capture",
        "stop_capture",
        "abort_capture",
        "dump_config",
        "close",
    ]


def test_manager_marks_algorithm_output_finalization_failure(tmp_path):
    manager = capture_module.CaptureManager(
        manager_config(tmp_path, fail_finalize=True)
    )
    manager.init_hw()

    with pytest.raises(RuntimeError, match="synthetic finalize failure"):
        manager.capture()

    status = json.loads((manager._capture_dir / "status.json").read_text())
    assert status["status"] == "failed"
    assert status["phase"] == "capture"
    assert FakeHardware.instances[0].calls == [
        "prepare_capture",
        "start_capture",
        "stop_capture",
        "dump_config",
        "finalize_capture",
        "abort_capture",
        "dump_config",
        "close",
    ]
