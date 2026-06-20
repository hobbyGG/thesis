import json
import tempfile
import unittest
from pathlib import Path

from acquisition.sync_capture import SyncCaptureSession


class FakeClock:
    def __init__(self):
        self._wall = 1_700_000_000.0
        self._mono = 10_000

    def wall_time_iso(self):
        self._wall += 0.001
        return f"2026-06-18T15:00:{self._wall % 60:06.3f}+08:00"

    def monotonic_ns(self):
        self._mono += 1_000
        return self._mono


class FakeDevice:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def start(self, output_dir):
        self.calls.append(("start", Path(output_dir).name))
        return {"output_file": f"{self.name}.bin"}

    def stop(self):
        self.calls.append(("stop", None))
        return {"samples": 3}


class SyncCaptureSessionTest(unittest.TestCase):
    def test_writes_sync_json_with_global_and_per_stream_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            radar = FakeDevice("radar")
            accel = FakeDevice("adxl355")

            session = SyncCaptureSession(
                root_dir=tmp,
                session_name="experiment_001",
                radar=radar,
                accel=accel,
                clock=FakeClock(),
            )

            session.start()
            sync_path = session.stop()

            data = json.loads(sync_path.read_text(encoding="utf-8"))

        self.assertEqual(sync_path.name, "sync.json")
        self.assertEqual(data["session_name"], "experiment_001")
        self.assertEqual(data["streams"]["radar"]["device"], "radar")
        self.assertEqual(data["streams"]["accel"]["device"], "adxl355")
        self.assertIn("start_monotonic_ns", data["streams"]["radar"])
        self.assertIn("start_monotonic_ns", data["streams"]["accel"])
        self.assertIn("stop_monotonic_ns", data["streams"]["radar"])
        self.assertIn("stop_monotonic_ns", data["streams"]["accel"])
        self.assertEqual(
            [event["event"] for event in data["events"]],
            [
                "session_prepare",
                "radar_start",
                "accel_start",
                "session_start_complete",
                "session_stop_request",
                "accel_stop",
                "radar_stop",
                "session_stop_complete",
            ],
        )
        self.assertLess(
            data["streams"]["radar"]["start_monotonic_ns"],
            data["streams"]["accel"]["start_monotonic_ns"],
        )
        self.assertEqual(radar.calls, [("start", "radar"), ("stop", None)])
        self.assertEqual(accel.calls, [("start", "accel"), ("stop", None)])


if __name__ == "__main__":
    unittest.main()
