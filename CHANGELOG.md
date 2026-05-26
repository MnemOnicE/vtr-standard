# Changelog

All notable changes to the VTR Standard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Governance model and RFC process (`GOVERNANCE.md`).
- Implementers guide (`IMPLEMENTERS.md`).
- Protocol Compliance Test Suite (`specs/test-vectors/`).
- Automated JSON Schema export script (`scripts/export_schema.py`).
- Threat model documentation (`THREAT_MODEL.md`).
- GitHub Actions CI/CD pipeline for automated testing, linting, and security audits.

## [0.1.0] - 2024-05-26

### Added
- Initial Proof of Concept (PoC) for the Video Truth Record (VTR) standard.
- Python reference implementation for `MockPRNU` and `VTRValidator`.
- Merkle tree hashing implementation for video file chunks.
- ZK-proof mock logic for hardware signatures.
- Pydantic schemas for the VTR Sidecar JSON structure.
- RFC-001 outlining the initial protocol proposal.
- Security and roadmap documents.
