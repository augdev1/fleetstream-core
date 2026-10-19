"""Hermetic Test Harness suite for FleetStream distribution engine.

Validates core business rules:
- Scenario 1: Balanced distribution of 10 videos across 4 iPhones (3, 3, 2, 2)
- Scenario 2: Paired metadata (.json) integrity and schema compliance
- Scenario 3: Fault tolerance for disallowed file extensions (.txt, .pdf)
- Scenario 4: Idempotent execution with empty inbox
"""

import json
from pathlib import Path
from typing import Any
import pytest
from core.distributor import DistributionEngine
from core.models import DistributionStatus, VideoMetadata


class MediaFileFactory:
    """Factory creating synthetic test media files inside inbox."""

    MP4_HEADER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"

    def __init__(self, inbox_dir: Path) -> None:
        self.inbox_dir = inbox_dir

    def create_video(self, filename: str = "video.mp4", size_bytes: int = 1024) -> Path:
        """Create a simulated .mp4 file with valid ftyp header in inbox."""
        file_path = self.inbox_dir / filename
        with open(file_path, "wb") as f:
            f.write(self.MP4_HEADER)
            remaining = max(0, size_bytes - len(self.MP4_HEADER))
            f.write(b"\x00" * remaining)
        return file_path

    def create_batch_videos(self, count: int, prefix: str = "clip") -> list[Path]:
        """Create an ordered batch of N synthetic .mp4 videos in inbox."""
        return [
            self.create_video(filename=f"{prefix}_{i:02d}.mp4", size_bytes=1024)
            for i in range(1, count + 1)
        ]

    def create_invalid_file(self, filename: str, content: str = "invalid content") -> Path:
        """Create non-video files (.txt, .pdf, etc.) in inbox."""
        file_path = self.inbox_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path


@pytest.fixture
def test_dirs(tmp_path: Path) -> dict[str, Any]:
    """Temporary fixture provisioning isolated inbox and 4 iPhone target folders."""
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    devices_dir = tmp_path / "devices"
    devices_dir.mkdir(parents=True, exist_ok=True)

    device_names = ["iphone_01", "iphone_02", "iphone_03", "iphone_04"]
    device_paths: list[Path] = []
    for name in device_names:
        dev_path = devices_dir / name
        dev_path.mkdir(parents=True, exist_ok=True)
        device_paths.append(dev_path)

    return {
        "root": tmp_path,
        "inbox": inbox_dir,
        "devices_dir": devices_dir,
        "devices": device_paths,
        "device_names": device_names,
    }


@pytest.fixture
def media_factory(test_dirs: dict[str, Any]) -> MediaFileFactory:
    """Fixture providing helper factory to create valid and invalid files."""
    return MediaFileFactory(test_dirs["inbox"])


@pytest.mark.harness
def test_scenario_1_uniform_distribution(
    test_dirs: dict[str, Any],
    media_factory: MediaFileFactory,
) -> None:
    """Scenario 1: Balanced distribution of 10 videos across 4 iPhones (3, 3, 2, 2)."""
    created_videos = media_factory.create_batch_videos(count=10, prefix="video")
    assert len(created_videos) == 10

    engine = DistributionEngine(
        inbox_dir=test_dirs["inbox"],
        devices_dir=test_dirs["devices_dir"],
    )
    summary = engine.process_inbox()

    device_counts = [
        len(list(dev.glob("*.mp4"))) for dev in test_dirs["devices"]
    ]

    assert sum(device_counts) == 10, (
        f"Distributed video count ({sum(device_counts)}) does not match generated total (10)."
    )

    # 10 items in 4 buckets must partition into [3, 3, 2, 2]
    assert sorted(device_counts, reverse=True) == [3, 3, 2, 2], (
        f"Imbalanced distribution across iPhones: {device_counts}, expected [3, 3, 2, 2]"
    )

    remaining_inbox = list(test_dirs["inbox"].glob("*.mp4"))
    assert len(remaining_inbox) == 0, (
        f"Residual files found in inbox: {remaining_inbox}"
    )

    assert summary is not None
    assert summary.distributed == 10


