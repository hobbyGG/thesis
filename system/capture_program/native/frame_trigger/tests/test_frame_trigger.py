import csv
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BINARY = ROOT / "frame_trigger"
TRIGGER_MODULE_PATH = (
    ROOT.parents[1] / "src" / "mmwavecapture" / "capture" / "trigger.py"
)


def mock_command(events, summary, **overrides):
    values = {
        "frequency_hz": "100",
        "count": "3",
        "pulse_width_us": "1000",
        "initial_delay_ms": "1",
    }
    values.update(overrides)
    return [
        str(BINARY),
        "--events",
        str(events),
        "--summary",
        str(summary),
        "--gpiochip",
        "/dev/gpiochip0",
        "--output-line",
        "18",
        "--frequency-hz",
        values["frequency_hz"],
        "--count",
        values["count"],
        "--pulse-width-us",
        values["pulse_width_us"],
        "--initial-delay-ms",
        values["initial_delay_ms"],
        "--mock",
    ]


class NativeMockTests(unittest.TestCase):
    def test_linux_make_uses_gpio_uapi_v2_without_libgpiod(self):
        completed = subprocess.run(
            [
                "make",
                "-n",
                "UNAME_S=Linux",
                "GPIO_UAPI_V2_AVAILABLE=1",
                "EXTRA_CPPFLAGS=-Itests/linux_stubs",
                "TARGET=frame_trigger-uapi-v2-test",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("-DFRAME_TRIGGER_ENABLE_LINUX_GPIO=1", completed.stdout)
        self.assertIn("-o frame_trigger-uapi-v2-test frame_trigger.c", completed.stdout)
        self.assertNotIn("pkg-config", completed.stdout + completed.stderr)

    def test_loopback_collector_drains_the_entire_pulse_window(self):
        source = (ROOT / "frame_trigger.c").read_text(encoding="utf-8")
        collector = source.split(
            "static int collect_loopback_until", maxsplit=1
        )[1].split("#endif", maxsplit=1)[0]

        self.assertIn("frame_trigger_record_loopback_edge(", collector)
        self.assertNotIn(
            "if (record->has_loopback_timestamp)",
            collector,
        )

    def test_mock_writes_complete_csv_and_atomic_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            events = directory / "events.csv"
            summary = directory / "summary.json"

            completed = subprocess.run(
                mock_command(events, summary),
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["requested_count"], 3)
            self.assertEqual(payload["emitted_count"], 3)
            self.assertEqual(payload["observed_count"], 0)
            self.assertEqual(payload["missed_loopback"], 0)
            self.assertEqual(payload["clock"], "CLOCK_MONOTONIC")
            self.assertEqual(
                payload["timestamp_quality"], "userspace_set_completed"
            )
            self.assertTrue(payload["configuration"]["mock"])
            self.assertFalse(list(directory.glob("*.tmp.*")))

            with events.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([int(row["sequence"]) for row in rows], [0, 1, 2])
            self.assertTrue(all(row["loopback_monotonic_ns"] == "" for row in rows))
            for row in rows:
                self.assertLessEqual(
                    int(row["scheduled_monotonic_ns"]),
                    int(row["asserted_monotonic_ns"]),
                )
                self.assertLess(
                    int(row["asserted_monotonic_ns"]),
                    int(row["deasserted_monotonic_ns"]),
                )

    def test_rejects_pulse_not_shorter_than_period(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            completed = subprocess.run(
                mock_command(
                    directory / "events.csv",
                    directory / "summary.json",
                    frequency_hz="1000",
                    pulse_width_us="1000",
                ),
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("shorter than one trigger period", completed.stderr)

    def test_mock_rejects_loopback_instead_of_fabricating_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            command = mock_command(directory / "events.csv", directory / "summary.json")
            command[-1:-1] = ["--loopback-line", "24"]

            completed = subprocess.run(
                command, check=False, capture_output=True, text=True
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("never fabricates kernel edges", completed.stderr)

    def test_sigterm_publishes_an_interrupted_partial_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            events = directory / "events.csv"
            summary = directory / "summary.json"
            command = mock_command(
                events,
                summary,
                frequency_hz="10",
                count="100",
                initial_delay_ms="5000",
            )
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(0.05)
            process.terminate()
            _, stderr = process.communicate(timeout=5.0)

            self.assertNotEqual(process.returncode, 0, stderr)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "interrupted")
            self.assertEqual(payload["requested_count"], 100)
            self.assertEqual(payload["emitted_count"], 0)
            self.assertEqual(events.read_text(encoding="utf-8").count("\n"), 1)


class PythonWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "frame_trigger_wrapper_under_test", TRIGGER_MODULE_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load trigger wrapper module")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def test_wrapper_runs_native_mock_and_validates_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            process = self.module.FrameTriggerProcess(
                pathlib.Path(temporary),
                binary_path=BINARY,
                frequency_hz=100.0,
                count=3,
                pulse_width_us=1000,
                initial_delay_ms=1,
                mock=True,
            )

            returned = process.start()
            self.assertIs(returned, process)
            summary = process.wait(timeout=5.0)

            self.assertEqual(summary["emitted_count"], 3)
            self.assertEqual(process.summary, summary)
            self.assertTrue(process.events_path.is_file())
            process.close()

    def test_wrapper_rejects_stale_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            sync_dir = pathlib.Path(temporary)
            (sync_dir / "frame_trigger_summary.json").write_text(
                "{}", encoding="utf-8"
            )
            process = self.module.FrameTriggerProcess(
                sync_dir,
                binary_path=BINARY,
                frequency_hz=100.0,
                count=1,
                pulse_width_us=1000,
                initial_delay_ms=1,
                mock=True,
            )

            with self.assertRaises(FileExistsError):
                process.start()

    def test_wrapper_supports_popen_injection_and_mock_omits_loopback(self):
        with tempfile.TemporaryDirectory() as temporary:
            sync_dir = pathlib.Path(temporary)
            captured = {}

            class FakeProcess:
                returncode = 0

                def communicate(self, timeout=None):
                    captured["timeout"] = timeout
                    return (None, "")

                def poll(self):
                    return self.returncode

            def fake_popen(command, **kwargs):
                captured["command"] = command
                captured["kwargs"] = kwargs
                summary_index = command.index("--summary") + 1
                pathlib.Path(command[summary_index]).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "status": "ok",
                            "requested_count": 2,
                            "emitted_count": 2,
                            "observed_count": 0,
                            "missed_loopback": 0,
                            "timestamp_quality": "userspace_set_completed",
                            "clock": "CLOCK_MONOTONIC",
                            "configuration": {
                                "gpiochip": "/dev/gpiochip0",
                                "output_line": 18,
                                "loopback_line": None,
                                "frequency_hz": 100.0,
                                "count": 2,
                                "pulse_width_us": 1000,
                                "initial_delay_ms": 1,
                                "mock": True,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return FakeProcess()

            process = self.module.FrameTriggerProcess(
                sync_dir,
                binary_path=pathlib.Path("/injected/frame_trigger"),
                frequency_hz=100.0,
                count=2,
                pulse_width_us=1000,
                initial_delay_ms=1,
                mock=True,
                popen=fake_popen,
            )
            process.start()
            summary = process.wait(timeout=3.0)

            self.assertEqual(summary["emitted_count"], 2)
            self.assertNotIn("--loopback-line", captured["command"])
            self.assertIn("--mock", captured["command"])
            self.assertEqual(captured["timeout"], 3.0)
            self.assertTrue(captured["kwargs"]["text"])


if __name__ == "__main__":
    unittest.main()
