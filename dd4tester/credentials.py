from __future__ import annotations

import getpass
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Protocol


SERVICE_NAME = "dd4tester.dd4"
DEFAULT_LOGIN_CREDENTIAL = "dd4-login"


class CredentialBackend(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...


class CredentialStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoginCredentials:
    username: str
    password: str


def save_login_credentials(
    credential_name: str,
    username: str,
    password: str,
    *,
    backend: CredentialBackend | None = None,
) -> None:
    _validate(credential_name, "credential_name")
    _validate(username, "username")
    _validate(password, "password")
    store = backend or _keyring_backend()
    store.set_password(SERVICE_NAME, _entry(credential_name, "username"), username)
    store.set_password(SERVICE_NAME, _entry(credential_name, "password"), password)


def load_login_credentials(
    credential_name: str,
    *,
    backend: CredentialBackend | None = None,
) -> LoginCredentials:
    _validate(credential_name, "credential_name")
    store = backend or _keyring_backend()
    username = store.get_password(SERVICE_NAME, _entry(credential_name, "username"))
    password = store.get_password(SERVICE_NAME, _entry(credential_name, "password"))
    if not username or not password:
        raise CredentialStoreError(
            f"No complete login credential named {credential_name!r} is stored. "
            "Run configure-login once or set DD4_USERNAME and DD4_PASSWORD."
        )
    return LoginCredentials(username=username, password=password)


def save_character_password(
    credential_name: str,
    password: str,
    *,
    backend: CredentialBackend | None = None,
) -> None:
    _validate(credential_name, "credential_name")
    _validate(password, "password")
    (backend or _keyring_backend()).set_password(
        SERVICE_NAME,
        _entry(credential_name, "character-password"),
        password,
    )


def load_character_password(
    credential_name: str,
    *,
    backend: CredentialBackend | None = None,
) -> str:
    _validate(credential_name, "credential_name")
    password = (backend or _keyring_backend()).get_password(
        SERVICE_NAME,
        _entry(credential_name, "character-password"),
    )
    if not password:
        raise CredentialStoreError(
            f"No character password named {credential_name!r} is stored. "
            "Run configure-character-password once or set the profile password environment variable."
        )
    return password


def configure_login(credential_name: str = DEFAULT_LOGIN_CREDENTIAL) -> None:
    username = input("DD4 login name: ").strip()
    password = getpass.getpass("DD4 login password: ")
    save_login_credentials(credential_name, username, password)


def configure_character_password(credential_name: str) -> None:
    password = getpass.getpass("DD4 character password: ")
    save_character_password(credential_name, password)


@contextmanager
def login_environment(credential_name: str) -> Iterator[None]:
    changed: dict[str, str | None] = {}
    missing = [name for name in ("DD4_USERNAME", "DD4_PASSWORD") if name not in os.environ]
    if missing:
        credentials = load_login_credentials(credential_name)
        values = {
            "DD4_USERNAME": credentials.username,
            "DD4_PASSWORD": credentials.password,
        }
        for name in missing:
            changed[name] = os.environ.get(name)
            os.environ[name] = values[name]
    try:
        yield
    finally:
        for name, previous in changed.items():
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous


def _keyring_backend() -> CredentialBackend:
    try:
        import keyring
    except ModuleNotFoundError as exc:
        raise CredentialStoreError(
            "Credential storage needs the optional keyring dependency. "
            "Run python -m pip install -e ."
        ) from exc
    return keyring


def _entry(credential_name: str, field: str) -> str:
    return f"{credential_name}:{field}"


def _validate(value: str, label: str) -> None:
    if not value.strip():
        raise CredentialStoreError(f"{label} must not be empty")
