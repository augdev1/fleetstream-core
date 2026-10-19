"""Integration tests: Validation of paired metadata sidecar files (.json)."""

from pathlib import Path
import pytest
from harness.assertions import assert_paired_json_valid
from harness.env import SandboxEnvironment
from harness.generators import DummyVideoGenerator
from core.models import DistributionStatus, VideoMetadata


@pytest.mark.integration
def test_paired_json_assertion_helper(
    sandbox_env: SandboxEnvironment,
    dummy_generator: type[DummyVideoGenerator],
) -> None:
    """Verify that the harness paired metadata assertion helper validates correctly."""
    dev = sandbox_env.get_device("iphone_01")
    video_path = dummy_generator.create_valid_video(dev.path, filename="video_001.mp4")

    # Simulate presence of paired .json file
    metadata = VideoMetadata(
        original_filename="video_001.mp4",
        distributed_filename="video_001.mp4",
        target_device="iphone_01",
        suggested_caption="New exclusive drop. Link in bio.",
        hashtags=["#viral", "#tech", "#tame"],
        file_size_bytes=video_path.stat().st_size,
        status=DistributionStatus.DISTRIBUTED,
    )

    json_path = dev.path / "video_001.json"
    json_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    # Execute harness assertion
    validated = assert_paired_json_valid(video_path, expected_device="iphone_01")
    assert validated.distributed_filename == "video_001.mp4"
    assert validated.target_device == "iphone_01"
    assert "#viral" in validated.hashtags
