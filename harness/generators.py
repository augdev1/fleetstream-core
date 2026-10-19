"""Synthetic and corrupted file generator for the FleetStream test harness."""

import os
from pathlib import Path


class DummyVideoGenerator:
    """Factory creating synthetic media files for ingestion testing."""

    # Minimal ISO Base Media File Format header (ftypmp42)
    MP4_HEADER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"

    @classmethod
    def create_valid_video(
        cls,
        target_dir: Path,
        filename: str = "sample_video.mp4",
        size_bytes: int = 1024 * 1024,
    ) -> Path:
        """Create a simulated valid video file with valid container header."""
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename

        with open(file_path, "wb") as f:
            f.write(cls.MP4_HEADER)
            remaining = max(0, size_bytes - len(cls.MP4_HEADER))
            f.write(os.urandom(remaining))

        return file_path

    @classmethod
    def create_corrupted_video(
        cls,
        target_dir: Path,
        filename: str = "corrupted_video.mp4",
        corruption_type: str = "zero_byte",
    ) -> Path:
        """Create anomalous files to test pipeline fault tolerance."""
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename

        if corruption_type == "zero_byte":
            file_path.touch()
        elif corruption_type == "truncated":
            with open(file_path, "wb") as f:
                f.write(b"\x00\x00\x00\x04")
        elif corruption_type == "garbage_header":
            with open(file_path, "wb") as f:
                f.write(b"NOT_A_VIDEO_FILE_HEADER" + os.urandom(512))
        else:
            raise ValueError(f"Unknown corruption type: {corruption_type}")

        return file_path

    @classmethod
    def create_batch(
        cls,
        target_dir: Path,
        count: int = 12,
        prefix: str = "clip",
        extension: str = ".mp4",
    ) -> list[Path]:
        """Generate a batch of N valid video files for Round-Robin tests."""
        paths: list[Path] = []
        for i in range(1, count + 1):
            name = f"{prefix}_{i:03d}{extension}"
            paths.append(cls.create_valid_video(target_dir, filename=name, size_bytes=10 * 1024))
        return paths
