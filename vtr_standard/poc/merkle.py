# Copyright (c) 2025 OntoLogics (Seth & Axion). All rights reserved.
# Licensed under the VTR Public License (VTR-PL), Version 1.0 (the "License").
# A copy of the License is available in the root/vtr_standard/poc/LICENSE file.
# This code is distributed WITHOUT ANY WARRANTY.

import os
import hashlib
import threading
import logging
from queue import Queue
from typing import List, Generator

# Configure module-level logger
logger = logging.getLogger(__name__)


class AsyncFileStream:
    """
    Reads a file in a background thread to keep the IO pipe full
    while the main thread processes the data.
    """

    def __init__(self, file_path: str, chunk_size: int):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.queue: Queue = Queue(maxsize=4)  # Keep 4 chunks in memory (Backpressure)
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._read_file_worker, daemon=True)

    def _read_file_worker(self):
        try:
            with open(self.file_path, "rb") as f:
                while not self.stop_event.is_set():
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    self.queue.put(chunk)  # Blocks if queue is full
        except Exception as e:
            # Log the error and allow the consumer to handle EOF or failure
            logger.error(f"IO Failure in AsyncFileStream: {e}")
            # We fail silently here regarding the queue flow, just ending the stream.
            # The main thread handles file existence check beforehand.
            pass
        finally:
            self.queue.put(None)  # Sentinel value to signal EOF

    def stream(self) -> Generator[bytes, None, None]:
        self.thread.start()
        while True:
            chunk = self.queue.get()
            if chunk is None:
                break
            yield chunk


class MerkleTree:
    """
    A high-performance implementation of a Merkle Tree for video file integrity.
    Uses Async IO (Producer-Consumer) to maximize throughput.
    """

    def __init__(self, file_path: str, chunk_size: int = 4 * 1024 * 1024):
        """
        Initialize the Merkle Tree by reading the file and computing the root.

        Args:
            file_path (str): Path to the video file.
            chunk_size (int): Size of chunks in bytes. Defaults to 4MB for NVMe/SSD optimization.
        """
        self.file_path = file_path
        self.chunk_size = chunk_size

        # Explicitly check for file existence to preserve strict error handling contract
        # This ensures FileNotFoundError is raised immediately, matching legacy behavior.
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(
                f"File not found or is not a regular file: {self.file_path}"
            )

        self.leaves = self._compute_leaves()
        self.root = self._compute_root(self.leaves)

    def _compute_leaves(self) -> List[bytes]:
        """Reads the file in chunks using AsyncFileStream and computes SHA256 hash for each chunk."""
        hashes = []
        streamer = AsyncFileStream(self.file_path, self.chunk_size)
        leaf_hasher = hashlib.sha256(b"\x00")

        for chunk in streamer.stream():
            h = leaf_hasher.copy()
            h.update(chunk)
            hashes.append(h.digest())

        if not hashes:
            return [hashlib.sha256(b"\x00").digest()]

        return hashes

    def _compute_root(self, leaves: List[bytes]) -> str:
        """Iteratively computes the Merkle Root from a list of hashes."""
        current_level = leaves
        if not current_level:
            return ""

        internal_hasher = hashlib.sha256(b"\x01")
        while len(current_level) > 1:
            next_len = (len(current_level) + 1) // 2
            for i in range(next_len):
                idx = i * 2
                node1 = current_level[idx]
                # Handle odd number of leaves by duplicating the last one
                node2 = (
                    current_level[idx + 1] if idx + 1 < len(current_level) else node1
                )

                h = internal_hasher.copy()
                h.update(node1)
                h.update(node2)
                current_level[i] = h.digest()
            del current_level[next_len:]

        # Final result is returned as a hex string for public API compatibility
        return current_level[0].hex()

    def get_root(self) -> str:
        """Returns the hexadecimal Merkle Root."""
        return self.root
