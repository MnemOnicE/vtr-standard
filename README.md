# The Video Truth Record (.vtr) Standard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-VTR--PL-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Reference%20Impl-green?style=flat-square)
![Pydantic](https://img.shields.io/badge/Powered%20by-Pydantic-e92063?style=flat-square&logo=pydantic&logoColor=white)
![Code Style](https://img.shields.io/badge/Code%20Style-Google-blue?style=flat-square)
![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=MnemOnicE_Vtr&metric=code_smells&token=97e48d43be849d33347274d2aa5edbf3a9e2eaf8)
![Bugs](https://sonarcloud.io/api/project_badges/measure?project=MnemOnicE_Vtr&metric=bugs&token=97e48d43be849d33347274d2aa5edbf3a9e2eaf8)](https://sonarcloud.io/summary/new_code?id=MnemOnicE_Vtr) 
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=MnemOnicE_Vtr&metric=ncloc&token=97e48d43be849d33347274d2aa5edbf3a9e2eaf8)](https://sonarcloud.io/summary/new_code?id=MnemOnicE_Vtr)

**Status:** Reference Implementation (V2.2)
**Focus:** Security & Chain of Custody

## Overview

The **Video Truth Record (.vtr)** is an open standard for **Hardware-Attested Media**. It provides a cryptographic binding between video content and the physical sensor that captured it, ensuring authenticity and chain of custody for critical applications.

This standard is designed for **Security Cameras, Dashcams, and Trusted User Devices** where data integrity is paramount. It solves the "Deepfake Defense" problem by verifying the *source hardware* rather than analyzing the pixels.

**Core Principles:**
1.  **Hardware is Truth:** We rely on the physical fingerprint (PRNU) of the sensor, not software signatures.
2.  **Privacy by Design:** Zero-Knowledge Proofs verify the hardware signature without revealing the device's unique serial number or owner identity.
3.  **Chain of Custody:** Each recording is cryptographically linked to the previous one, creating an unbroken timeline of events.

## Features

*   **Hardware Root of Trust:** Leverages unique sensor noise patterns (PRNU) to attest origin.
*   **Tamper-Evident Container:** Merkle Tree hashing ensures frame-by-frame integrity.
*   **Chain of Custody:** "Blockchain-style" linking of file signatures provides audit trails for legal and security contexts.
*   **Liveness Detection:** Protocol support for hardware-level liveness checks (e.g., 3D depth, gyro) to prevent screen recording attacks.

## Repository Structure

The repository is organized as follows:

*   `/vtr_standard`: The canonical Python implementation of the standard.
    *   `/poc`: The **Reference Implementation** (SDK) for hardware integrators.
    *   `/docs`: Technical documentation.

## Installation & Setup

### Prerequisites

*   Python 3.8 or higher.

### Installation

Clone the repository and install the package:

```bash
git clone https://github.com/mnemonice/vtr-standard.git
cd vtr-standard
pip install .
```

This will install the required dependencies (including `pydantic`).

## Usage Guide

### Running the CLI

The Proof of Concept provides a Command Line Interface (CLI) to sign and verify video files.

> **⚠️ WARNING:** The POC runs in **Mock Sensor Mode**. It uses simulated hardware roots of trust and is for demonstration purposes only.

#### Sign a Video

Generate a VTR sidecar (`.vtr.json`) for a video file:

```bash
python3 -m vtr_standard.poc.cli sign my_video.mp4
```

Options:
*   `--sensor-id <ID>`: Simulate a specific sensor ID (e.g., `DEVICE_123`).
*   `--allow-ai`: Flag to allow your data to be used for AI training.
*   `--link-to <PATH>`: Path to a previous sidecar to create a "Chain of Custody" link.

#### Verify a Video

Verify the integrity and authenticity of a VTR container:

```bash
python3 -m vtr_standard.poc.cli verify my_video.mp4
```

This checks:
1.  **File Integrity:** Merkle Tree hashing of the video content.
2.  **Signature Validity:** Cryptographic verification of the ZK proof.
3.  **Schema Compliance:** Ensures the sidecar matches V2.0 specs.

## API Documentation

### `vtr_standard.poc.vtr_container`

Main module for handling VTR containers.

*   `VTRContainer`: Class to manage video and sensor association.
    *   `create_sidecar(allow_ai_training=False)`: Generates the JSON sidecar.

### `vtr_standard.poc.mock_prnu`

Module for simulating hardware sensor logic.

*   `MockPRNU`: Class simulating the hardware root of trust.
    *   `generate_zk_proof(video_path, timestamp)`: Creates a simulated cryptographic proof.
    *   `check_liveness()`: Simulates liveness checks (e.g., 3D depth).

## Contributing

This is an open standard. We welcome contributions from engineers, cryptographers, and privacy advocates.

*See `CONTRIBUTING.md` for the "Poison Pill" anti-forking rules.*

## License

This project is licensed under the **VTR Public License (VTR-PL)**, a reciprocal license designed to protect the integrity of human-generated media. See `LICENSE` for details.
