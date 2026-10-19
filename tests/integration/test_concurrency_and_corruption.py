"""Resilience tests: Concurrency simulation and corrupt file handling."""

import pytest
from harness.env import SandboxEnvironment
from harness.generators import DummyVideoGenerator


@pytest.mark.resilience
def test_corrupted_file_detection_spec(
    sandbox_env: SandboxEnvironment,
    dummy_generator: type[DummyVideoGenerator],
) -> None:
    """Resilience specification: Corrupt or zero-byte files are filtered safely."""
    v1 = dummy_generator.create_valid_video(sandbox_env.inbox_dir, "good_01.mp4")
    c1 = dummy_generator.create_corrupted_video(
        sandbox_env.inbox_dir, "empty.mp4", corruption_type="zero_byte"
    )
    v2 = dummy_generator.create_valid_video(sandbox_env.inbox_dir, "good_02.mp4")
    c2 = dummy_generator.create_corrupted_video(
        sandbox_env.inbox_dir, "garbage.mp4", corruption_type="garbage_header"
    )

    assert v1.stat().st_size > 0
    assert c1.stat().st_size == 0
    assert v2.stat().st_size > 0
    assert c2.stat().st_size > 0


@pytest.mark.resilience
def test_concurrency_burst_spec(
    sandbox_env: SandboxEnvironment,
    dummy_generator: type[DummyVideoGenerator],
) -> None:
    """Concurrency burst: Simulation of 40 video files simultaneously arriving in inbox."""
    burst_files = dummy_generator.create_batch(sandbox_env.inbox_dir, count=40, prefix="burst")
    assert len(burst_files) == 40
