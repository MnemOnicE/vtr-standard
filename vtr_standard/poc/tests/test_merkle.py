import unittest
import tempfile
import os
import hashlib
from vtr_standard.poc.merkle import MerkleTree


class TestMerkleTree(unittest.TestCase):

    def test_empty_file_edge_case(self):
        """Test that a 0-byte empty file correctly yields a prefixed leaf hash."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, temp_file.name)
        temp_file.close()  # Create a 0-byte file and close it so MerkleTree can read it
        tree = MerkleTree(temp_file.name)
        expected_root = hashlib.sha256(b"\x00" + b"").hexdigest()
        self.assertEqual(tree.get_root(), expected_root)

    def test_one_byte_file_edge_case(self):
        """Test that a 1-byte file yields the correct prefixed leaf hash."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, temp_file.name)
        temp_file.write(b"a")
        temp_file.close()
        tree = MerkleTree(temp_file.name)
        expected_root = hashlib.sha256(b"\x00" + b"a").hexdigest()
        self.assertEqual(tree.get_root(), expected_root)

    def test_missing_file_raises_error(self):
        """Test that initializing a MerkleTree with a non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            MerkleTree("non_existent_file_path.txt")


if __name__ == "__main__":
    unittest.main()
