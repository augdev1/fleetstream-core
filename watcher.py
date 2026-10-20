#!/usr/bin/env python3
"""FleetStream Watcher - Continuous Automated Ingestion and Distribution Daemon.

Monitors the inbox directory using the watchdog library, verifies file write stabilization
(preventing I/O permission locks during active file transfers), and invokes the
DistributionEngine to route files via balanced Round-Robin to iPhone target directories
with their paired .json metadata sidecars.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import threading
import time

from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Settings
from core.distributor import DistributionEngine

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fleetstream.watcher")

VALID_VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".mkv", ".m4v"}
TEMPORARY_EXTENSIONS: set[str] = {
    ".tmp",
    ".part",
    ".crdownload",
    ".swp",
    ".lock",
    ".download",
    ".partial",
    ".~tmp",
}


def log_event(message: str, style: str = "white", tag: str = "INFO") -> None:
    """Output formatted console log with timestamp and tag."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if RICH_AVAILABLE and console:
        console.print(f"[dim]{timestamp}[/dim] [{style}][{tag}] {message}[/{style}]")
    else:
        print(f"[{timestamp}] [{tag}] {message}")


def is_valid_target_file(file_path: Path) -> bool:
    """Verify whether a file is an eligible video and not temporary or hidden."""
    name = file_path.name
    if name.startswith("."):
        return False

    suffix = file_path.suffix.lower()
    if suffix in TEMPORARY_EXTENSIONS:
        return False

    return suffix in VALID_VIDEO_EXTENSIONS


def wait_for_file_to_finish_copying(
    file_path: Path,
    timeout: float = 60.0,
    check_interval: float = 0.5,
    stable_checks: int = 2,
) -> bool:
    """Wait for video file writes to stabilize before attempting to move it.

    Ensures the file is no longer being actively copied or pasted into the directory,
    preventing Windows PermissionError and OS write-lock collisions.

    Returns:
        True if the file size has stabilized with size > 0 and is readable.
        False if timeout was reached or the file was deleted.
    """
    last_size = -1
    consecutive_stable = 0
    start_time = time.monotonic()

    while (time.monotonic() - start_time) < timeout:
        if not file_path.exists():
            return False

        try:
            current_size = file_path.stat().st_size
        except (OSError, IOError):
            time.sleep(check_interval)
            continue

        can_open = False
        try:
            with open(file_path, "rb") as f:
                f.read(128)
            can_open = True
        except (OSError, IOError, PermissionError):
            can_open = False

        if current_size > 0 and current_size == last_size and can_open:
            consecutive_stable += 1
            if consecutive_stable >= stable_checks:
                return True
        else:
            consecutive_stable = 0
            last_size = current_size

        time.sleep(check_interval)

    logger.warning("Timeout (%ss) reached waiting for %s to stabilize", timeout, file_path.name)
    return False


