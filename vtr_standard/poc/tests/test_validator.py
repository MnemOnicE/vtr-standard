# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import os
import json
import unittest
from unittest.mock import patch
from vtr_standard.poc.validator import VTRValidator

# We can define a dummy exception if pydantic is not present
try:
    from pydantic import ValidationError
except ImportError:

    class ValidationError(Exception):
        pass


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.video_file = "test_invalid_json_video.mp4"
        self.sidecar_file = f"{self.video_file}.vtr.json"

        with open(self.video_file, "wb") as f:
            f.write(b"dummy video")

    def tearDown(self):
        if os.path.exists(self.video_file):
            os.remove(self.video_file)
        if os.path.exists(self.sidecar_file):
            os.remove(self.sidecar_file)

    def test_invalid_json_sidecar(self):
        with open(self.sidecar_file, "w") as f:
            f.write("{ invalid json ]")

        validator = VTRValidator()
        result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_JSON")

    @patch("vtr_standard.poc.validator.VTRValidator._parse_sidecar")
    def test_log_injection_prevention(self, mock_parse_sidecar):
        validator = VTRValidator()

        # Mock the exception raised by _parse_sidecar directly
        class MockValidationError(Exception):
            def __init__(self, msg):
                super().__init__(msg)
                self.errors = lambda: [1, 2, 3]  # fake errors list

        mock_error = MockValidationError("Test Error\r\nLine 1\nLine 2\rLine 3")
        mock_parse_sidecar.side_effect = mock_error

        with open(self.sidecar_file, "w") as f:
            f.write('{"dummy": "data"}')

        with self.assertLogs("vtr_standard.poc.validator", level="ERROR") as cm:
            result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_SCHEMA")
        self.assertIn("VTR Schema Validation Error:", cm.output[0])
        self.assertEqual(cm.output[0].count("\n"), 0)

    @patch("vtr_standard.poc.validator.VTRValidator._parse_sidecar")
    def test_video_not_found(self, mock_parse_sidecar):
        validator = VTRValidator()
        result = validator.validate_container("non_existent_video.mp4")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "VIDEO_NOT_FOUND")

    @patch("vtr_standard.poc.validator.VTRValidator._parse_sidecar")
    def test_video_is_directory(self, mock_parse_sidecar):
        dir_path = "test_dir"
        os.makedirs(dir_path, exist_ok=True)
        try:
            validator = VTRValidator()
            result = validator.validate_container(dir_path)
            self.assertFalse(result.is_valid)
            self.assertIn(result.error_code, ["VIDEO_NOT_FOUND", "READ_ERROR"])
        finally:
            os.rmdir(dir_path)

    def test_sidecar_not_found(self):
        validator = VTRValidator()
        result = validator.validate_container(self.video_file)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "SIDECAR_NOT_FOUND")

    @patch("vtr_standard.poc.validator.VTRValidator._parse_sidecar")
    def test_sidecar_read_error(self, mock_parse_sidecar):
        with open(self.sidecar_file, "w") as f:
            f.write('{"dummy": "data"}')

        validator = VTRValidator()
        mock_parse_sidecar.side_effect = OSError("Disk error")

        with self.assertLogs("vtr_standard.poc.validator", level="ERROR"):
            result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "READ_ERROR")

    def _create_valid_sidecar_dict(self, merkle_root="correct_root", liveness=True):
        return {
            "vtr_version": "2.2",
            "hardware_signature": {
                "public_key": "test_pubkey",
                "zk_proof": "test_proof",
                "liveness_flag": liveness,
                "timestamp": 1234567890.0,
                "merkle_root": merkle_root,
                "location_block_hash": "test_loc",
                "nonce": "test_nonce",
                "previous_signature_link": None,
            },
            "legal_assertions": {
                "x_vtr_ai_training": False,
                "copyright_notice": "test notice",
            },
        }

    def test_merkle_mismatch(self):
        sidecar_data = self._create_valid_sidecar_dict(merkle_root="mismatched_root")
        with open(self.sidecar_file, "w") as f:
            json.dump(sidecar_data, f)

        validator = VTRValidator()
        with patch(
            "vtr_standard.poc.validator.MockPRNU._static_hash_video_content",
            return_value="actual_root",
        ):
            with patch(
                "vtr_standard.poc.validator.MockPRNU.verify_zk_proof", return_value=True
            ):
                result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "MERKLE_MISMATCH")

    def test_liveness_failure(self):
        sidecar_data = self._create_valid_sidecar_dict(liveness=False)
        sidecar_data["hardware_signature"]["merkle_root"] = "actual_root"
        with open(self.sidecar_file, "w") as f:
            json.dump(sidecar_data, f)

        validator = VTRValidator()
        with patch(
            "vtr_standard.poc.validator.MockPRNU._static_hash_video_content",
            return_value="actual_root",
        ):
            with patch(
                "vtr_standard.poc.validator.MockPRNU.verify_zk_proof", return_value=True
            ):
                result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "LIVENESS_FAILURE")

    def test_invalid_signature(self):
        sidecar_data = self._create_valid_sidecar_dict()
        with open(self.sidecar_file, "w") as f:
            json.dump(sidecar_data, f)

        validator = VTRValidator()
        with patch(
            "vtr_standard.poc.validator.MockPRNU.verify_zk_proof", return_value=False
        ):
            with patch(
                "vtr_standard.poc.validator.MockPRNU.calculate_expected_proof",
                return_value="expected_proof",
            ):
                result = validator.validate_container(self.video_file)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_SIGNATURE")
        self.assertEqual(result.details["proof_expected"], "expected_proof")

    def test_validate_container_success(self):
        sidecar_data = self._create_valid_sidecar_dict(merkle_root="actual_root")
        with open(self.sidecar_file, "w") as f:
            json.dump(sidecar_data, f)

        validator = VTRValidator()
        with patch(
            "vtr_standard.poc.validator.MockPRNU._static_hash_video_content",
            return_value="actual_root",
        ):
            with patch(
                "vtr_standard.poc.validator.MockPRNU.verify_zk_proof", return_value=True
            ):
                result = validator.validate_container(self.video_file)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.details["merkle_root"], "actual_root")
        self.assertTrue(result.details["liveness"])


if __name__ == "__main__":
    unittest.main()
