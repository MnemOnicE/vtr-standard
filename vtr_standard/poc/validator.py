# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pydantic import ValidationError
from .mock_prnu import MockPRNU
from .schemas import VTRSidecar

# Configure module-level logger
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Encapsulates the result of a VTR validation attempt.

    Attributes:
        is_valid (bool): True if the container is valid, False otherwise.
        error_code (Optional[str]): A short string identifying the error type (e.g., "INVALID_PROOF").
        message (Optional[str]): A human-readable description of the result.
        details (Dict[str, Any]): Additional context or metadata about the validation.
    """

    is_valid: bool
    error_code: Optional[str] = None
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class VTRValidator:
    """Validates Video Truth Record (VTR) containers and sidecar files.

    This class performs integrity checks, schema validation, and cryptographic
    verification of the hardware signature against the video content.
    """

    def _parse_sidecar(self, sidecar_path: str) -> VTRSidecar:
        with open(sidecar_path, "r") as f:
            raw_data = json.load(f)
        return VTRSidecar.model_validate(raw_data)

    def _verify_crypto_binding(
        self, sidecar: VTRSidecar, video_path: str
    ) -> VerificationResult:
        hw_sig = sidecar.hardware_signature

        public_key = hw_sig.public_key
        zk_proof = hw_sig.zk_proof
        timestamp = hw_sig.timestamp
        previous_signature = hw_sig.previous_signature_link
        liveness_flag = hw_sig.liveness_flag
        location_block_hash = hw_sig.location_block_hash
        nonce = hw_sig.nonce

        # Calculate actual merkle root once to optimize IO
        # This will open the video file and may raise FileNotFoundError or OSError
        actual_merkle_root = MockPRNU._static_hash_video_content(video_path)

        # Verify using MockPRNU static method, passing the pre-calculated hash
        is_signature_valid = MockPRNU.verify_zk_proof(
            public_key=public_key,
            video_path=video_path,
            timestamp=timestamp,
            zk_proof=zk_proof,
            liveness_flag=liveness_flag,
            location_block_hash=location_block_hash,
            nonce=nonce,
            previous_signature=previous_signature,
            video_hash=actual_merkle_root,
        )

        if is_signature_valid:
            # Additional check: Verify the Merkle Root matches the one in sidecar
            sidecar_merkle_root = hw_sig.merkle_root

            if sidecar_merkle_root != actual_merkle_root:
                return VerificationResult(
                    is_valid=False,
                    error_code="MERKLE_MISMATCH",
                    message="Sidecar Merkle Root does not match actual video Merkle Root.",
                    details={
                        "sidecar_root": sidecar_merkle_root,
                        "actual_root": actual_merkle_root,
                    },
                )

            # Strict Liveness Check (Security Feature)
            if not liveness_flag:
                return VerificationResult(
                    is_valid=False,
                    error_code="LIVENESS_FAILURE",
                    message="Hardware liveness check failed. This content is flagged as potentially synthetic.",
                    details={"liveness_flag": False},
                )

            details = {
                "vtr_version": sidecar.vtr_version,
                "timestamp": timestamp,
                "liveness": liveness_flag,
                "merkle_root": actual_merkle_root,
            }
            if previous_signature:
                details["chained_to_previous_proof"] = True
                details["previous_proof_hash"] = previous_signature

            return VerificationResult(
                is_valid=True, message="VTR container is valid.", details=details
            )
        else:
            # Enhanced debugging for failed signatures
            expected_proof = MockPRNU.calculate_expected_proof(
                public_key=public_key,
                video_hash=actual_merkle_root,
                timestamp=timestamp,
                liveness_flag=liveness_flag,
                location_block_hash=location_block_hash,
                nonce=nonce,
                previous_signature=previous_signature,
            )

            return VerificationResult(
                is_valid=False,
                error_code="INVALID_SIGNATURE",
                message="Cryptographic proof verification failed. The content may have been modified or the sidecar does not match the video.",
                details={
                    "timestamp_claimed": timestamp,
                    "liveness_claimed": liveness_flag,
                    "location_hash_claimed": location_block_hash,
                    "actual_merkle_root_calculated": actual_merkle_root,
                    "nonce": nonce,
                    "public_key": public_key,
                    "previous_signature_link": previous_signature,
                    "proof_received": zk_proof,
                    "proof_expected": expected_proof,
                },
            )

    def validate_container(
        self, video_path: str, sidecar_path: Optional[str] = None
    ) -> VerificationResult:
        """Validates a video file against its VTR sidecar.

        Args:
            video_path (str): The path to the raw video file.
            sidecar_path (Optional[str]): The path to the .vtr.json sidecar file.
                If None, it defaults to <video_path>.vtr.json.

        Returns:
            VerificationResult: The outcome of the validation process.
        """
        # 1. Resolve Sidecar Path
        if sidecar_path is None:
            sidecar_path = os.path.abspath(f"{video_path}.vtr.json")
        video_path = os.path.abspath(video_path)

        # 2. Parse Sidecar
        try:
            sidecar = self._parse_sidecar(sidecar_path)
        except FileNotFoundError:
            return VerificationResult(
                is_valid=False,
                error_code="SIDECAR_NOT_FOUND",
                message=f"Sidecar file not found at: {sidecar_path}",
            )
        except json.JSONDecodeError:
            return VerificationResult(
                is_valid=False,
                error_code="INVALID_JSON",
                message="Sidecar file contains invalid JSON.",
            )
        except OSError:
            # Generic read failure - Log internally, sanitize externally
            logger.error("VTR Sidecar Read Error", exc_info=True)
            return VerificationResult(
                is_valid=False,
                error_code="READ_ERROR",
                message="An error occurred while reading or parsing the sidecar file.",
                details={},
            )
        except Exception as e:
            # Pydantic validation failed - Log internally, sanitize externally
            sanitized_error = " | ".join(str(e).splitlines())
            logger.error(f"VTR Schema Validation Error: {sanitized_error}")
            return VerificationResult(
                is_valid=False,
                error_code="INVALID_SCHEMA",
                message="Sidecar file does not match the required VTR schema.",
                details={
                    "validation_error_count": (
                        len(e.errors()) if hasattr(e, "errors") else 1
                    )
                },
            )

        # 3. Cryptographic Verification
        try:
            return self._verify_crypto_binding(sidecar, video_path)
        except FileNotFoundError:
            return VerificationResult(
                is_valid=False,
                error_code="VIDEO_NOT_FOUND",
                message=f"Video file not found at: {video_path}",
            )
        except OSError:
            logger.error("VTR Video Read Error", exc_info=True)
            return VerificationResult(
                is_valid=False,
                error_code="READ_ERROR",
                message="An error occurred while reading the video file.",
                details={},
            )
