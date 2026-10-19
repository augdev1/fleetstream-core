"""Specialized assertion helpers for FleetStream test harness."""

import json
from pathlib import Path
from core.models import VideoMetadata


def assert_round_robin_balanced(
    devices_dir: Path,
    expected_total: int,
    tolerance: int = 1,
) -> None:
    """Verify that video files are evenly balanced across device targets."""
    device_folders = [d for d in devices_dir.iterdir() if d.is_dir()]
    assert len(device_folders) > 0, "No device target directories found."

    counts: dict[str, int] = {}
    for folder in device_folders:
        videos = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv"}
        ]
        counts[folder.name] = len(videos)

    total_counted = sum(counts.values())
    assert total_counted == expected_total, (
        f"Expected {expected_total} total distributed videos, found {total_counted}. "
        f"Counts per device: {counts}"
    )

    max_count = max(counts.values())
    min_count = min(counts.values())
    diff = max_count - min_count

    assert diff <= tolerance, (
        f"Round-Robin imbalance detected. Max difference: {diff} (allowed: {tolerance}). "
        f"Device counts: {counts}"
    )


def assert_paired_json_valid(video_path: Path, expected_device: str | None = None) -> VideoMetadata:
    """Validate that the paired .json file exists and strictly satisfies VideoMetadata schema."""
    json_path = video_path.with_suffix(".json")
    assert json_path.exists(), f"Paired metadata sidecar not found: {json_path}"
    assert json_path.is_file(), f"Metadata path is not a file: {json_path}"

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    metadata = VideoMetadata.model_validate(data)

    assert metadata.distributed_filename == video_path.name, (
        f"Metadata filename ({metadata.distributed_filename}) does not match physical video ({video_path.name})"
    )

    if expected_device:
        assert metadata.target_device == expected_device, (
            f"Metadata device ({metadata.target_device}) does not match expected ({expected_device})"
        )

    assert len(metadata.hashtags) > 0, "Generated metadata contains empty hashtags"
    assert metadata.timestamp is not None, "Timestamp missing in metadata"

    return metadata


def assert_no_leftover_in_inbox(inbox_dir: Path) -> None:
    """Ensure no processed media files remain residual in the inbox folder."""
    remaining = [
        f for f in inbox_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv", ".json"}
    ]
    assert len(remaining) == 0, f"Residual files found in inbox after processing: {remaining}"
