"""Regression tests for platform-specific backend selection."""

import contextlib
import io
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from check_compatibility import provide_recommendations
from main import ToolCallingAgent


class BackendDetectionTests(unittest.TestCase):
    def setUp(self):
        self.agent = ToolCallingAgent.__new__(ToolCallingAgent)

    def test_native_windows_uses_ollama_even_when_cuda_is_available(self):
        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: True)
        )

        with mock.patch("main.platform.system", return_value="Windows"):
            with mock.patch.dict(sys.modules, {"torch": fake_torch}):
                self.assertEqual(self.agent._detect_best_backend(), "ollama")

    def test_linux_with_cuda_uses_vllm(self):
        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: True)
        )

        with mock.patch("main.platform.system", return_value="Linux"):
            with mock.patch.dict(sys.modules, {"torch": fake_torch}):
                self.assertEqual(self.agent._detect_best_backend(), "vllm")

    def test_linux_without_cuda_uses_ollama(self):
        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: False)
        )

        with mock.patch("main.platform.system", return_value="Linux"):
            with mock.patch.dict(sys.modules, {"torch": fake_torch}):
                self.assertEqual(self.agent._detect_best_backend(), "ollama")


class CompatibilityRecommendationTests(unittest.TestCase):
    def test_native_windows_with_cuda_recommends_ollama(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            provide_recommendations(cuda_available=True, system="windows")

        recommendations = output.getvalue()
        self.assertIn("native Windows - will use Ollama", recommendations)
        self.assertIn("official vLLM requires Linux", recommendations)
        self.assertNotIn("Your system supports vLLM!", recommendations)


if __name__ == "__main__":
    unittest.main()
