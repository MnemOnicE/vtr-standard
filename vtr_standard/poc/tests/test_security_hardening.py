# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import unittest
import os
import json
import logging
from vtr_standard.poc.vtr_container import VTRContainer
from vtr_standard.poc.validator import VTRValidator

# Configure test logger
logging.basicConfig(level=logging.ERROR)


class TestSecurityHardening(unittest.TestCase):
    VIDEO_PATH = "test_security.mp4"
    SIDECAR_PATH = "test_security.mp4.vtr.json"

    def setUp(self):
        # Create dummy video
        with open(self.VIDEO_PATH, "wb") as f:
            f.write(b"Security Test Content")

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.VIDEO_PATH):
            os.remove(self.VIDEO_PATH)
        if os.path.exists(self.SIDECAR_PATH):
            os.remove(self.SIDECAR_PATH)
        # Clear env vars
        if "VTR_TEST_LIVENESS" in os.environ:
            del os.environ["VTR_TEST_LIVENESS"]

    def test_tamper_resistance_liveness(self):
        """Test that modifying liveness_flag invalidates the signature."""
        # 1. Sign (with liveness=True)
        os.environ["VTR_TEST_LIVENESS"] = "true"
        container = VTRContainer(self.VIDEO_PATH, "SENSOR_TEST")
        container.create_sidecar()

        # 2. Modify sidecar: Set liveness to False
        with open(self.SIDECAR_PATH, "r") as f:
            data = json.load(f)

        # Sanity check: it was true
        self.assertTrue(data["hardware_signature"]["liveness_flag"])

        # Tamper: Set to False
        data["hardware_signature"]["liveness_flag"] = False
        with open(self.SIDECAR_PATH, "w") as f:
            json.dump(data, f)

        # 3. Verify
        validator = VTRValidator()
        result = validator.validate_container(self.VIDEO_PATH)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_SIGNATURE")  # Crypto fail

    def test_strict_liveness_check(self):
        """Test that verification fails if liveness is authentic but False."""
        # 1. Sign with Liveness=False
        os.environ["VTR_TEST_LIVENESS"] = "false"
        container = VTRContainer(self.VIDEO_PATH, "SENSOR_TEST")
        container.create_sidecar()

        # 2. Verify
        validator = VTRValidator()
        result = validator.validate_container(self.VIDEO_PATH)

        # 3. Assert failure
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "LIVENESS_FAILURE")

    def test_location_binding(self):
        """Test that modifying location_block_hash invalidates signature."""
        # 1. Sign
        os.environ["VTR_TEST_LIVENESS"] = "true"
        container = VTRContainer(self.VIDEO_PATH, "SENSOR_TEST")
        container.create_sidecar()

        # 2. Tamper
        with open(self.SIDECAR_PATH, "r") as f:
            data = json.load(f)

        data["hardware_signature"]["location_block_hash"] = "deadbeef" * 8

        with open(self.SIDECAR_PATH, "w") as f:
            json.dump(data, f)

        # 3. Verify
        validator = VTRValidator()
        result = validator.validate_container(self.VIDEO_PATH)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_SIGNATURE")

    def test_replay_protection_nonce(self):
        """Test that modifying the nonce invalidates the signature."""
        # 1. Sign
        os.environ["VTR_TEST_LIVENESS"] = "true"
        container = VTRContainer(self.VIDEO_PATH, "SENSOR_TEST")
        container.create_sidecar()

        # 2. Tamper: Change Nonce
        with open(self.SIDECAR_PATH, "r") as f:
            data = json.load(f)

        # Sanity check: nonce exists
        self.assertIn("nonce", data["hardware_signature"])

        # Modify nonce
        data["hardware_signature"]["nonce"] = "modified_nonce_123"

        with open(self.SIDECAR_PATH, "w") as f:
            json.dump(data, f)

        # 3. Verify
        validator = VTRValidator()
        result = validator.validate_container(self.VIDEO_PATH)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_SIGNATURE")

    def test_success_path(self):
        """Test normal success path."""
        os.environ["VTR_TEST_LIVENESS"] = "true"
        container = VTRContainer(self.VIDEO_PATH, "SENSOR_TEST")
        container.create_sidecar()

        validator = VTRValidator()
        result = validator.validate_container(self.VIDEO_PATH)

        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
