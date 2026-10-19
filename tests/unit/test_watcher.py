"""Unit tests for the watcher module and I/O write stabilization routines."""

from pathlib import Path
import pytest
from watcher import is_valid_target_file, wait_for_file_to_finish_copying


@pytest.mark.unit
def test_is_valid_target_file_extensions() -> None:
    """Validate allowed video format filtering and rejection of non-video formats."""
    # Valid formats
    assert is_valid_target_file(Path("video.mp4")) is True
    assert is_valid_target_file(Path("clip.MOV")) is True
    assert is_valid_target_file(Path("movie.mkv")) is True
    assert is_valid_target_file(Path("reel.m4v")) is True

    # Invalid formats
    assert is_valid_target_file(Path("notes.txt")) is False
    assert is_valid_target_file(Path("document.pdf")) is False
    assert is_valid_target_file(Path("script.sh")) is False
    assert is_valid_target_file(Path("photo.jpg")) is False


@pytest.mark.unit
def test_is_valid_target_file_temporary_and_hidden() -> None:
    """Ensure temporary download artifacts and hidden files are ignored."""
    assert is_valid_target_file(Path(".DS_Store")) is False
    assert is_valid_target_file(Path(".tmp_video.mp4")) is False
    assert is_valid_target_file(Path("video.mp4.crdownload")) is False
    assert is_valid_target_file(Path("video.mp4.part")) is False
    assert is_valid_target_file(Path("video.tmp")) is False
    assert is_valid_target_file(Path("video.swp")) is False


@pytest.mark.unit
def test_wait_for_file_to_finish_copying_success(tmp_path: Path) -> None:
    """Validate stabilization detection success for a fully written file."""
    target_file = tmp_path / "complete_video.mp4"
    target_file.write_bytes(b"\x00" * 1024)

    ready = wait_for_file_to_finish_copying(
        file_path=target_file,
        timeout=2.0,
        check_interval=0.05,
        stable_checks=2,
    )
    assert ready is True


@pytest.mark.unit
def test_wait_for_file_to_finish_copying_non_existent(tmp_path: Path) -> None:
    """Ensure immediate False return if target file does not exist."""
    ghost_file = tmp_path / "ghost.mp4"
    ready = wait_for_file_to_finish_copying(file_path=ghost_file, timeout=0.2)
    assert ready is False


@pytest.mark.unit
def test_wait_for_file_to_finish_copying_zero_byte_timeout(tmp_path: Path) -> None:
    """Ensure zero-byte files are not marked as ready."""
    empty_file = tmp_path / "empty.mp4"
    empty_file.touch()

    ready = wait_for_file_to_finish_copying(
        file_path=empty_file,
        timeout=0.3,
        check_interval=0.05,
        stable_checks=2,
    )
    assert ready is False
