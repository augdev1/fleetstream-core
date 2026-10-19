"""Global pytest fixtures integrating the test harness."""

from collections.abc import Generator
from pathlib import Path
import pytest
from core.config import Settings
from harness.env import SandboxEnvironment
from harness.generators import DummyVideoGenerator


@pytest.fixture
def sandbox_env(tmp_path: Path) -> Generator[SandboxEnvironment, None, None]:
    """Provision a clean isolated sandbox environment with 4 simulated iPhones."""
    sandbox = SandboxEnvironment.create(
        base_dir=tmp_path,
        device_names=["iphone_01", "iphone_02", "iphone_03", "iphone_04"],
    )
    yield sandbox


@pytest.fixture
def dummy_generator() -> type[DummyVideoGenerator]:
    """Provide the synthetic and corrupt video generator factory."""
    return DummyVideoGenerator


@pytest.fixture
def test_settings(sandbox_env: SandboxEnvironment) -> Settings:
    """Settings mapped strictly to the isolated sandbox paths."""
    return Settings(
        base_dir=sandbox_env.root_path,
        inbox_dir=sandbox_env.inbox_dir,
        devices_dir=sandbox_env.devices_dir,
        dead_letter_dir=sandbox_env.dead_letter_dir,
        device_ids=[d.device_id for d in sandbox_env.devices],
        file_settle_timeout_seconds=0.1,
        poll_interval_seconds=0.1,
    )
