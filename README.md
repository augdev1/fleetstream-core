# FleetStream Core

Local video file distribution and orchestration engine designed for mobile device fleets (4 iPhones managed via Tame.so).

---

## Direct Download

- **Ready-to-use Package (.ZIP):** [Download fleetstream-core.zip](https://github.com/augdev1/fleetstream-core/raw/main/fleetstream-core.zip)
- **Source Code (.ZIP):** [Download GitHub Repository ZIP](https://github.com/augdev1/fleetstream-core/archive/refs/heads/main.zip)

---

## Overview

FleetStream eliminates media orchestration bottlenecks in automated multi-phone social media operations. It continuously monitors an incoming inbox folder, safely waits for file copies to stabilize, distributes or mirrors videos to your iPhone directories (`iphone_01` through `iphone_04`), and automatically generates paired `.json` metadata sidecars containing viral captions, hashtags, timestamps, and SHA-256 integrity verification for Tame.so.

---

## Complete Step-by-Step Tutorial (Windows)

No programming knowledge or command-line typing is required. The entire workflow operates through Windows Explorer and one-click batch scripts.

### Step 1: Unpack
1. Download **`fleetstream-core.zip`** using the download link above.
2. Extract the folder anywhere on your computer (for example, `C:\FleetStream` or `D:\FleetStream`).

### Step 2: Run Installer (`INSTALL.bat`)
1. Open the extracted folder and double-click **`INSTALL.bat`**.
2. **Automatic Python Setup:** You do not need to install Python manually. If Python is missing from your PC, `INSTALL.bat` will automatically download and configure standalone Python 3.12 and all required dependencies in an isolated `.venv` environment.
3. Once finished, the terminal will display `[SUCCESS] FleetStream environment ready!`. Press any key to close the window.

### Step 3: Test Installation (Optional)
Double-click **`RUN_DEMO.bat`** to run a self-contained simulation. The script generates 8 test reels, processes them, and outputs a formatted terminal report confirming that video routing and `.json` sidecar generation are functional.

### Step 4: Configure Settings (`config.json`)
Open **`config.json`** using Notepad to customize your setup:

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

#### Configuration Options:
- **`mode`**:
  - `"broadcast"` (Default): Copies every incoming video to **all 4 iPhones** with individual `.json` sidecars in each phone folder.
  - `"round_robin"`: Divides videos evenly among the 4 iPhones (e.g., 4 videos = 1 per phone).
- **`default_hashtags`**: Array of hashtags attached to the `.json` sidecars for your niche.
- **`default_captions`**: Pool of viral captions rotated across distributed videos.
- **`inbox_dir`**: Folder where you drop new videos.
- **`devices_dir`**: Folder containing your iPhone subdirectories (`iphone_01` to `iphone_04`). If you use custom Tame.so sync paths, set them here.

### Step 5: Start the Service (`START_FLEETSTREAM.bat`)
1. Double-click **`START_FLEETSTREAM.bat`**.
2. Keep the black terminal window open (or minimized) in the background. It will show:
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

## Key Engineering Features

### 1. Write Stabilization and Lock Prevention
When large video files are pasted or downloaded into the inbox, premature file operations cause `PermissionError` and corrupted transfers. FleetStream implements `wait_for_file_to_finish_copying`, continuously monitoring file size stability across consecutive intervals and verifying read accessibility before moving.

### 2. Atomic Sidecar Serialization
Metadata JSON files are serialized to temporary files (`.tmp_*.json`) before atomic renaming. This guarantees that Tame.so watchers on the iPhones never read half-written JSON files.

### 3. Fault Tolerance
Non-video extensions (such as `.txt`, `.pdf`, `.sh`) and temporary download files (`.part`, `.crdownload`, `.tmp`) are safely ignored, tracked as skipped items, and left in the inbox without interrupting the queue.

---

## Automated Test Suite

To run all 23 tests across unit, integration, and harness suites:

```bash
pytest -v
```

---

## License

MIT License. Developed for automated iPhone fleet orchestration.
