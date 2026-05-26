# VTR Implementers Guide

Welcome to the Video Truth Record (VTR) standard. This guide is designed for external developers who want to build a VTR-compliant system—whether that is a physical camera with a Trusted Execution Environment (TEE), a mobile application, or a verification server.

## Overview

A Video Truth Record (VTR) relies on three core pillars:
1.  **Merkle Tree Hashing:** The video file is chunked and hashed into a Merkle root to guarantee temporal and spatial integrity.
2.  **Hardware Signatures:** Using Photo-Response Non-Uniformity (PRNU) noise or a TEE to sign the content at the sensor level.
3.  **Sidecar Metadata:** A `vtr-sidecar.json` file that accompanies the video file, containing the Merkle root, signatures, location blocks, and liveness flags.

## Protocol vs. Software

This repository (`MnemOnicE/vtr-standard`) serves as the official **Reference Implementation** (Python PoC) and the source of truth for the **Protocol Definitions**.

If you are building in a different language (e.g., Rust, C++, Swift), you do not need to use our Python code. You only need to conform to the formal protocol, which is defined by our JSON Schema and Test Vectors.

## Getting Started

### 1. Understand the JSON Schema
The absolute source of truth for the Sidecar format is the `specs/vtr-sidecar.schema.json` file. Any VTR-compliant file you generate *must* pass validation against this schema.

### 2. Pass the Test Vectors
We provide a suite of Test Vectors in `specs/test-vectors/`. Your implementation (whether it's generating signatures or validating them) should be able to:
- Successfully validate `valid_container.json`.
- Reject `invalid_merkle_mismatch.json` with a specific error indicating a Merkle root mismatch.
- Reject `invalid_zk_malformed.json` with an error indicating an invalid proof.
- Reject `missing_required_fields.json` due to schema non-compliance.

### 3. Implement the Cryptography
- **Hashing:** We strictly require **SHA-256** for all Merkle tree nodes and metadata hashing.
- **Proof Generation (Mock):** Until formal TEE hardware is widely available, our reference mock logic uses **PBKDF2-HMAC-SHA256**. See `MockPRNU` in the Python source for the exact derivation string.

## Reporting Issues
If you encounter protocol-level vulnerabilities or inconsistencies in the standard, please refer to our `SECURITY.md` for disclosure procedures. For standard bug reports in the Python PoC, please open a GitHub Issue.
