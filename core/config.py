"""Core configuration settings for FleetStream."""

import json
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Operational parameters for the ingestion and distribution engine."""

    model_config = SettingsConfigDict(
        env_prefix="FLEETSTREAM_",
        env_file=".env",
        extra="ignore",
    )

    # Core Directories
    base_dir: Path = Field(default=Path("./"), description="Base working directory")
    inbox_dir: Path = Field(default=Path("./inbox"), description="Inbox directory for raw incoming videos")
    devices_dir: Path = Field(default=Path("./devices"), description="Root directory containing iPhone targets")
    dead_letter_dir: Path = Field(
        default=Path("./dead_letter"),
        description="Directory where corrupt or unprocessable files are isolated",
    )

    # Device identifiers for the iPhone fleet (managed via Tame.so)
    device_ids: list[str] = Field(
        default=["iphone_01", "iphone_02", "iphone_03", "iphone_04"],
        description="Ordered list of device identifiers for Round-Robin rotation",
    )

    # Supported video formats
    supported_extensions: set[str] = Field(
        default={".mp4", ".mov", ".m4v", ".mkv"},
        description="Accepted video file extensions",
    )

    # File stability and debounce policies
    file_settle_timeout_seconds: float = Field(
        default=60.0,
        description="Maximum seconds to wait for in-progress file copying/writing to finish",
    )
    poll_interval_seconds: float = Field(
        default=0.5,
        description="Interval in seconds between file stability checks",
    )

    # Metadata defaults
    default_hashtags: list[str] = Field(
        default=["#viral", "#fyp", "#trending", "#reels", "#explore"],
        description="Default hashtags attached to generated metadata sidecars",
    )
    default_captions: list[str] = Field(
        default=[
            "New exclusive drop. Link in bio.",
            "Wait until the end. You will not believe this.",
            "Daily viral clip. Follow for more.",
            "Trending now. Check out the latest release.",
            "Behind the scenes footage. Link in bio.",
        ],
        description="Rotating pool of viral captions",
    )

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        """Load configuration from config.json if present, falling back to defaults/env."""
        target_path = config_path or Path("config.json")
        if target_path.exists() and target_path.is_file():
            try:
                with open(target_path, encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                pass
        return cls()
