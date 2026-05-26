# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import unittest
from unittest.mock import patch, MagicMock
import os
import json
import io
import sys

# VTR-STANDUP: Fallback Mock for restricted environments where pydantic is missing.

class MockBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def model_validate(cls, data):
        return cls(**data)

    def model_dump_json(self, **kwargs):
        import json

        def default(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        return json.dumps(self.__dict__, default=default)


mock_pydantic = MagicMock()
mock_pydantic.BaseModel = MockBaseModel
mock_pydantic.Field = MagicMock(return_value=None)
sys.modules["pydantic"] = mock_pydantic


from vtr_standard.poc.vtr_container import VTRContainer # noqa: E402
from vtr_standard.poc.cli import cmd_verify, cmd_sign # noqa: E402


class TestCLI(unittest.TestCase):
    """
    Integration tests for the VTR CLI commands.
    """

    def setUp(self):
        # Setup environment variables for deterministic mock behavior
        # Use patch.dict instead of setting os.environ directly to avoid state leakage
        self.env_patcher = patch.dict(
            os.environ,
            {
                "VTR_TEST_LIVENESS": "true",
                "VTR_TEST_GPS": "34.0522,-118.2437",
                "VTR_KDF_SALT": "test_salt_cli_123",
            },
        )
        self.env_patcher.start()

        # Clear LRU caches that depend on environment variables
        from vtr_standard.poc.mock_prnu import MockPRNU

        MockPRNU._get_kdf_params.cache_clear()

        self.video_path = "test_cli_video.mp4"
        self.sidecar_path = f"{self.video_path}.vtr.json"

        # Create a dummy video file
        with open(self.video_path, "wb") as f:
            f.write(b"dummy video content for cli tests")

        self.sensor_id = "TEST_SENSOR_CLI"

    def tearDown(self):
        # Cleanup
        try:
            if os.path.exists(self.video_path):
                os.remove(self.video_path)
            if os.path.exists(self.sidecar_path):
                os.remove(self.sidecar_path)
        finally:
            self.env_patcher.stop()
            from vtr_standard.poc.mock_prnu import MockPRNU

            MockPRNU._get_kdf_params.cache_clear()

    def test_setup_teardown(self):
        """Sanity check that the file is created and cleaned up"""
        self.assertTrue(os.path.exists(self.video_path))

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_sign_success(self, mock_logger):
        """
        Verify that cmd_sign creates a sidecar successfully with default settings.
        """
        args = MagicMock()
        args.video_path = self.video_path
        args.sensor_id = None
        args.allow_ai = False
        args.link_to = None
        args.force = False

        try:
            cmd_sign(args)
        except SystemExit as e:
            self.fail(f"cmd_sign raised SystemExit unexpectedly: {e}")

        # Check if the sidecar was created
        self.assertTrue(os.path.exists(self.sidecar_path))

        # Check logger calls
        mock_logger.info.assert_any_call("🆔  Using Default Mock Sensor ID")

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_sign_success_custom_sensor(self, mock_logger):
        """
        Verify that cmd_sign creates a sidecar successfully with a custom sensor ID and allow_ai=True.
        """
        args = MagicMock()
        args.video_path = self.video_path
        args.sensor_id = "CUSTOM_SENSOR_123"
        args.allow_ai = True
        args.link_to = None
        args.force = False

        try:
            cmd_sign(args)
        except SystemExit as e:
            self.fail(f"cmd_sign raised SystemExit unexpectedly: {e}")

        # Check if the sidecar was created
        self.assertTrue(os.path.exists(self.sidecar_path))

        # Verify JSON contents
        with open(self.sidecar_path, "r") as f:
            sidecar_data = json.load(f)

        self.assertTrue(
            sidecar_data.get("legal_assertions", {}).get("x_vtr_ai_training")
        )

        # Check logger calls
        mock_logger.info.assert_any_call(
            f"🆔  Using Custom Sensor ID: {args.sensor_id}"
        )

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_sign_file_exists_error(self, mock_logger):
        """
        Verify that cmd_sign exits with 1 when the sidecar exists and --force is not used.
        """
        # Create a dummy sidecar first
        with open(self.sidecar_path, "w") as f:
            f.write("{}")

        args = MagicMock()
        args.video_path = self.video_path
        args.sensor_id = None
        args.allow_ai = False
        args.link_to = None
        args.force = False

        with self.assertRaises(SystemExit) as cm:
            cmd_sign(args)

        self.assertEqual(cm.exception.code, 1)
        mock_logger.error.assert_any_call(
            "    Use --force to overwrite the existing sidecar."
        )

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_sign_file_not_found(self, mock_logger):
        """
        Verify that cmd_sign exits with 1 when the video file is not found.
        """
        args = MagicMock()
        args.video_path = "non_existent_video_path.mp4"
        args.sensor_id = None
        args.allow_ai = False
        args.link_to = None
        args.force = False

        with self.assertRaises(SystemExit) as cm:
            cmd_sign(args)

        self.assertEqual(cm.exception.code, 1)
        # Verify the specific error format logged in cli.py
        mock_logger.error.assert_any_call(
            f"❌  Error: Video file '{args.video_path}' not found."
        )

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_sign_unexpected_error(self, mock_logger):
        """
        Verify that cmd_sign exits with 1 on unexpected errors (e.g. invalid link_to path).
        """
        args = MagicMock()
        args.video_path = self.video_path
        args.sensor_id = None
        args.allow_ai = False
        args.link_to = "invalid_previous_sidecar.json"
        args.force = False

        with self.assertRaises(SystemExit) as cm:
            cmd_sign(args)

        self.assertEqual(cm.exception.code, 1)

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_verify_success(self, mock_logger):
        """
        Verify that cmd_verify succeeds on a valid container and sidecar.
        """
        # Generate a valid sidecar
        container = VTRContainer(self.video_path, self.sensor_id)
        container.create_sidecar(overwrite=True)

        # Create mock arguments for the CLI command
        args = MagicMock()
        args.video_path = self.video_path
        args.sidecar = self.sidecar_path
        args.json = False

        # Should run without raising SystemExit
        try:
            cmd_verify(args)
        except SystemExit as e:
            self.fail(f"cmd_verify raised SystemExit unexpectedly: {e}")

        # Check logger calls to verify success output
        mock_logger.info.assert_any_call("\n✅  VERIFICATION SUCCESSFUL")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cmd_verify_success_json(self, mock_stdout):
        """
        Verify that cmd_verify outputs correct JSON on success when --json is passed.
        """
        # Generate a valid sidecar
        container = VTRContainer(self.video_path, self.sensor_id)
        container.create_sidecar(overwrite=True)

        # Create mock arguments for the CLI command
        args = MagicMock()
        args.video_path = self.video_path
        args.sidecar = self.sidecar_path
        args.json = True

        # Should run without raising SystemExit
        try:
            cmd_verify(args)
        except SystemExit as e:
            self.fail(f"cmd_verify raised SystemExit unexpectedly: {e}")

        # Verify JSON output
        output = mock_stdout.getvalue()
        try:
            result_json = json.loads(output)
            self.assertTrue(result_json.get("is_valid"))
            self.assertIsNone(result_json.get("error_code"))
        except json.JSONDecodeError:
            self.fail("Output was not valid JSON")

    @patch("vtr_standard.poc.cli.logger")
    def test_cmd_verify_failure(self, mock_logger):
        """
        Verify that cmd_verify fails gracefully when the sidecar doesn't match the video.
        """
        # Generate a valid sidecar
        container = VTRContainer(self.video_path, self.sensor_id)
        container.create_sidecar(overwrite=True)

        # Tamper with the video to invalidate the signature
        with open(self.video_path, "ab") as f:
            f.write(b"tampered")

        # Create mock arguments for the CLI command
        args = MagicMock()
        args.video_path = self.video_path
        args.sidecar = self.sidecar_path
        args.json = False

        # Should raise SystemExit(1)
        with self.assertRaises(SystemExit) as cm:
            cmd_verify(args)

        self.assertEqual(cm.exception.code, 1)

        # Check logger calls to verify failure output
        mock_logger.error.assert_any_call("\n❌  VERIFICATION FAILED")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cmd_verify_failure_json(self, mock_stdout):
        """
        Verify that cmd_verify outputs JSON with failure details when --json is passed and validation fails.
        """
        # Generate a valid sidecar
        container = VTRContainer(self.video_path, self.sensor_id)
        container.create_sidecar(overwrite=True)

        # Tamper with the video to invalidate the signature
        with open(self.video_path, "ab") as f:
            f.write(b"tampered")

        # Create mock arguments for the CLI command
        args = MagicMock()
        args.video_path = self.video_path
        args.sidecar = self.sidecar_path
        args.json = True

        # Should raise SystemExit(1)
        with self.assertRaises(SystemExit) as cm:
            cmd_verify(args)

        self.assertEqual(cm.exception.code, 1)

        # Verify JSON output
        output = mock_stdout.getvalue()
        try:
            result_json = json.loads(output)
            self.assertFalse(result_json.get("is_valid"))
            self.assertIsNotNone(result_json.get("error_code"))
        except json.JSONDecodeError:
            self.fail("Output was not valid JSON")


if __name__ == "__main__":
    unittest.main()
