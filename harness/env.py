"""Sandbox simulation environment for FleetStream orchestration tests."""

from dataclasses import dataclass
from pathlib import Path
from core.models import Device


@dataclass
class SandboxEnvironment:
    """Isolated filesystem sandbox mirroring production device mounts."""

    root_path: Path
    inbox_dir: Path
    devices_dir: Path
    dead_letter_dir: Path
    devices: list[Device]

    @classmethod
    def create(
        cls,
        base_dir: Path,
        device_names: list[str] | None = None,
    ) -> "SandboxEnvironment":
        """Instantiate and create all physical directories in the sandbox root."""
        if device_names is None:
            device_names = ["iphone_01", "iphone_02", "iphone_03", "iphone_04"]

        inbox_dir = base_dir / "inbox"
        devices_dir = base_dir / "devices"
        dead_letter_dir = base_dir / "dead_letter"

        inbox_dir.mkdir(parents=True, exist_ok=True)
        devices_dir.mkdir(parents=True, exist_ok=True)
        dead_letter_dir.mkdir(parents=True, exist_ok=True)

        devices: list[Device] = []
        for name in device_names:
            dev_path = devices_dir / name
            dev_path.mkdir(parents=True, exist_ok=True)
            devices.append(Device(device_id=name, path=dev_path, is_active=True))

        return cls(
            root_path=base_dir,
            inbox_dir=inbox_dir,
            devices_dir=devices_dir,
            dead_letter_dir=dead_letter_dir,
            devices=devices,
        )

    def get_device(self, device_id: str) -> Device:
        """Find a device node by ID."""
        for dev in self.devices:
            if dev.device_id == device_id:
                return dev
        raise KeyError(f"Device {device_id} not found in sandbox.")

    def list_device_videos(self, device_id: str) -> list[Path]:
        """List all video files inside a specific iPhone directory."""
        dev = self.get_device(device_id)
        return sorted([
            f for f in dev.path.iterdir()
            if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv"}
        ])

    def list_device_metadata(self, device_id: str) -> list[Path]:
        """List all .json metadata files inside a specific iPhone directory."""
        dev = self.get_device(device_id)
        return sorted([f for f in dev.path.iterdir() if f.is_file() and f.suffix.lower() == ".json"])

    def count_total_distributed_videos(self) -> int:
        """Count total videos across all device target directories."""
        total = 0
        for dev in self.devices:
            total += len(self.list_device_videos(dev.device_id))
        return total
