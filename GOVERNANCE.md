# VTR Standard Governance & Protocol Standardization

This document outlines the governance model and the Request for Comments (RFC) process for proposing, reviewing, and ratifying changes to the Video Truth Record (VTR) standard.

## 1. Governance Model

The VTR standard is maintained by a core team of maintainers, but it is designed to be an open, industry-adopted standard. Changes to the core protocol, schema, or cryptographic requirements must follow the RFC process.

### Roles
- **Implementers**: Anyone building a VTR-compliant system (cameras, validators, etc.). Implementers are encouraged to provide feedback on RFCs.
- **Contributors**: Anyone who submits code, documentation, or RFCs to the repository.
- **Maintainers**: The core team responsible for reviewing RFCs, merging PRs, and ratifying changes.

## 2. The RFC Process

To ensure protocol stability and interoperability, any significant change to the VTR standard must be proposed via an RFC. This process is inspired by the Python PEP process and the Ethereum EIP process.

### When is an RFC Required?
- Any change to the `vtr-sidecar.schema.json`.
- Changes to the cryptographic requirements (e.g., changing the hashing algorithm from SHA-256).
- Changes to the required metadata fields.
- Backward-incompatible changes to the protocol.

### RFC Lifecycle

1. **Drafting (Draft):**
   - The author creates a draft RFC document in the `docs/rfcs/` directory (e.g., `RFC-002-new-feature.md`).
   - The draft should include:
     - **Title**: A short, descriptive title.
     - **Author**: The name and contact info of the author.
     - **Summary**: A high-level overview of the proposed change.
     - **Motivation**: Why is this change necessary? What problem does it solve?
     - **Specification**: The technical details of the change.
     - **Backward Compatibility**: How does this affect existing implementations?
     - **Security Implications**: Are there any new attack vectors introduced?
   - The author opens a Pull Request (PR) against the `main` branch.

2. **Review (In Review):**
   - The community and maintainers review the draft RFC PR.
   - Feedback is provided, and the author updates the draft as necessary.
   - This phase requires at least two approvals from core maintainers.

3. **Ratification (Ratified or Rejected):**
   - Once consensus is reached, the maintainers will either ratify or reject the RFC.
   - If ratified, the RFC PR is merged, and the changes are considered part of the "planned" standard.

4. **Implementation (Implemented):**
   - The changes described in the ratified RFC are implemented in the Reference Implementation (this repository).
   - Once the implementation is complete and released, the RFC status is updated to "Implemented".

## 3. Versioning

The VTR standard follows [Semantic Versioning](https://semver.org/).
- **MAJOR** version when you make incompatible API/schema changes.
- **MINOR** version when you add functionality in a backwards compatible manner.
- **PATCH** version when you make backwards compatible bug fixes.

All significant changes are documented in the `CHANGELOG.md`.
