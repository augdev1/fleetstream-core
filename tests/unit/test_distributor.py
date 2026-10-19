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
