import os
from vtr_standard.poc.vtr_container import ensure_dummy_video


def test_ensure_dummy_video_creates_file(tmp_path):
    """Test that ensure_dummy_video creates a 1MB file when it doesn't exist."""
    test_file = tmp_path / "test_video.mp4"
    file_path_str = str(test_file)

    # Ensure file doesn't exist yet
    assert not os.path.exists(file_path_str)

    try:
        # Call the function
        ensure_dummy_video(file_path_str)

        # Verify file exists
        assert os.path.exists(file_path_str)

        # Verify file size is 1MB (1024 * 1024 bytes)
        assert os.path.getsize(file_path_str) == 1024 * 1024
    finally:
        # Cleanup
        if os.path.exists(file_path_str):
            os.remove(file_path_str)


def test_ensure_dummy_video_skips_existing_file(tmp_path):
    """Test that ensure_dummy_video does not overwrite an existing file."""
    test_file = tmp_path / "existing_video.mp4"
    file_path_str = str(test_file)

    # Create a small dummy file (not 1MB)
    test_content = b"existing content"
    with open(file_path_str, "wb") as f:
        f.write(test_content)

    # Verify initial file state
    assert os.path.exists(file_path_str)
    assert os.path.getsize(file_path_str) == len(test_content)

    try:
        # Call the function
        ensure_dummy_video(file_path_str)

        # Verify file still exists
        assert os.path.exists(file_path_str)

        # Verify file size hasn't changed (wasn't overwritten with 1MB)
        assert os.path.getsize(file_path_str) == len(test_content)

        # Verify content hasn't changed
        with open(file_path_str, "rb") as f:
            assert f.read() == test_content
    finally:
        # Cleanup
        if os.path.exists(file_path_str):
            os.remove(file_path_str)
