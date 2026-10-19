"""Integration tests for the continuous FleetStreamWatcher daemon."""

from pathlib import Path
import time
import pytest
from watcher import FleetStreamWatcher


@pytest.mark.integration
def test_watcher_detects_and_distributes_video(tmp_path: Path) -> None:
    """Verify that the watcher monitors inbox and distributes a newly arriving video."""
    inbox_dir = tmp_path / "inbox"
    devices_dir = tmp_path / "devices"

    watcher = FleetStreamWatcher(
        inbox_dir=inbox_dir,
        devices_dir=devices_dir,
        settle_timeout=2.0,
        settle_interval=0.05,
    )

    try:
        watcher.start(scan_existing=False)

        video_path = inbox_dir / "live_clip.mp4"
        video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024)

        max_wait = 3.0
        start = time.monotonic()
        distributed = False

        while (time.monotonic() - start) < max_wait:
            found_videos = list(devices_dir.glob("*/live_clip.mp4"))
            if len(found_videos) == 1:
                distributed = True
                dest_video = found_videos[0]
                assert dest_video.with_suffix(".json").exists()
                break
            time.sleep(0.1)

        assert distributed is True, "The video was not distributed to devices by watcher."
        assert not video_path.exists(), "Original file should have been moved from inbox."

    finally:
        watcher.stop()
