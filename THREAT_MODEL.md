# VTR Threat Model & Red Team Analysis

This document formalizes the security assumptions and known threat vectors against the Video Truth Record (VTR) standard. As a protocol claiming "Video Truth", it is imperative that we openly document how the system can be attacked, mitigated, or compromised.

## 1. The Analog Gap (Camera-to-Screen-to-Camera)

**The Attack:** An attacker plays a deepfake or manipulated video on a high-resolution display (e.g., a 4K OLED monitor) and films that screen using a VTR-compliant camera. The resulting VTR file has valid cryptographic signatures and a valid Merkle root because the *camera hardware* genuinely recorded the light hitting its sensor.

**Security Assumption:** VTR currently guarantees that *a specific hardware sensor captured a specific pattern of photons at a specific time*. It does **not** inherently guarantee that those photons originated from a 3D physical scene rather than a 2D digital screen.

**Mitigations:**
- **Active Liveness Detection:** Relying on Depth/LiDAR sensors in mobile devices to reject 2D planar surfaces.
- **Moire Pattern Detection:** Analyzing the PRNU noise for artifacts typical of digital displays.
- *Status:* This remains an open research problem and a primary limitation of hardware-only attestation.

## 2. Replay Attacks

**The Attack:** An attacker intercepts a perfectly valid `video.mp4` and its accompanying `vtr-sidecar.json`. They later attempt to submit or broadcast this exact same pair as if it were a new event or to a different smart contract/verification service.

**Security Assumption:** The sidecar alone does not prove *when* it was submitted to a verifier, only when the camera *claims* it was created.

**Mitigations:**
- **Nonce/Challenge-Response:** The `hardware_signature.nonce` field in the VTR schema is designed to prevent economic replay. When submitting a VTR for a bounty or verification, the verifier must provide a unique challenge nonce that the camera signs *at the time of capture*.
- *Status:* Addressed by protocol design, provided the implementer enforces nonce uniqueness during verification.

## 3. Sensor Spoofing (TEE Compromise)

**The Attack:** An attacker roots their device or extracts the cryptographic keys from the Trusted Execution Environment (TEE). They write a software emulator that takes arbitrary manipulated video frames and generates valid PRNU signatures and Merkle roots, effectively bypassing the camera hardware entirely.

**Security Assumption:** The protocol assumes the TEE and the hardware burned-in keys are physically secure and unextractable.

**Mitigations:**
- **Hardware Root of Trust:** Using secure enclaves (e.g., Apple Secure Enclave, Android TrustZone) that are highly resistant to physical extraction.
- **Revocation Lists:** If a specific device model or sensor ID is known to be compromised, verifiers can check the `hardware_signature.public_key` against a public Certificate Revocation List (CRL).
- *Status:* Relies heavily on the physical security of the OEM hardware. If the hardware is compromised, the protocol is compromised for that specific key.
