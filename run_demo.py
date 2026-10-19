#!/usr/bin/env python3
"""FleetStream Operational Demonstration Script.

1. Initializes the ./mock_rig sandbox environment (inbox and 4 iPhone target folders).
2. Generates 8 simulated test videos if the inbox is empty.
3. Executes the Round-Robin distribution engine and emits paired .json sidecars.
4. Renders a formatted terminal report verifying device balances and metadata integrity.
"""

from datetime import datetime
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.distributor import DistributionEngine
from core.models import VideoMetadata
from harness.generators import DummyVideoGenerator

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_mock_rig(base_path: Path) -> tuple[Path, Path, list[Path]]:
    """Initialize mock rig directories for local simulation."""
    inbox_dir = base_path / "inbox"
    devices_dir = base_path / "devices"

    inbox_dir.mkdir(parents=True, exist_ok=True)
    devices_dir.mkdir(parents=True, exist_ok=True)

    device_names = ["iphone_01", "iphone_02", "iphone_03", "iphone_04"]
    device_paths: list[Path] = []
    for name in device_names:
        dev_dir = devices_dir / name
        dev_dir.mkdir(parents=True, exist_ok=True)
        device_paths.append(dev_dir)

    return inbox_dir, devices_dir, device_paths


def populate_inbox_if_empty(inbox_dir: Path, count: int = 8) -> list[Path]:
    """Generate synthetic .mp4 videos when inbox is empty."""
    existing_videos = [
        f for f in inbox_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv"}
    ]

    if existing_videos:
        return existing_videos

    print(f"[INFO] Empty inbox detected. Generating {count} simulated test videos...")
    return DummyVideoGenerator.create_batch(
        target_dir=inbox_dir,
        count=count,
        prefix="reel_tame",
        extension=".mp4",
    )


def print_report(
    summary,
    devices: list[Path],
    duration_ms: float,
) -> None:
    """Print clean formatted report verifying distribution results."""
    if not RICH_AVAILABLE:
        print("\n" + "=" * 60)
        print("FLEETSTREAM DISTRIBUTION REPORT")
        print("=" * 60)
        print(f"Total Evaluated: {summary.processed}")
        print(f"Distributed:     {summary.distributed}")
        print(f"Skipped:         {summary.skipped}")
        print(f"Failed:          {summary.failed}")
        print("-" * 60)
        for dev in devices:
            videos = list(dev.glob("*.mp4"))
            jsons = list(dev.glob("*.json"))
            print(f"Device {dev.name}: {len(videos)} videos | {len(jsons)} sidecars")
            for v in videos:
                status = "[OK]" if v.with_suffix(".json").exists() else "[MISSING SIDECAR]"
                print(f"   -> {v.name} -> {status}")
        print("=" * 60 + "\n")
        return

    console = Console()

    header_text = (
        f"[bold cyan]FleetStream[/bold cyan] - Local Video Orchestration Engine\n"
        f"[dim]Simulation Mode: 4 iPhones managed via Tame.so | Execution: {duration_ms:.1f}ms[/dim]"
    )
    console.print(Panel(header_text, border_style="cyan", box=box.ROUNDED))

    table = Table(
        title="Fleet Device Distribution",
        box=box.HEAVY_EDGE,
        header_style="bold magenta",
        title_style="bold green",
    )
    table.add_column("Device ID", style="bold yellow", width=14)
    table.add_column("Video Count", justify="center", width=14)
    table.add_column("Distributed Files", style="white")
    table.add_column(".JSON Integrity", justify="center", width=18)

    total_verified_jsons = 0

    for dev in devices:
        videos = sorted(list(dev.glob("*.mp4")))
        file_lines = []
        valid_jsons_for_device = 0

        for v in videos:
            json_file = v.with_suffix(".json")
            if json_file.exists():
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    VideoMetadata.model_validate(data)
                    valid_jsons_for_device += 1
                    total_verified_jsons += 1
                    file_lines.append(f"[green][OK][/green] {v.name}")
                except Exception:
                    file_lines.append(f"[red][INVALID][/red] {v.name}")
            else:
                file_lines.append(f"[red][NO JSON][/red] {v.name}")

        files_str = "\n".join(file_lines) if file_lines else "[dim]No files[/dim]"

        if len(videos) > 0 and valid_jsons_for_device == len(videos):
            json_status = f"[bold green]100% Valid ({valid_jsons_for_device})[/bold green]"
        elif len(videos) == 0:
            json_status = "[dim]0[/dim]"
        else:
            json_status = f"[bold red]Incomplete ({valid_jsons_for_device}/{len(videos)})[/bold red]"

        table.add_row(
            dev.name,
            str(len(videos)),
            files_str,
            json_status,
        )

    console.print(table)

    summary_panel = (
        f"[bold]Total Evaluated:[/bold] {summary.processed} | "
        f"[bold green]Successfully Distributed:[/bold green] {summary.distributed} | "
        f"[bold yellow]Skipped (invalid extension):[/bold yellow] {summary.skipped} | "
        f"[bold red]Failed:[/bold red] {summary.failed}\n"
        f"[bold cyan]Paired Sidecars Verified:[/bold cyan] {total_verified_jsons} valid .json files"
    )
    console.print(Panel(summary_panel, title="Operational Metrics", border_style="green", box=box.ROUNDED))


def main() -> None:
    """Demonstration CLI entrypoint."""
    mock_rig_path = PROJECT_ROOT / "mock_rig"
    inbox_dir, devices_dir, devices = setup_mock_rig(mock_rig_path)

    populate_inbox_if_empty(inbox_dir, count=8)

    engine = DistributionEngine(
        inbox_dir=inbox_dir,
        devices_dir=devices_dir,
    )

    start_time = datetime.now()
    summary = engine.process_inbox()
    duration_ms = (datetime.now() - start_time).total_seconds() * 1000

    print_report(summary, devices, duration_ms)


if __name__ == "__main__":
    main()
