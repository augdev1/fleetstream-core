"""File distribution module using balanced Round-Robin scheduling."""

from collections.abc import Sequence
import logging
from pathlib import Path
import shutil
from typing import Protocol
from core.exceptions import DeviceTargetUnavailableError, DistributionError
from core.metadata import MetadataGenerator
from core.models import Device, DistributionStatus, DistributionSummary, IngestJob

logger = logging.getLogger(__name__)


class DistributorProtocol(Protocol):
    """Protocol contract for fleet distribution algorithms."""

    def select_next_device(self) -> Device:
        """Return the next eligible device according to configured policy."""
        ...

    def dispatch(self, video_path: Path) -> IngestJob:
        """Orchestrate atomic file transfer to the selected device."""
        ...


class RoundRobinDistributor:
    """Deterministic circular (Round-Robin) distributor across iPhone fleet nodes.

    Guarantees balanced load distribution across all active devices.
    """

    def __init__(self, devices: Sequence[Device]) -> None:
        self.devices: list[Device] = list(devices)
        self._current_index: int = 0
        self.metadata_generator: MetadataGenerator = MetadataGenerator()

    @property
    def active_devices(self) -> list[Device]:
        """Devices that are operational and ready to accept media."""
        return [d for d in self.devices if d.is_active]

    def select_next_device(self) -> Device:
        """Select the next active device in the circular queue."""
        active = self.active_devices
        if not active:
            raise DeviceTargetUnavailableError("No active devices available for distribution.")

        device = active[self._current_index % len(active)]
        self._current_index = (self._current_index + 1) % len(active)
        return device

    def dispatch(self, video_path: Path) -> IngestJob:
        """Atomically dispatch a video file to the next device in queue."""
        if not video_path.exists():
            raise FileNotFoundError(f"Source file not found: {video_path}")

        device = self.select_next_device()
        device.path.mkdir(parents=True, exist_ok=True)
        target_video_path = device.path / video_path.name

        try:
            shutil.move(str(video_path), str(target_video_path))
            meta = self.metadata_generator.generate(
                video_path=target_video_path,
                target_device=device,
                original_filename=video_path.name,
            )
            meta_path = self.metadata_generator.write_sidecar(meta, target_video_path)

            return IngestJob(
                source_path=video_path,
                target_device=device,
                target_video_path=target_video_path,
                target_metadata_path=meta_path,
                status=DistributionStatus.DISTRIBUTED,
            )
        except (OSError, IOError, shutil.Error) as exc:
            logger.error("Failed to dispatch video %s to %s: %s", video_path, device.device_id, exc)
            raise DistributionError(f"I/O error moving {video_path} to {device.device_id}: {exc}") from exc


class DistributionEngine:
    """Core distribution and orchestration engine for iPhone fleets."""

    def __init__(
        self,
        inbox_dir: Path,
        devices_dir: Path | None = None,
        device_paths: list[Path] | None = None,
        allowed_extensions: set[str] | None = None,
    ) -> None:
        """Initialize engine with inbox folder, target device roots, and allowed formats."""
        self.inbox_dir: Path = Path(inbox_dir)
        self.allowed_extensions: set[str] = {
            ext.lower()
            for ext in (
                allowed_extensions
                if allowed_extensions is not None
                else {".mp4", ".mov", ".m4v", ".mkv"}
            )
        }

        # Resolve device target directories
        if device_paths is not None:
            self.device_paths: list[Path] = [Path(p) for p in device_paths]
        elif devices_dir is not None:
            dev_root = Path(devices_dir)
            dev_root.mkdir(parents=True, exist_ok=True)
            # Detect existing subdirectories alphabetically
            subdirs = sorted([d for d in dev_root.iterdir() if d.is_dir()])
            if subdirs:
                self.device_paths = subdirs
            else:
                # Initialize standard 4 iPhones
                self.device_paths = [
                    dev_root / f"iphone_{i:02d}" for i in range(1, 5)
                ]
                for p in self.device_paths:
                    p.mkdir(parents=True, exist_ok=True)
        else:
            self.device_paths = []

        self._current_index: int = 0
        self.metadata_generator: MetadataGenerator = MetadataGenerator()

    def get_devices(self) -> list[Path]:
        """Return list of managed device directory paths."""
        return list(self.device_paths)

    def get_next_device(self) -> Path:
        """Return the next target device path in Round-Robin order."""
        if not self.device_paths:
            raise DeviceTargetUnavailableError("No devices available in distribution engine.")

        device = self.device_paths[self._current_index % len(self.device_paths)]
        self._current_index = (self._current_index + 1) % len(self.device_paths)
        return device

    def distribute_file(self, file_path: Path) -> IngestJob:
        """Atomically distribute a single file to the next iPhone in rotation."""
        if not file_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {file_path}")

        target_dev = self.get_next_device()
        target_dev.mkdir(parents=True, exist_ok=True)
        dest_video = target_dev / file_path.name

        # Physical file transfer via shutil.move
        shutil.move(str(file_path), str(dest_video))

        # Generate and persist paired JSON sidecar
        metadata = self.metadata_generator.generate(
            video_path=dest_video,
            target_device=target_dev.name,
            original_filename=file_path.name,
        )
        meta_path = self.metadata_generator.write_sidecar(
            metadata=metadata,
            destination_path=dest_video.with_suffix(".json"),
        )

        return IngestJob(
            source_path=file_path,
            target_device=Device(device_id=target_dev.name, path=target_dev),
            target_video_path=dest_video,
            target_metadata_path=meta_path,
            status=DistributionStatus.DISTRIBUTED,
        )

    def process_inbox(self) -> DistributionSummary:
        """Execute complete cycle: scan, validate, distribute, and emit metadata."""
        summary = DistributionSummary(processed=0, distributed=0, skipped=0, failed=0)

        if not self.inbox_dir.exists():
            return summary

        try:
            entries = sorted([f for f in self.inbox_dir.iterdir() if f.is_file()])
        except (OSError, IOError) as exc:
            logger.error("I/O error listing inbox %s: %s", self.inbox_dir, exc)
            return summary

        if not entries:
            return summary

        for file_path in entries:
            if not file_path.exists():
                continue

            summary.processed += 1

            # Skip disallowed extensions
            if file_path.suffix.lower() not in self.allowed_extensions:
                summary.skipped += 1
                logger.info("File skipped due to non-video extension: %s", file_path.name)
                continue

            try:
                job = self.distribute_file(file_path)
                summary.distributed += 1
                target_name = job.target_device.device_id if job.target_device else "device"
                logger.info("Video distributed successfully: %s -> %s", file_path.name, target_name)

            except (OSError, IOError, shutil.Error) as exc:
                logger.error("Disk I/O failure processing %s: %s", file_path.name, exc)
                summary.failed += 1
            except Exception as exc:
                logger.error("Unexpected error in pipeline for %s: %s", file_path.name, exc)
                summary.failed += 1

        return summary

    def run(self) -> DistributionSummary:
        """Execute distribution pipeline (alias for process_inbox)."""
        return self.process_inbox()
