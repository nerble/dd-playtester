import os

import pytest

from dd4tester.credentials import (
    CredentialStoreError,
    load_character_password,
    load_login_credentials,
    login_environment,
    save_character_password,
    save_login_credentials,
)


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password


def test_login_credentials_round_trip_and_temporarily_supply_environment(monkeypatch) -> None:
    backend = FakeKeyring()
    save_login_credentials("test-login", "Rulemira", "not-in-a-file", backend=backend)

    credentials = load_login_credentials("test-login", backend=backend)
    assert credentials.username == "Rulemira"
    assert credentials.password == "not-in-a-file"

    monkeypatch.delenv("DD4_USERNAME", raising=False)
    monkeypatch.delenv("DD4_PASSWORD", raising=False)
    monkeypatch.setattr(
        "dd4tester.credentials.load_login_credentials",
        lambda _name: credentials,
    )
    with login_environment("test-login"):
        assert os.environ["DD4_USERNAME"] == "Rulemira"
        assert os.environ["DD4_PASSWORD"] == "not-in-a-file"
    assert "DD4_USERNAME" not in os.environ
    assert "DD4_PASSWORD" not in os.environ


def test_existing_environment_value_is_not_overwritten(monkeypatch) -> None:
    backend = FakeKeyring()
    save_login_credentials("test-login", "stored-user", "stored-password", backend=backend)
    monkeypatch.setenv("DD4_USERNAME", "environment-user")
    monkeypatch.delenv("DD4_PASSWORD", raising=False)
    monkeypatch.setattr(
        "dd4tester.credentials.load_login_credentials",
        lambda _name: load_login_credentials("test-login", backend=backend),
    )

    with login_environment("test-login"):
        assert os.environ["DD4_USERNAME"] == "environment-user"
        assert os.environ["DD4_PASSWORD"] == "stored-password"


def test_character_password_round_trip_and_missing_entry_error() -> None:
    backend = FakeKeyring()
    save_character_password("character:rulemira", "stored-password", backend=backend)

    assert (
        load_character_password("character:rulemira", backend=backend)
        == "stored-password"
    )
    with pytest.raises(CredentialStoreError, match="No character password"):
        load_character_password("character:missing", backend=backend)
