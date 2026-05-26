# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import json
import time
import os
import logging
import secrets
from .mock_prnu import MockPRNU
from .schemas import VTRSidecar, HardwareSignature, LegalAssertions

# Configure module-level logger
logger = logging.getLogger(__name__)


class VTRContainer:
    """Manages the creation of Video Truth Record (VTR) containers.

    This is the canonical V2.1 generator. It handles the association of a raw video
    file with a hardware root of trust (via MockPRNU), generating a sidecar file
    containing cryptographic proofs and legal assertions.
    """

    def __init__(self, raw_video_path, sensor_id_mock):
        """Initializes the VTRContainer."""
        self.video_path = raw_video_path
        self.timestamp = time.time()
        # Initialize the hardware root of trust (the Merged MockPRNU)
        self.prnu = MockPRNU(sensor_id_mock)

    def create_sidecar(
        self, allow_ai_training=False, previous_sidecar_path=None, overwrite=False
    ):
        """Generates the .vtr sidecar JSON file.

        Args:
            allow_ai_training (bool, optional): A flag indicating whether the content
                may be used for AI training datasets. Defaults to False.
            previous_sidecar_path (str, optional): Path to the previous sidecar in the chain.
            overwrite (bool, optional): If True, overwrites an existing sidecar file. Defaults to False.

        Returns:
            None: This method writes the sidecar file to disk.
        """
        filename = f"{self.video_path}.vtr.json"
        if not overwrite and os.path.exists(filename):
            raise FileExistsError(f"Sidecar file already exists: {filename}")

        previous_signature = None
        if previous_sidecar_path:
            try:
                # STRICT CHAIN OF CUSTODY CHECK
                # If a previous link is requested, it MUST be valid.
                with open(previous_sidecar_path, "r", encoding="utf-8") as f:
                    prev_data = json.load(f)

                # We attempt to validate the previous sidecar against the schema to ensure integrity
                try:
                    prev_model = VTRSidecar.model_validate(prev_data)
                    previous_signature = prev_model.hardware_signature.zk_proof
                except Exception as e:
                    # Fallback to loose extraction if strict schema fails?
                    # Sentinel says: NO. If schema is invalid, the chain is suspect.
                    # However, to be slightly pragmatic for cross-version compatibility (if handled),
                    # we might inspect the error. For now, we enforce structure.
                    raise ValueError(f"Previous sidecar schema validation failed: {e}")

                if not previous_signature:
                    raise ValueError(
                        f"Could not extract zk_proof from {previous_sidecar_path}"
                    )

            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Previous sidecar not found at: {previous_sidecar_path}"
                )
            except json.JSONDecodeError:
                raise ValueError(
                    f"Previous sidecar is not valid JSON: {previous_sidecar_path}"
                )
            except Exception as e:
                # Re-raise to halt execution. Chain of Custody cannot be optional if requested.
                raise ValueError(f"Chain of Custody Failure: {e}") from e

        # --- 1. Hardware Signature Components ---
        # Calculate liveness and location first to bind them in the proof
        liveness_flag = self.prnu.check_liveness()

        if not liveness_flag:
            logger.warning(
                "⚠️  WARNING: Liveness check FAILED. The generated VTR will be cryptographically valid but flagged as 'Synthetic' by validators."
            )

        location_block_hash = self.prnu.calculate_location_block_hash()

        # Generate Nonce for Replay Protection
        nonce = secrets.token_hex(16)

        # Calculate Merkle Root once to optimize IO
        actual_merkle_root = self.prnu._hash_video_content(self.video_path)

        zk_proof = self.prnu.generate_zk_proof(
            self.video_path,
            self.timestamp,
            liveness_flag=liveness_flag,
            location_block_hash=location_block_hash,
            nonce=nonce,
            previous_signature=previous_signature,
            video_hash=actual_merkle_root,
        )

        hardware_signature = HardwareSignature(
            public_key=self.prnu.get_public_key(),
            zk_proof=zk_proof,
            liveness_flag=liveness_flag,
            timestamp=self.timestamp,
            merkle_root=actual_merkle_root,
            location_block_hash=location_block_hash,
            previous_signature_link=previous_signature,
            nonce=nonce,
        )

        # --- 2. Construct Final Sidecar ---
        legal_assertions = LegalAssertions(
            x_vtr_ai_training=allow_ai_training,
            copyright_notice="Scraping this data without consent violates DMCA Sec 1202.",
        )

        sidecar = VTRSidecar(
            vtr_version="2.2",
            hardware_signature=hardware_signature,
            legal_assertions=legal_assertions,
        )

        # Write to disk
        with open(filename, "w", encoding="utf-8") as f:
            f.write(sidecar.model_dump_json(indent=4))

        logger.info(f"✅ VTR Sidecar created: {filename}")
        logger.info(f"🔒 AI Training Permission: {allow_ai_training}")


def ensure_dummy_video(filename):
    """Auto-generate dummy files if they don't exist.

    Generates a 1MB file of random bytes to simulate video content.
    """
    if not os.path.exists(filename):
        parent_dir = os.path.dirname(filename)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        logger.info(f"🎥 Generating dummy video file: {filename}")
        # Generate 1MB of random bytes to simulate video content
        with open(filename, "wb") as f:
            f.write(os.urandom(1024 * 1024))


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    logger.info("--- OntoLogics VTR Generator v2.0 (Merged POC) ---")

    ensure_dummy_video("first_video.mp4")
    ensure_dummy_video("second_video.mp4")

    # Simulate a "Potato Phone" capturing a video (First Link in the Chain)
    camera_1 = VTRContainer("first_video.mp4", sensor_id_mock="SENSOR_PRNU_XYZ_999")
    camera_1.create_sidecar(allow_ai_training=True)

    # Simulate capturing a subsequent video (Second Link in the Chain)
    camera_2 = VTRContainer("second_video.mp4", sensor_id_mock="SENSOR_PRNU_XYZ_999")
    # Link to the first sidecar to create the Chain of Custody
    camera_2.create_sidecar(
        allow_ai_training=False, previous_sidecar_path="first_video.mp4.vtr.json"
    )
