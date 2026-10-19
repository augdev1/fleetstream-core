"""Integration tests: Ingestion pipeline and balanced distribution specification."""

import pytest
from core.distributor import DistributionEngine
from harness.assertions import (
    assert_no_leftover_in_inbox,
    assert_paired_json_valid,
    assert_round_robin_balanced,
)
from harness.env import SandboxEnvironment
from harness.generators import DummyVideoGenerator


@pytest.mark.integration
def test_harness_sandbox_initialization(sandbox_env: SandboxEnvironment) -> None:
    """Verify that the test sandbox initializes isolated folder structure properly."""
    assert sandbox_env.inbox_dir.exists()
    assert sandbox_env.devices_dir.exists()
    assert sandbox_env.dead_letter_dir.exists()
    assert len(sandbox_env.devices) == 4

    for dev in sandbox_env.devices:
        assert dev.path.exists()
        assert dev.path.is_dir()


@pytest.mark.integration
def test_dummy_generator_produces_valid_and_corrupt_files(
    sandbox_env: SandboxEnvironment,
    dummy_generator: type[DummyVideoGenerator],
) -> None:
    """Validate artifact generation factory methods."""
    batch = dummy_generator.create_batch(sandbox_env.inbox_dir, count=8)
    assert len(batch) == 8
    for f in batch:
        assert f.exists()
        assert f.stat().st_size > 0

    corrupt = dummy_generator.create_corrupted_video(
        sandbox_env.inbox_dir,
        filename="broken.mp4",
        corruption_type="zero_byte",
    )
    assert corrupt.exists()
    assert corrupt.stat().st_size == 0


@pytest.mark.integration
def test_pipeline_spec_balanced_round_robin(
    sandbox_env: SandboxEnvironment,
    dummy_generator: type[DummyVideoGenerator],
) -> None:
    """Pipeline specification: 12 ingested videos distributed evenly across 4 iPhones."""
    files = dummy_generator.create_batch(sandbox_env.inbox_dir, count=12)
    assert len(files) == 12

    engine = DistributionEngine(
        inbox_dir=sandbox_env.inbox_dir,
        devices_dir=sandbox_env.devices_dir,
    )
    summary = engine.process_inbox()

    assert summary.distributed == 12
    assert_round_robin_balanced(sandbox_env.devices_dir, expected_total=12, tolerance=0)
    assert_no_leftover_in_inbox(sandbox_env.inbox_dir)
