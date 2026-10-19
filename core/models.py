"""Data models and Pydantic schema contracts for FleetStream."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class DistributionStatus(str, Enum):
    """Lifecycle status of video processing and distribution."""

    PENDING = "pending"
    PROCESSING = "processing"
    DISTRIBUTED = "distributed"
    CORRUPTED = "corrupted"
    FAILED = "failed"


class VideoMetadata(BaseModel):
    """Paired JSON schema contract generated for each video distributed to a device."""

    original_filename: str = Field(description="Original filename received in the inbox")
    distributed_filename: str = Field(description="Filename stored inside the target iPhone directory")
    target_device: str = Field(description="Identifier of target iPhone device (e.g., iphone_01)")
    suggested_caption: str = Field(
        default="New exclusive drop. Link in bio.",
        description="Suggested viral social media caption for publishing",
    )
    hashtags: list[str] = Field(
        default_factory=lambda: ["#viral", "#fyp", "#trending", "#reels", "#explore"],
        description="List of hashtags associated with the video",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the distribution event",
    )
    file_size_bytes: int = Field(ge=0, description="File size in bytes")
    checksum_sha256: str | None = Field(
        default=None,
        description="SHA-256 hash verifying data integrity from inbox to destination",
    )
    status: DistributionStatus = Field(
        default=DistributionStatus.DISTRIBUTED,
        description="Current operational status of the item",
    )
    extra_payload: dict[str, Any] = Field(
        default_factory=lambda: {"managed_by": "tame.so", "orchestrator": "fleetstream"},
        description="Additional contextual metadata for Tame.so automation",
    )


class Device(BaseModel):
    """Representation of an iPhone hardware/mount node within the fleet."""

    device_id: str = Field(description="Unique device identifier (e.g., iphone_01)")
    path: Path = Field(description="Filesystem path monitored by Tame.so for this device")
    is_active: bool = Field(default=True, description="Indicates whether the device is ready to receive videos")


class IngestJob(BaseModel):
    """Tracking record for an ingested file through the distribution pipeline."""

    source_path: Path
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_device: Device | None = None
    target_video_path: Path | None = None
    target_metadata_path: Path | None = None
    status: DistributionStatus = DistributionStatus.PENDING
    error_message: str | None = None


class DistributionSummary(BaseModel):
    """Summary metrics of an inbox distribution cycle execution."""

    processed: int = Field(default=0, description="Total files evaluated in inbox")
    distributed: int = Field(default=0, description="Total videos successfully distributed")
    skipped: int = Field(default=0, description="Total files skipped due to disallowed extensions")
    failed: int = Field(default=0, description="Total files that encountered processing errors")

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)
