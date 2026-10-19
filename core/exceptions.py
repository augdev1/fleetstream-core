"""Domain exception hierarchy for FleetStream."""


class FleetStreamError(Exception):
    """Base exception for all FleetStream errors."""


class CorruptMediaError(FleetStreamError):
    """Raised when a video file is corrupted, zero bytes, or unreadable."""


class IngestLockedError(FleetStreamError):
    """Raised when an inbox file is still being written to or locked by another process."""


class DeviceTargetUnavailableError(FleetStreamError):
    """Raised when a target device directory is missing or non-writable."""


class MetadataGenerationError(FleetStreamError):
    """Raised when synthesizing or serializing paired metadata fails."""


class DistributionError(FleetStreamError):
    """Raised when a failure occurs during the Round-Robin distribution cycle."""
