"""Hermetic Test Harness suite for macOS and Linux Cross-Platform Compatibility.

Validates that:
- macOS launcher scripts (.command, .sh) strictly use LF line endings (no CRLF).
- Shebang headers are valid POSIX bash headers.
- Executable permissions (0755) are preserved in git and inside fleetstream-core.zip.
- The zip package contains all essential runtime assets and preserves execution bits.
- Python codebase contains zero Windows-only runtime imports (e.g., msvcrt, windll).
"""

from pathlib import Path
import stat
import zipfile
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MACOS_SCRIPTS = [
    "INSTALL.command",
    "START_FLEETSTREAM.command",
    "install.sh",
    "start.sh",
]


@pytest.mark.harness
def test_macos_scripts_line_endings() -> None:
    """Ensure all macOS scripts have LF line endings (CRLF breaks bash on macOS)."""
    for script_name in MACOS_SCRIPTS:
        script_path = PROJECT_ROOT / script_name
        assert script_path.exists(), f"Expected script missing: {script_name}"
        raw_bytes = script_path.read_bytes()
        assert b"\r\n" not in raw_bytes, (
            f"Script {script_name} contains Windows CRLF line endings. "
            f"This causes '/bin/bash^M: bad interpreter' on macOS."
        )


@pytest.mark.harness
def test_macos_scripts_shebang() -> None:
    """Ensure all macOS scripts start with valid bash shebang."""
    for script_name in MACOS_SCRIPTS:
        script_path = PROJECT_ROOT / script_name
        first_line = script_path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line.startswith("#!/usr/bin/env bash") or first_line.startswith("#!/bin/bash"), (
            f"Script {script_name} has invalid shebang: {first_line}"
        )


@pytest.mark.harness
def test_zero_windows_only_imports() -> None:
    """Ensure the core codebase does not import Windows-exclusive modules."""
    disallowed = ["msvcrt", "winreg", "_winapi", "ctypes.windll"]
    python_files = list((PROJECT_ROOT / "core").glob("*.py")) + [PROJECT_ROOT / "watcher.py"]

    for py_file in python_files:
        content = py_file.read_text(encoding="utf-8")
        for bad_mod in disallowed:
            assert f"import {bad_mod}" not in content and f"from {bad_mod}" not in content, (
                f"File {py_file.name} contains disallowed Windows-only module import: {bad_mod}"
            )


@pytest.mark.harness
def test_distribution_zip_permissions_and_integrity() -> None:
    """Verify that fleetstream-core.zip preserves POSIX executable bits (0755) for Mac."""
    zip_path = PROJECT_ROOT / "fleetstream-core.zip"
    assert zip_path.exists(), "fleetstream-core.zip was not found. Run package_release.py first."

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        required_in_zip = [
            "fleetstream-core/INSTALL.command",
            "fleetstream-core/START_FLEETSTREAM.command",
            "fleetstream-core/install.sh",
            "fleetstream-core/start.sh",
            "fleetstream-core/INSTALL.bat",
            "fleetstream-core/START_FLEETSTREAM.bat",
            "fleetstream-core/config.json",
            "fleetstream-core/requirements.txt",
            "fleetstream-core/watcher.py",
            "fleetstream-core/core/__init__.py",
            "fleetstream-core/core/distributor.py",
            "fleetstream-core/core/metadata.py",
            "fleetstream-core/core/config.py",
        ]

        for req in required_in_zip:
            assert req in namelist, f"Essential file missing from distribution zip: {req}"

        for info in zf.filelist:
            mode = info.external_attr >> 16
            if any(info.filename.endswith(s) for s in [".command", ".sh", "uv.exe"]):
                is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
                assert is_executable, (
                    f"File {info.filename} inside zip is missing executable permission: {oct(mode)}"
                )
