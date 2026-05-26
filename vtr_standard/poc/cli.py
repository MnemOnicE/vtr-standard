# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import argparse
import sys
import json
import logging
from .vtr_container import VTRContainer
from .validator import VTRValidator

# Configure Logging
logger = logging.getLogger("vtr")


def setup_logging():
    """Configures the logging format and level."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(message)s"
    )  # Simple format for CLI user friendliness
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def print_banner():
    """Logs the VTR warning banner."""
    banner = (
        "\n"
        + "=" * 60
        + "\n"
        + "🎥  ONTOLOGICS VIDEO TRUTH RECORD (VTR) - POC TOOL  🎥\n"
        + "=" * 60
        + "\n"
        + "⚠️  WARNING: RUNNING IN MOCK SENSOR MODE\n"
        + "    This tool uses simulated hardware roots of trust.\n"
        + "    DO NOT USE FOR ACTUAL EVIDENTIARY PURPOSES.\n"
        + "=" * 60
        + "\n"
    )
    logger.warning(banner)


def cmd_sign(args):
    """Handles the 'sign' command."""
    logger.info(f"🔄  Processing video: {args.video_path}")
    if args.sensor_id:
        logger.info(f"🆔  Using Custom Sensor ID: {args.sensor_id}")
    else:
        logger.info("🆔  Using Default Mock Sensor ID")

    # Initialize Container
    # Using a default sensor ID if not provided, or the one from args
    sensor_id = args.sensor_id if args.sensor_id else "MOCK_SENSOR_DEFAULT_001"

    try:
        container = VTRContainer(args.video_path, sensor_id_mock=sensor_id)

        # Determine previous sidecar path for chaining
        prev_sidecar = args.link_to if args.link_to else None

        container.create_sidecar(
            allow_ai_training=args.allow_ai,
            previous_sidecar_path=prev_sidecar,
            overwrite=args.force,
        )
    except FileExistsError as e:
        logger.error(f"❌  Error: {e}")
        logger.error("    Use --force to overwrite the existing sidecar.")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"❌  Error: Video file '{args.video_path}' not found.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌  An unexpected error occurred: {e}")
        sys.exit(1)


def cmd_verify(args):
    """Handles the 'verify' command."""
    if not args.json:
        logger.info(f"🔍  Verifying: {args.video_path}")

    validator = VTRValidator()
    result = validator.validate_container(args.video_path, args.sidecar)

    if args.json:
        # Output pure JSON to stdout
        output = {
            "is_valid": result.is_valid,
            "error_code": result.error_code,
            "message": result.message,
            "details": result.details,
        }
        print(json.dumps(output, indent=4))
        if not result.is_valid:
            sys.exit(1)
        return

    if result.is_valid:
        logger.info("\n✅  VERIFICATION SUCCESSFUL")
        logger.info("    The video content matches the hardware signature.")
        logger.info("-" * 40)
        for key, value in result.details.items():
            logger.info(f"    {key}: {value}")
        logger.info("-" * 40)
    else:
        logger.error("\n❌  VERIFICATION FAILED")
        logger.error(f"    Error Code: {result.error_code}")
        logger.error(f"    Message:    {result.message}")
        if result.details:
            logger.error(f"    Details:    {json.dumps(result.details, indent=4)}")
        sys.exit(1)


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="VTR Proof of Concept CLI")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- SIGN Command ---
    parser_sign = subparsers.add_parser(
        "sign", help="Generate a VTR sidecar for a video file"
    )
    parser_sign.add_argument("video_path", help="Path to the video file")
    parser_sign.add_argument(
        "--sensor-id", help="Simulate a specific Sensor ID", default=None
    )
    parser_sign.add_argument(
        "--allow-ai", action="store_true", help="Allow AI training on this content"
    )
    parser_sign.add_argument(
        "--link-to", help="Path to a previous VTR sidecar to create a Chain of Custody"
    )
    parser_sign.add_argument(
        "--force", action="store_true", help="Overwrite existing sidecar file"
    )
    parser_sign.set_defaults(func=cmd_sign)

    # --- VERIFY Command ---
    parser_verify = subparsers.add_parser(
        "verify", help="Verify a VTR sidecar against a video file"
    )
    parser_verify.add_argument("video_path", help="Path to the video file")
    parser_verify.add_argument(
        "--sidecar", help="Path to the .vtr.json sidecar (optional)", default=None
    )
    parser_verify.add_argument(
        "--json", action="store_true", help="Output result as JSON"
    )
    parser_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()

    print_banner()
    args.func(args)


if __name__ == "__main__":
    main()
