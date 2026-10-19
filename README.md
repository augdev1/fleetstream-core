# FleetStream Core

Local video file distribution and orchestration engine designed for mobile device fleets (4 iPhones managed via Tame.so).

---

## Overview

FleetStream eliminates local media management bottlenecks in automated multi-phone operations. It continuously monitors an incoming inbox folder, distributes video files across physical device targets (`iphone_01` through `iphone_04`) using a deterministic Round-Robin strategy, and automatically generates paired `.json` metadata sidecars containing viral captions, hashtags, timestamps, and SHA-256 integrity verification.

Built under strict Test Harness Engineering principles, the repository includes a complete test bench simulating filesystem concurrency, file write stabilization, and fault injection without requiring physical hardware.

---

## Quick Start (3 Steps for Windows)

### Step 1: Unpack
Extract the repository folder to your local drive (for example, `D:\fleetstream-core` or `C:\fleetstream-core`).

### Step 2: Install Dependencies
Double-click `INSTALL.bat` in the root folder.
This script checks your Python installation (Python 3.11+ required) and installs the required runtime dependencies:
```cmd
INSTALL.bat
```

### Step 3: Start the Orchestrator
Double-click `START_FLEETSTREAM.bat`.
This launches the continuous watcher daemon:
```cmd
START_FLEETSTREAM.bat
```
Any video dropped into the `inbox` directory will be automatically stabilized, distributed across your iPhones, and paired with a `.json` metadata sidecar.

---

## Architecture and Directory Structure

```text
fleetstream-core/
|-- INSTALL.bat                 # Windows dependency installation script
|-- START_FLEETSTREAM.bat       # Windows one-click watcher launcher
|-- config.json                 # Path and device configuration file
|-- requirements.txt            # Minimal runtime and testing dependencies
|-- pyproject.toml              # Build metadata and tool configuration
|-- run_demo.py                 # Self-contained operational demo script
|-- watcher.py                  # Continuous background file watcher daemon
|
|-- core/                       # Core orchestration logic and schemas
|   |-- __init__.py
|   |-- config.py               # Pydantic configuration loader
|   |-- distributor.py          # Round-Robin distribution engine
|   |-- exceptions.py           # Domain exception classes
|   |-- metadata.py             # Atomic sidecar JSON generator
|   |-- models.py               # Pydantic data schemas
|   |-- watcher.py              # Ingest orchestrator interface
|
|-- harness/                    # Test Harness Engineering toolkit
|   |-- __init__.py
|   |-- assertions.py           # Domain validation rules
|   |-- env.py                  # Isolated sandbox environment manager
|   |-- generators.py           # Synthetic video and corrupt file generator
|   |-- test_distributor.py     # Hermetic test bench suite
|
`-- tests/                      # Unit and integration test suite
    |-- __init__.py
    |-- conftest.py             # Global pytest fixtures
    |-- unit/                   # Model and unit tests
    `-- integration/            # Pipeline and fault tolerance tests
```

---

## Configuration (`config.json`)

To map FleetStream to your local Tame.so mount directories, modify `config.json` in the root folder:

```json
{
  "inbox_dir": "./inbox",
  "devices_dir": "./devices",
  "device_ids": [
    "iphone_01",
    "iphone_02",
    "iphone_03",
    "iphone_04"
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
  "timestamp": "2026-10-19T22:48:08.362158Z",
  "file_size_bytes": 10485760,
  "checksum_sha256": "7957dac3839bef272e314fcd59b3abf5bd0a36403432803126aa2bdc9ae4cac6",
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

## Running the Automated Test Suite

To run all 22 tests across unit, integration, and harness suites:

```bash
pytest -v
```

To run only the isolated test harness:

```bash
pytest -v harness/
```

To run the interactive CLI demonstration with visual terminal output:

```bash
python run_demo.py
```

---

## License

MIT License. Developed for automated iPhone fleet orchestration.
