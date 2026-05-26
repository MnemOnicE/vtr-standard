# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import unittest
import hashlib
import os
import tempfile
from typing import List
from vtr_standard.poc.merkle import MerkleTree


class TestMerkleCompatibility(unittest.TestCase):
    """
    Tests ensuring the new iterative Merkle Tree implementation produces
    identical results to the legacy recursive logic.
    """

    def _recursive_compute_root_bytes(self, leaves: List[bytes]) -> bytes:
        if not leaves:
            return b""
        if len(leaves) == 1:
            return leaves[0]

        parents = []
        for i in range(0, len(leaves), 2):
            node1 = leaves[i]
            node2 = leaves[i + 1] if i + 1 < len(leaves) else node1
            combined = node1 + node2
            parents.append(hashlib.sha256(b"\x01" + combined).digest())

        return self._recursive_compute_root_bytes(parents)

    def test_merkle_logic_parity(self):
        """
        Generates random leaves and verifies that the new iterative class
        matches the old recursive helper.
        """
        # Create a dummy file to satisfy MerkleTree init
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"dummy_content")
            temp_path = f.name

        try:
            merkle_instance = MerkleTree(temp_path)

            # Test cases with varying number of leaves
            # We convert test strings to bytes to match the new API
            test_cases = [
                [],  # Empty
                [b"a"],  # Single
                [b"a", b"b"],  # Even
                [b"a", b"b", b"c"],  # Odd
                [str(i).encode() for i in range(10)],  # Larger Even
                [str(i).encode() for i in range(11)],  # Larger Odd
                [str(i).encode() for i in range(100)],  # Big Even
                [str(i).encode() for i in range(101)],  # Big Odd
            ]

            for leaves in test_cases:
                # Pre-hash the leaves to simulate _compute_leaves output
                hashed_leaves = (
                    [hashlib.sha256(b"\x00" + leaf).digest() for leaf in leaves]
                    if leaves
                    else [hashlib.sha256(b"\x00").digest()]
                )

                # Calculate using old recursive logic
                expected_root = self._recursive_compute_root_bytes(hashed_leaves).hex()

                # Calculate using new iterative logic (by injecting leaves directly)
                # We bypass _compute_leaves by calling _compute_root directly
                actual_root = merkle_instance._compute_root(hashed_leaves)

                self.assertEqual(
                    actual_root, expected_root, f"Mismatch for leaves: {leaves}"
                )

        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
