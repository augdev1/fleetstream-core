"""Package FleetStream Core into a cross-platform release archive (.zip).

Preserves POSIX executable permissions (0755) for macOS/Linux scripts
and Windows batch files, ensuring 2-click operation on both macOS and Windows.
"""

from pathlib import Path
import stat
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIST_FILES = [
    "INSTALL.bat",
    "START_FLEETSTREAM.bat",
    "INSTALL.command",
    "START_FLEETSTREAM.command",
    "install.sh",
    "start.sh",
    "config.json",
    "README.txt",
    "requirements.txt",
    "watcher.py",
    "tools/uv.exe",
    "core/__init__.py",
    "core/config.py",
    "core/distributor.py",
    "core/exceptions.py",
    "core/metadata.py",
    "core/models.py",
    "core/watcher.py",
]

EXECUTABLES = {
    "INSTALL.command",
    "START_FLEETSTREAM.command",
    "install.sh",
    "start.sh",
    "tools/uv.exe",
}


def build_zip(output_path: Path) -> Path:
    """Construct deterministic zip archive with explicit Unix permissions."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_str in sorted(DIST_FILES):
            source_file = PROJECT_ROOT / rel_str
            if not source_file.exists():
                raise FileNotFoundError(f"Required release file missing: {source_file}")

            archive_name = f"fleetstream-core/{rel_str.replace('\\', '/')}"
            data = source_file.read_bytes()

            zinfo = zipfile.ZipInfo(archive_name)
            zinfo.create_system = 3  # 3 = Unix (allows macOS Archive Utility to set permissions)

            if rel_str in EXECUTABLES or rel_str.endswith(".command") or rel_str.endswith(".sh"):
                # rwxr-xr-x (0755)
                zinfo.external_attr = (stat.S_IFREG | 0o755) << 16
            else:
                # rw-r--r-- (0644)
                zinfo.external_attr = (stat.S_IFREG | 0o644) << 16

            zf.writestr(zinfo, data)

    print(f"[SUCCESS] Packaged {len(DIST_FILES)} files into {output_path} ({output_path.stat().st_size / (1024*1024):.2f} MB)")
    return output_path


if __name__ == "__main__":
    out = PROJECT_ROOT / "fleetstream-core.zip"
    build_zip(out)
