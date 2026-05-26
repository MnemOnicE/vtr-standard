# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import functools
import hashlib
import hmac
import os
import secrets
from typing import Optional

from .merkle import MerkleTree


class MockPRNU:
    """Simulates the Hardware Root of Trust and PRNU (Photo Response Non-Uniformity) logic.

    This is the canonical V2.0 implementation, merging real Merkle hashing
    with V2.2 schema mock functions (Liveness, Location).
    """

    def __init__(self, sensor_id):
        """Initializes the MockPRNU instance."""
        self.sensor_id = sensor_id

        # SECURITY PATCH: Fail if running in PRODUCTION mode
        if os.environ.get("VTR_ENV") == "PRODUCTION":
            raise RuntimeError(
                "CRITICAL SECURITY VIOLATION: MockPRNU loaded in PRODUCTION environment. "
                "This module is for testing only. Use RealPRNU interface."
            )

        # Mock GPS Block used for location hashing.
        # Check env var for deterministic override: VTR_TEST_GPS
        self.gps_salt = os.environ.get("VTR_TEST_GPS", "34.0522,118.2437")

        # Snapshot KDF parameters to ensure instance stability
        self._kdf_salt, self._kdf_iterations = self._get_kdf_params()

    def get_public_key(self):
        """Derives a simulated Public Verification Key from the sensor ID."""
        return self._derive_pbkdf2(self.sensor_id, self._kdf_salt, self._kdf_iterations)

    def _hash_video_content(self, video_path):
        """Calculates the Merkle Root of the video file content."""
        return MockPRNU._static_hash_video_content(video_path)

    def generate_zk_proof(
        self,
        video_path,
        timestamp,
        liveness_flag,
        location_block_hash,
        nonce,
        previous_signature=None,
        video_hash=None,
    ):
        """Simulates generating a Zero-Knowledge Proof (ZKP) for V2.0.

        Binds the Verification Key, Merkle Root, Timestamp, Liveness, Location,
        Nonce (Replay Protection), and optional Chain-of-Custody link.

        Args:
            video_path (str): Path to the video file (used if video_hash is None).
            timestamp (float): The timestamp of capture.
            liveness_flag (bool): The liveness status.
            location_block_hash (str): The hash of the location block.
            nonce (str): The replay protection nonce.
            previous_signature (Optional[str]): The proof of the previous link.
            video_hash (Optional[str]): Pre-calculated Merkle Root. If provided, video_path is ignored for hashing.

        Returns:
            str: The simulated zk_proof string.
        """
        # 1. Calculate Hash of the actual Video Content (Merkle Root)
        if video_hash is None:
            video_hash = self._hash_video_content(video_path)

        # 2. Derive the Public Verification Key
        verification_key = self.get_public_key()

        # 3. Create the Proof
        return self.calculate_expected_proof(
            public_key=verification_key,
            video_hash=video_hash,
            timestamp=timestamp,
            liveness_flag=liveness_flag,
            location_block_hash=location_block_hash,
            nonce=nonce,
            previous_signature=previous_signature,
        )

    def check_liveness(self):
        """Simulates the Passive Liveness / Anti-Matrix Check.

        Now supports deterministic control via VTR_TEST_LIVENESS env var.
        """
        env_liveness = os.environ.get("VTR_TEST_LIVENESS")
        if env_liveness is not None:
            # Accepts "true", "1", "pass" as True; anything else as False (if
            # set)
            return env_liveness.strip().lower() in ("true", "1", "pass")

        # Mock logic: Randomly pass for demo purposes
        # SECURITY FIX: Use secrets.choice() for cryptographically secure and efficient randomness.
        # This replaces the inefficient instantiation of SystemRandom() and
        # maintains the mock's intent.
        return secrets.choice([True] + [False] * 9)
        # SECURITY FIX: Use secrets.SystemRandom() for cryptographically secure
        # randomness.
        liveness_score = secrets.SystemRandom().uniform(0.8, 1.0)
        return liveness_score > 0.9

    def calculate_location_block_hash(self):
        """Calculates the hash of the location data (salted)."""
        return self._derive_pbkdf2(self.gps_salt, self._kdf_salt, self._kdf_iterations)

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _get_kdf_params():
        """Centralized helper to retrieve KDF parameters from the environment."""
        env_salt = os.environ.get("VTR_KDF_SALT")
        salt = env_salt.encode() if env_salt else b"vtr_kdf_salt_2025_canonical"
        try:
            iterations = max(100000, int(os.environ.get("VTR_KDF_ITERATIONS", 100000)))
        except ValueError:
            iterations = 100000
        return salt, iterations

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _derive_pbkdf2(data: str, salt: bytes, iterations: int) -> str:
        """Derives a hex string using PBKDF2-HMAC-SHA256 with caching.

        Args:
            data (str): The input string to be hashed.
            salt (bytes): The salt used for PBKDF2.
            iterations (int): The number of PBKDF2 iterations.

        Returns:
            str: The hex string of the derived PBKDF2-HMAC-SHA256 key.
        """
        """Derives a hex string using PBKDF2-HMAC-SHA256 with caching."""
        return hashlib.pbkdf2_hmac("sha256", data.encode(), salt, iterations).hex()

    @staticmethod
    def _static_hash_video_content(video_path):
        """Static helper to hash video content using Merkle Tree."""
        return MerkleTree(video_path).get_root()

    @staticmethod
    def calculate_expected_proof(
        public_key: str,
        video_hash: str,
        timestamp: float,
        liveness_flag: bool,
        location_block_hash: str,
        nonce: str,
        previous_signature: Optional[str] = None,
    ) -> str:
        """Calculates the expected zk_proof string based on the provided inputs.

        Args:
            public_key (str): The public verification key.
            video_hash (str): The Merkle Root of the video content.
            timestamp (float): The timestamp of capture.
            liveness_flag (bool): The liveness status.
            location_block_hash (str): The hash of the location block.
            nonce (str): The replay protection nonce.
            previous_signature (Optional[str]): The proof of the previous link.

        Returns:
            str: The expected zk_proof string.
        """
        # Security Fix: Use length-prefixed strings to prevent canonicalization attacks
        # We cast liveness_flag (bool) to lowercase string for consistent
        # hashing.
        fields = [
            public_key,
            str(timestamp),
            video_hash,
            "true" if liveness_flag else "false",
            location_block_hash,
            nonce,
            previous_signature or "",
        ]

        # Format as: length:value
        data_to_sign = "".join(f"{len(str(f))}:{f}" for f in fields)

        proof_hash = hashlib.sha256(data_to_sign.encode()).hexdigest()
        return f"zk_snark_{proof_hash[:16]}"

    @staticmethod
    def verify_zk_proof(
        public_key,
        video_path,
        timestamp,
        zk_proof,
        liveness_flag,
        location_block_hash,
        nonce,
        previous_signature=None,
        video_hash=None,
    ):
        """Verifies a simulated Zero-Knowledge Proof.

        Now requires liveness_flag, location_block_hash, and nonce to reconstruct the hash.

        Args:
            public_key (str): The public verification key.
            video_path (str): Path to the video file (used if video_hash is None).
            timestamp (float): The timestamp of capture.
            zk_proof (str): The proof string to verify.
            liveness_flag (bool): The liveness status.
            location_block_hash (str): The hash of the location block.
            nonce (str): The replay protection nonce.
            previous_signature (Optional[str]): The proof of the previous link.
            video_hash (Optional[str]): Pre-calculated Merkle Root. If provided, video_path is ignored for hashing.

        Returns:
            bool: True if the proof is valid, False otherwise.
        """
        if video_hash is None:
            video_hash = MockPRNU._static_hash_video_content(video_path)

        expected_proof = MockPRNU.calculate_expected_proof(
            public_key=public_key,
            video_hash=video_hash,
            timestamp=timestamp,
            liveness_flag=liveness_flag,
            location_block_hash=location_block_hash,
            nonce=nonce,
            previous_signature=previous_signature,
        )

        return hmac.compare_digest(expected_proof, zk_proof)
