import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from algorithm.run import run
from measured_bridge_simulation import package_builder


class AlgorithmPipelineTest(unittest.TestCase):
    def test_measured_bridge_package_uses_algorithm_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            result = Path(temporary) / "result.npz"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            output, summary = run(package, result)
            self.assertTrue(output.is_file())
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["method"], "fixed_geometry_beta_structural_kalman")
            arrays = np.load(output)
            self.assertEqual(arrays["q_hat_m"].shape, (100,))
            self.assertEqual(arrays["selected_target_indices"].size, 5)


if __name__ == "__main__":
    unittest.main()
