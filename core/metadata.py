"""Module for generating and serializing paired metadata sidecars (.json)."""

from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
from typing import Protocol
from core.exceptions import MetadataGenerationError
from core.models import Device, DistributionStatus, VideoMetadata

logger = logging.getLogger(__name__)

DEFAULT_VIRAL_CAPTIONS: list[str] = [
    "New exclusive drop. Link in bio.",
    "Wait until the end. You will not believe this.",
    "Daily viral clip. Follow for more.",
    "Trending now. Check out the latest release.",
    "Behind the scenes footage. Link in bio.",
]

DEFAULT_HASHTAGS: list[str] = ["#viral", "#fyp", "#trending", "#reels", "#explore"]


def calculate_sha256(file_path: Path) -> str | None:
    """Calculate the SHA-256 hash of a file using memory-safe buffered chunks."""
    try:
        if not file_path.exists() or not file_path.is_file():
            return None
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError) as exc:
        logger.warning("Failed to compute SHA-256 hash for %s: %s", file_path, exc)
        return None


class MetadataGeneratorProtocol(Protocol):
    """Protocol contract for video metadata generators."""

    def generate(
        self,
        video_path: Path,
        target_device: Device | str,
        original_filename: str | None = None,
        suggested_caption: str | None = None,
        hashtags: list[str] | None = None,
    ) -> VideoMetadata:
        """Create a validated metadata object for a specific video and device."""
        ...

    def write_sidecar(self, metadata: VideoMetadata, destination_path: Path) -> Path:
        """Serialize metadata in JSON format paired with the video destination."""
        ...


class MetadataGenerator:
    """Standard generator for paired .json sidecars containing captions, tags, and status."""

    def __init__(
        self,
        default_hashtags: list[str] | None = None,
        default_captions: list[str] | None = None,
    ) -> None:
        self.default_hashtags: list[str] = (
            list(default_hashtags) if default_hashtags is not None else list(DEFAULT_HASHTAGS)
        )
        self.default_captions: list[str] = (
            list(default_captions) if default_captions is not None else list(DEFAULT_VIRAL_CAPTIONS)
        )
        self._caption_index: int = 0

    def get_suggested_caption(self, video_stem: str) -> str:
        """Return a viral English caption."""
        if not self.default_captions:
            return "Trending video. Link in bio."
        caption = self.default_captions[self._caption_index % len(self.default_captions)]
        self._caption_index += 1
        return caption

    def generate(
        self,
        video_path: Path,
        target_device: Device | str,
        original_filename: str | None = None,
        suggested_caption: str | None = None,
        hashtags: list[str] | None = None,
    ) -> VideoMetadata:
        """Generate a validated VideoMetadata instance via Pydantic."""
        try:
            device_id = (
                target_device.device_id
                if isinstance(target_device, Device)
                else str(target_device)
            )
            file_size = video_path.stat().st_size if video_path.exists() else 0
            checksum = calculate_sha256(video_path)

            caption = (
                suggested_caption
                if suggested_caption is not None
                else self.get_suggested_caption(video_path.stem)
            )
            tags = list(hashtags) if hashtags is not None else list(self.default_hashtags)

            return VideoMetadata(
                original_filename=original_filename or video_path.name,
                distributed_filename=video_path.name,
                target_device=device_id,
                suggested_caption=caption,
                hashtags=tags,
                timestamp=datetime.now(timezone.utc),
                file_size_bytes=file_size,
                checksum_sha256=checksum,
                status=DistributionStatus.DISTRIBUTED,
                extra_payload={"managed_by": "tame.so", "orchestrator": "fleetstream"},
            )
        except Exception as exc:
            logger.error("Failed to construct VideoMetadata for %s: %s", video_path, exc)
            raise MetadataGenerationError(f"Error generating metadata for {video_path}: {exc}") from exc

    def write_sidecar(self, metadata: VideoMetadata, destination_path: Path) -> Path:
        """Atomically write the paired .json sidecar next to the video.

        Writes to a temporary hidden file first before atomic replacement to guarantee
        that downstream automation (e.g. Tame.so) never reads partially written JSON files.
        """
        target_json = (
            destination_path
            if destination_path.suffix.lower() == ".json"
            else destination_path.with_suffix(".json")
        )

        try:
            target_json.parent.mkdir(parents=True, exist_ok=True)
            temp_json = target_json.with_name(f".tmp_{target_json.name}")

            with open(temp_json, "w", encoding="utf-8") as f:
                f.write(metadata.model_dump_json(indent=2))

            temp_json.replace(target_json)
            return target_json
        except (OSError, IOError) as exc:
            logger.error("Disk I/O error writing sidecar %s: %s", target_json, exc)
            raise MetadataGenerationError(f"Disk write failure for {target_json}: {exc}") from exc