@pytest.mark.harness
def test_scenario_2_metadata_integrity(
    test_dirs: dict[str, Any],
    media_factory: MediaFileFactory,
) -> None:
    """Scenario 2: Metadata integrity (valid paired .json for each moved video)."""
    media_factory.create_batch_videos(count=4, prefix="promo")

    engine = DistributionEngine(
        inbox_dir=test_dirs["inbox"],
        devices_dir=test_dirs["devices_dir"],
    )
    engine.process_inbox()

    total_validated = 0
    for dev in test_dirs["devices"]:
        videos = list(dev.glob("*.mp4"))
        for video_path in videos:
            json_path = video_path.with_suffix(".json")

            assert json_path.exists(), f"Paired sidecar .json missing for video {video_path.name}"

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            assert "original_filename" in data and data["original_filename"]
            assert data["distributed_filename"] == video_path.name
            assert data["target_device"] == dev.name
            assert "suggested_caption" in data
            assert isinstance(data.get("hashtags"), list) and len(data["hashtags"]) > 0
            assert "timestamp" in data and data["timestamp"]
            assert data["status"] in ("distributed", DistributionStatus.DISTRIBUTED)

            metadata = VideoMetadata.model_validate(data)
            assert metadata.distributed_filename == video_path.name
            assert metadata.target_device == dev.name
            assert metadata.status == DistributionStatus.DISTRIBUTED
            total_validated += 1

    assert total_validated == 4, f"Expected 4 validated pairs, got {total_validated}"


@pytest.mark.harness
def test_scenario_3_fault_tolerance_invalid_extensions(
    test_dirs: dict[str, Any],
    media_factory: MediaFileFactory,
) -> None:
    """Scenario 3: Fault tolerance (disallowed inbox files are skipped, not moved)."""
    media_factory.create_video("clip_01.mp4")
    media_factory.create_video("clip_02.mp4")

    media_factory.create_invalid_file("notes.txt", "arbitrary text")
    media_factory.create_invalid_file("contract.pdf", "%PDF-1.4 mock")
    media_factory.create_invalid_file("script.sh", "echo 'test'")

    engine = DistributionEngine(
        inbox_dir=test_dirs["inbox"],
        devices_dir=test_dirs["devices_dir"],
    )

    summary = engine.process_inbox()

    distributed_videos = [
        f for dev in test_dirs["devices"] for f in dev.glob("*.mp4")
    ]
    assert len(distributed_videos) == 2

    for dev in test_dirs["devices"]:
        invalid_moved = [
            f for f in dev.iterdir()
            if f.suffix.lower() in {".txt", ".pdf", ".sh"}
        ]
        assert len(invalid_moved) == 0, (
            f"Disallowed files were moved to {dev.name}: {invalid_moved}"
        )

    total_jsons = [f for dev in test_dirs["devices"] for f in dev.glob("*.json")]
    assert len(total_jsons) == 2

    assert (test_dirs["inbox"] / "notes.txt").exists()
    assert (test_dirs["inbox"] / "contract.pdf").exists()
    assert (test_dirs["inbox"] / "script.sh").exists()

    assert summary is not None
    assert summary.distributed == 2
    assert summary.skipped >= 3


@pytest.mark.harness
def test_scenario_4_empty_inbox(test_dirs: dict[str, Any]) -> None:
    """Scenario 4: Empty inbox returns zeroed counters without exceptions."""
    assert len(list(test_dirs["inbox"].iterdir())) == 0

    engine = DistributionEngine(
        inbox_dir=test_dirs["inbox"],
        devices_dir=test_dirs["devices_dir"],
    )

    summary = engine.process_inbox()

    assert summary is not None
    assert summary.distributed == 0
    assert summary.processed == 0
    assert summary.failed == 0
    assert summary.skipped == 0

    for dev in test_dirs["devices"]:
        assert len(list(dev.iterdir())) == 0
