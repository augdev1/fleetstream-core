# FleetStream Core

Local video file distribution and orchestration engine designed for mobile device fleets (4 iPhones managed via Tame.so).

---

## Download

- **FleetStream Client Package (.ZIP):** [Download fleetstream-core.zip](https://github.com/augdev1/fleetstream-core/raw/main/fleetstream-core.zip)

---

## Overview

FleetStream eliminates media orchestration bottlenecks in automated multi-phone social media operations. It continuously monitors an incoming inbox folder, safely waits for file copies to stabilize, mirrors videos to all your iPhone directories (`iphone_01` through `iphone_04`), and automatically generates paired `.json` metadata sidecars containing viral captions, hashtags, timestamps, and SHA-256 integrity verification for Tame.so.

---

## Quick Setup Guide (Windows & macOS)

No programming knowledge or command-line typing is required.

### Step 1: Unpack
1. Download **`fleetstream-core.zip`** using the download link above.
2. Extract the folder anywhere on your computer (for example, `~/FleetStream` or `C:\FleetStream`).

### Step 2: Run Installer
- **Windows:** Double-click **`INSTALL.bat`**.
- **macOS:** Double-click **`INSTALL.command`**.
- **Automatic Python Setup:** Python and dependencies are configured automatically. You do not need to install Python manually.
- Once finished, the terminal displays `[SUCCESS] FleetStream environment ready!`. Press any key to close the window.

### Step 3: Configure Settings (`config.json`)
Open **`config.json`** using Notepad to customize your setup if needed:

```json
{
  "mode": "broadcast",
  "inbox_dir": "./inbox",
  "devices_dir": "./devices",
  "device_ids": [
    "iphone_01",
    "iphone_02",
    "iphone_03",
    "iphone_04"
  ],
  "default_hashtags": [
    "#viral",
    "#fyp",
    "#trending",
    "#reels",
    "#explore"
  ],
  "default_captions": [
    "New exclusive drop. Link in bio.",
    "Wait until the end. You will not believe this.",
    "Daily viral clip. Follow for more.",
    "Trending now. Check out the latest release.",
    "Behind the scenes footage. Link in bio."
  ],
  "supported_extensions": [
    ".mp4",
    ".mov",
    ".mkv",
    ".m4v"
  ],
  "file_settle_timeout_seconds": 60.0,
  "poll_interval_seconds": 0.5
}
```

#### Settings Summary:
- **`mode`**: `"broadcast"` (mirrors every video to all 4 iPhones) or `"round_robin"` (divides videos evenly).
- **`default_hashtags`**: Custom hashtags attached to the `.json` sidecars.
- **`default_captions`**: Pool of viral captions rotated across videos.
- **`inbox_dir`**: Folder where you drop incoming videos.
- **`devices_dir`**: Folder containing your iPhone subdirectories (`iphone_01` to `iphone_04`).

### Step 4: Start the Service (`START_FLEETSTREAM.bat`)
1. Double-click **`START_FLEETSTREAM.bat`**.
2. Keep the window open (or minimized) in the background. It will show:
   ```text
   [READY] Monitoring active. Waiting for incoming videos...
   ```
3. Whenever you have videos to post, simply **drag and drop them into the `inbox` folder**.
4. FleetStream will automatically:
   - Detect each video and await copy stabilization.
   - Deliver the files to your iPhone device folders (`devices/iphone_01/` through `iphone_04/`).
   - Write paired `.json` sidecars with captions, hashtags, and SHA-256 checksums alongside each video.
   - Clean the `inbox` folder so it remains ready for the next batch.
5. Tame.so detects the files on each iPhone and handles the scheduled posting.

---

## Paired Metadata Sidecar Specification

Each distributed video file (e.g., `clip_001.mp4`) generates an exact paired sidecar (`clip_001.json`) validated by Pydantic:

```json
{
  "original_filename": "clip_001.mp4",
  "distributed_filename": "clip_001.mp4",
  "target_device": "iphone_01",
  "suggested_caption": "Wait until the end. You will not believe this.",
  "hashtags": [
    "#viral",
    "#fyp",
    "#trending",
    "#reels",
    "#explore"
  ],
  "timestamp": "2026-10-20T07:52:56.681939Z",
  "file_size_bytes": 30087752,
  "checksum_sha256": "54ae8b54b78c33fb8a8ccef927041c58cb97422e26d7151132ee396f255c1585",
  "status": "distributed",
  "extra_payload": {
    "managed_by": "tame.so",
    "orchestrator": "fleetstream"
  }
}
```

---

## License

MIT License. Developed for automated iPhone fleet orchestration.
