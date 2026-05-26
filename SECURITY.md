# Security Policy

## Reporting a Vulnerability

We take the security of the Video Truth Record (VTR) protocol and its reference implementations seriously.

If you discover a vulnerability, please **DO NOT** open a public issue.

Instead, please send an email to: **security@ontologics.com**

### Scope

Please clearly distinguish in your report whether the vulnerability is:
1.  **Software-Level**: A bug in the Python PoC code (e.g., buffer overflow, bad input validation, dependency vulnerability).
2.  **Protocol-Level**: A flaw in the mathematical assumptions or architecture of the standard itself (e.g., Merkle tree collision attack, ZK-proof forgery, or replay attack vectors).

Protocol-Level vulnerabilities are extremely critical as they affect all implementers of the VTR standard, not just the Python reference implementation.

### Response Time
We will strive to acknowledge receipt of your vulnerability report within 48 hours and provide an estimated timeline for triage and resolution.
