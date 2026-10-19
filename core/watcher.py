"""Inbox watcher and lifecycle orchestrator."""

from pathlib import Path
from typing import Protocol
from core.config import Settings
from core.distributor import DistributorProtocol
from core.metadata import MetadataGeneratorProtocol
from core.models import IngestJob


class IngestWatcherProtocol(Protocol):
    """Protocol interface for the inbox watcher and orchestrator."""

    def scan_inbox(self) -> list[Path]:
        """Scan inbox identifying ready incoming videos for processing."""
        ...

    def process_file(self, file_path: Path) -> IngestJob:
        """Execute validation, distribution, and metadata sidecar emission for a file."""
        ...


class InboxWatcher:
    """Local orchestrator monitoring the /inbox directory."""

    def __init__(
        self,
        settings: Settings,
        distributor: DistributorProtocol,
        metadata_generator: MetadataGeneratorProtocol,
    ) -> None:
        self.settings = settings
        self.distributor = distributor
        self.metadata_generator = metadata_generator

    def scan_inbox(self) -> list[Path]:
        """Scan inbox folder for valid video files."""
        if not self.settings.inbox_dir.exists():
            return []
        valid_exts = {ext.lower() for ext in self.settings.supported_extensions}
        return sorted([
            f for f in self.settings.inbox_dir.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in valid_exts
        ])

    def process_file(self, file_path: Path) -> IngestJob:
        """Move the video and generate the paired .json sidecar."""
        return self.distributor.dispatch(file_path)
