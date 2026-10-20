"""Unit tests for the RoundRobinDistributor contract."""

from pathlib import Path
import pytest
from core.distributor import RoundRobinDistributor
from core.models import Device


@pytest.mark.unit
def test_distributor_initialization_and_active_devices() -> None:
    """Verify that distributor filters active devices correctly."""
    devices = [
        Device(device_id="iphone_01", path=Path("/devices/iphone_01"), is_active=True),
        Device(device_id="iphone_02", path=Path("/devices/iphone_02"), is_active=False),
        Device(device_id="iphone_03", path=Path("/devices/iphone_03"), is_active=True),
        Device(device_id="iphone_04", path=Path("/devices/iphone_04"), is_active=True),
    ]

    distributor = RoundRobinDistributor(devices)
    active = distributor.active_devices

    assert len(active) == 3
    assert [d.device_id for d in active] == ["iphone_01", "iphone_03", "iphone_04"]


@pytest.mark.unit
def test_distributor_round_robin_cycling() -> None:
    """Validate strict circular rotation across active devices."""
    devices = [
        Device(device_id="iphone_01", path=Path("/devices/iphone_01"), is_active=True),
        Device(device_id="iphone_02", path=Path("/devices/iphone_02"), is_active=False),
        Device(device_id="iphone_03", path=Path("/devices/iphone_03"), is_active=True),
    ]
    distributor = RoundRobinDistributor(devices)

    # First cycle
    assert distributor.select_next_device().device_id == "iphone_01"
    assert distributor.select_next_device().device_id == "iphone_03"
    # Second cycle loops back to beginning
    assert distributor.select_next_device().device_id == "iphone_01"
    assert distributor.select_next_device().device_id == "iphone_03"


@pytest.mark.unit
def test_distributor_no_active_devices_raises() -> None:
    """Raise DeviceTargetUnavailableError when all devices are inactive."""
    from core.exceptions import DeviceTargetUnavailableError

    devices = [Device(device_id="iphone_01", path=Path("/devices/iphone_01"), is_active=False)]
    distributor = RoundRobinDistributor(devices)

    with pytest.raises(DeviceTargetUnavailableError):
        distributor.select_next_device()


@pytest.mark.unit
def test_broadcast_distributor_dispatches_to_all_devices(tmp_path: Path) -> None:
    """Verify BroadcastDistributor copies video to all active devices and removes source."""
    from core.distributor import BroadcastDistributor

    inbox = tmp_path / "inbox"
    inbox.mkdir()
    video = inbox / "sample.mp4"
    video.write_bytes(b"\x00" * 128)

    dev1 = tmp_path / "devices" / "iphone_01"
    dev2 = tmp_path / "devices" / "iphone_02"
    dev1.mkdir(parents=True)
    dev2.mkdir(parents=True)

    devices = [
        Device(device_id="iphone_01", path=dev1, is_active=True),
        Device(device_id="iphone_02", path=dev2, is_active=True),
    ]

    distributor = BroadcastDistributor(devices)
    jobs = distributor.dispatch(video)

    assert len(jobs) == 2
    assert (dev1 / "sample.mp4").exists()
    assert (dev1 / "sample.json").exists()
    assert (dev2 / "sample.mp4").exists()
    assert (dev2 / "sample.json").exists()
    assert not video.exists()  # Removed from inbox after broadcast