class InboxWatcherHandler(FileSystemEventHandler):
    """Watchdog event handler with asynchronous worker pool and file debounce."""

    def __init__(
        self,
        engine: DistributionEngine,
        settle_timeout: float = 60.0,
        settle_interval: float = 0.5,
        max_workers: int = 4,
    ) -> None:
        super().__init__()
        self.engine = engine
        self.settle_timeout = settle_timeout
        self.settle_interval = settle_interval
        self._processing: set[str] = set()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="FleetWatcher")

    def _should_handle(self, path: Path) -> bool:
        """Determine if path represents a valid candidate video file."""
        if not path.is_file():
            return False
        return is_valid_target_file(path)

    def _enqueue_file(self, file_path: Path) -> None:
        """Schedule file for write verification and distribution."""
        normalized = str(file_path.resolve())
        with self._lock:
            if normalized in self._processing:
                return
            self._processing.add(normalized)

        # Log: Detection of file
        log_event(
            f"New file detected in inbox: [bold]{file_path.name}[/bold]",
            style="yellow",
            tag="DETECTED",
        )

        self._executor.submit(self._process_file_task, file_path, normalized)

    def _process_file_task(self, file_path: Path, normalized_key: str) -> None:
        """Worker task checking copy completion and executing distribution."""
        try:
            log_event(
                f"Awaiting file write completion for: [bold]{file_path.name}[/bold]...",
                style="dim cyan",
                tag="WAITING",
            )

            is_ready = wait_for_file_to_finish_copying(
                file_path=file_path,
                timeout=self.settle_timeout,
                check_interval=self.settle_interval,
            )

            if not is_ready:
                log_event(
                    f"File write failed to stabilize or file was removed: [bold]{file_path.name}[/bold]",
                    style="red",
                    tag="ABORTED",
                )
                return

            size_mb = file_path.stat().st_size / (1024 * 1024)
            # Log: Confirmation of write completed
            log_event(
                f"File write confirmed completed: [bold]{file_path.name}[/bold] ({size_mb:.2f} MB)",
                style="green",
                tag="STABILIZED",
            )

            job = self.engine.distribute_file(file_path)
            target_device = job.target_device.device_id if job.target_device else "unknown"
            meta_name = job.target_metadata_path.name if job.target_metadata_path else ".json"

            # Log: Device destination
            log_event(
                f"Routed successfully: [bold]{job.source_path.name}[/bold] -> "
                f"[bold cyan]{target_device}[/bold cyan] "
                f"[dim](Sidecar generated: {meta_name})[/dim]",
                style="bold magenta",
                tag="ROUTED",
            )

        except Exception as exc:
            logger.error("Error distributing file %s: %s", file_path.name, exc, exc_info=True)
            log_event(
                f"Error distributing [bold]{file_path.name}[/bold]: {exc}",
                style="bold red",
                tag="ERROR",
            )
        finally:
            with self._lock:
                self._processing.discard(normalized_key)

    def on_created(self, event: FileSystemEvent) -> None:
        """Triggered when a new filesystem entry is created."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_handle(path):
            self._enqueue_file(path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Triggered when a file is modified during write operations."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_handle(path):
            self._enqueue_file(path)

    def on_moved(self, event: FileMovedEvent) -> None:
        """Triggered when a file is moved or renamed into the inbox."""
        if event.is_directory:
            return
        dest_path = Path(event.dest_path)
        if self._should_handle(dest_path):
            self._enqueue_file(dest_path)

    def process_existing_files(self, inbox_dir: Path) -> None:
        """Scan and process files already present in the inbox at startup."""
        if not inbox_dir.exists():
            return
        for file_path in sorted(inbox_dir.iterdir()):
            if self._should_handle(file_path):
                self._enqueue_file(file_path)

    def shutdown(self) -> None:
        """Gracefully shutdown worker threads."""
        self._executor.shutdown(wait=False)


class FleetStreamWatcher:
    """Continuous inbox monitoring and distribution manager."""

    def __init__(
        self,
        inbox_dir: Path,
        devices_dir: Path,
        device_paths: list[Path] | None = None,
        settle_timeout: float = 60.0,
        settle_interval: float = 0.5,
    ) -> None:
        self.inbox_dir = Path(inbox_dir)
        self.devices_dir = Path(devices_dir)

        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.devices_dir.mkdir(parents=True, exist_ok=True)

        self.engine = DistributionEngine(
            inbox_dir=self.inbox_dir,
            devices_dir=self.devices_dir,
            device_paths=device_paths,
            allowed_extensions=VALID_VIDEO_EXTENSIONS,
        )

        self.handler = InboxWatcherHandler(
            engine=self.engine,
            settle_timeout=settle_timeout,
            settle_interval=settle_interval,
        )
        self.observer = Observer()

    def start(self, scan_existing: bool = True) -> None:
        """Start listening for filesystem events."""
        self.observer.schedule(self.handler, path=str(self.inbox_dir), recursive=False)
        self.observer.start()

        if scan_existing:
            self.handler.process_existing_files(self.inbox_dir)

    def stop(self) -> None:
        """Stop watcher and await thread termination."""
        self.observer.stop()
        self.observer.join()
        self.handler.shutdown()


def print_banner(inbox_dir: Path, devices_dir: Path) -> None:
    """Display startup information banner."""
    devices: list[str] = []
    if devices_dir.exists():
        devices = [d.name for d in sorted(devices_dir.iterdir()) if d.is_dir()]
    if not devices:
        devices = [
            "iphone_01",
            "iphone_02",
            "iphone_03",
            "iphone_04",
        ]

    if RICH_AVAILABLE and console:
        banner = (
            f"[bold cyan]FleetStream Continuous Watcher[/bold cyan]\n"
            f"[dim]Active Video Ingestion and Fleet Orchestrator[/dim]\n\n"
            f"[bold]Inbox Folder:[/bold] [yellow]{inbox_dir.resolve()}[/yellow]\n"
            f"[bold]Devices ({len(devices)}):[/bold] [green]{', '.join(devices)}[/green]\n"
            f"[bold]Accepted Extensions:[/bold] {', '.join(sorted(VALID_VIDEO_EXTENSIONS))}\n\n"
            f"[dim italic]Press Ctrl+C to terminate the service at any time.[/dim italic]"
        )
        console.print(Panel(banner, border_style="cyan", box=box.ROUNDED))
    else:
        print("=" * 60)
        print("FleetStream Continuous Watcher - Active Daemon")
        print(f"Inbox: {inbox_dir}")
        print(f"Devices: {', '.join(devices)}")
        print("=" * 60)


def main() -> None:
    """CLI entrypoint for the continuous watcher daemon."""
    parser = argparse.ArgumentParser(
        description="FleetStream Watcher - Continuous inbox monitoring and video orchestration.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to configuration JSON file (default: config.json)",
    )
    parser.add_argument(
        "--inbox",
        type=Path,
        default=None,
        help="Path to inbox directory",
    )
    parser.add_argument(
        "--devices",
        type=Path,
        default=None,
        help="Root path containing iPhone target directories",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Execute using the ./mock_rig test sandbox directory",
    )
    parser.add_argument(
        "--settle-timeout",
        type=float,
        default=None,
        help="Maximum timeout in seconds to wait for file stabilization",
    )
    parser.add_argument(
        "--settle-interval",
        type=float,
        default=None,
        help="Interval in seconds between file stabilization checks",
    )

    args = parser.parse_args()

    settings = Settings.load(args.config)

    if args.mock:
        inbox_dir = args.inbox or (PROJECT_ROOT / "mock_rig" / "inbox")
        devices_dir = args.devices or (PROJECT_ROOT / "mock_rig" / "devices")
    else:
        inbox_dir = args.inbox or settings.inbox_dir
        devices_dir = args.devices or settings.devices_dir

    if not inbox_dir.is_absolute():
        inbox_dir = (PROJECT_ROOT / inbox_dir).resolve()
    if not devices_dir.is_absolute():
        devices_dir = (PROJECT_ROOT / devices_dir).resolve()

    inbox_dir.mkdir(parents=True, exist_ok=True)
    devices_dir.mkdir(parents=True, exist_ok=True)

    device_ids = settings.device_ids or ["iphone_01", "iphone_02", "iphone_03", "iphone_04"]
    for dev_id in device_ids:
        (devices_dir / dev_id).mkdir(parents=True, exist_ok=True)

    settle_timeout = args.settle_timeout or settings.file_settle_timeout_seconds
    settle_interval = args.settle_interval or settings.poll_interval_seconds

    print_banner(inbox_dir, devices_dir)

    watcher_service = FleetStreamWatcher(
        inbox_dir=inbox_dir,
        devices_dir=devices_dir,
        settle_timeout=settle_timeout,
        settle_interval=settle_interval,
    )

    watcher_service.start(scan_existing=True)
    log_event("Monitoring active. Waiting for incoming videos...", style="bold green", tag="READY")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_event("Shutdown signal received. Stopping service...", style="yellow", tag="HALTING")
        watcher_service.stop()
        log_event("Watcher daemon cleanly terminated.", style="dim", tag="STOPPED")


if __name__ == "__main__":
    main()
