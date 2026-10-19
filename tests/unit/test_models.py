"""Unit tests for data models and schema validation."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from core.models import Device, DistributionStatus, VideoMetadata


@pytest.mark.unit
def test_video_metadata_valid_instantiation() -> None:
    """Validate valid creation and JSON serialization of VideoMetadata."""
    metadata = VideoMetadata(
        original_filename="promo_01.mp4",
        distributed_filename="clip_001.mp4",
        target_device="iphone_01",
        suggested_caption="New exclusive drop. Link in bio.",
        hashtags=["#viral", "#fyp", "#trending"],
        file_size_bytes=1048576,
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status=DistributionStatus.DISTRIBUTED,
        extra_payload={"source_campaign": "alpha_launch"},
    )

    assert metadata.target_device == "iphone_01"
    assert metadata.status == DistributionStatus.DISTRIBUTED
    assert len(metadata.hashtags) == 3

    # Round-trip JSON validation
    json_str = metadata.model_dump_json()
    reloaded = VideoMetadata.model_validate_json(json_str)
    assert reloaded == metadata


@pytest.mark.unit
def test_video_metadata_negative_filesize_rejected() -> None:
    """Ensure negative file size values are rejected by schema."""
    with pytest.raises(ValidationError):
        VideoMetadata(
            original_filename="corrupted.mp4",
            distributed_filename="clip_corrupted.mp4",
            target_device="iphone_02",
            file_size_bytes=-100,
        )


@pytest.mark.unit
def test_device_model() -> None:
    """Validate Device node representation model."""
    dev = Device(device_id="iphone_03", path="/devices/iphone_03", is_active=True)
    assert dev.device_id == "iphone_03"
    assert dev.is_active is True
