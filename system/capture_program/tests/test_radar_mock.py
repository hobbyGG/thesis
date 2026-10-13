import pathlib

import mmwavecapture.radar as radar_module


class FakeSerial:
    instances = []

    def __init__(self):
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.is_open = False
        self.writes = []
        self.__class__.instances.append(self)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def write(self, payload):
        self.writes.append(payload)

    def read_until(self, _marker):
        return b"\nDone\nmmwDemo:/>\n"


def test_radar_serial_configuration_and_start_are_mocked(monkeypatch, tmp_path):
    FakeSerial.instances = []
    monkeypatch.setattr(radar_module.serial, "Serial", FakeSerial)
    monkeypatch.setattr(radar_module.time, "sleep", lambda _seconds: None)
    config_path = pathlib.Path(tmp_path) / "radar.cfg"
    config_path.write_text(
        "\n".join(
            [
                "sensorStop",
                "flushCfg",
                "channelCfg 15 5 0",
                "profileCfg 0 77 429 7 57.14 0 0 70 1 256 5209 0 0 30",
                "frameCfg 0 1 16 0 100 1 0",
                "sensorStart",
            ]
        ),
        encoding="utf-8",
    )

    radar = radar_module.Radar(
        config_port="/dev/ttyACM0",
        config_baudrate=115200,
        data_port="/dev/ttyACM1",
        data_baudrate=921600,
        config_filename=config_path,
        initialize_connection_and_radar=True,
        capture_frames=12,
    )
    radar.config()
    radar.start_sensor()

    config_serial = FakeSerial.instances[0]
    commands = [payload.decode().strip() for payload in config_serial.writes]
    assert config_serial.port == "/dev/ttyACM0"
    assert config_serial.baudrate == 115200
    assert "frameCfg 0 1 16 12 100 1 0" in commands
    assert commands.count("sensorStart") == 1
    assert FakeSerial.instances[1].port == "/dev/ttyACM1"
