from pathlib import Path

import pytest

from dd4tester.lease import (
    CampaignLease,
    CampaignLeaseBusyError,
    campaign_lease_path,
)


def test_campaign_lease_rejects_a_second_holder_and_releases(tmp_path: Path) -> None:
    path = tmp_path / "campaign.lock"
    first = CampaignLease(path)
    second = CampaignLease(path)

    first.acquire()
    try:
        with pytest.raises(CampaignLeaseBusyError):
            second.acquire()
    finally:
        first.release()

    with second:
        assert path.exists()


def test_campaign_lease_path_is_stable_per_config(tmp_path: Path) -> None:
    database = tmp_path / "runs.sqlite3"
    config = tmp_path / "campaigns" / "mage.yaml"

    first = campaign_lease_path(database, config)
    second = campaign_lease_path(database, config)
    other = campaign_lease_path(database, tmp_path / "campaigns" / "warrior.yaml")

    assert first == second
    assert first != other
    assert first.parent == database.parent / ".campaign-leases"
